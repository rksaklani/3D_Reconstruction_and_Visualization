"""Bundle adjustment using Ceres Solver (via COLMAP) or scipy."""

import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from typing import Dict, Tuple, Optional
import subprocess
from pathlib import Path
import logging

from backend.services.colmap_service import SfMResult, Camera, Image, Point3D

logger = logging.getLogger(__name__)


class BundleAdjustmentError(Exception):
    """Bundle adjustment error."""
    pass


class BundleAdjuster:
    """Bundle adjustment optimizer."""
    
    def __init__(
        self,
        max_iterations: int = 100,
        function_tolerance: float = 1e-6,
        gradient_tolerance: float = 1e-10,
        parameter_tolerance: float = 1e-8,
        use_colmap: bool = True
    ):
        """
        Initialize bundle adjuster.
        
        Args:
            max_iterations: Maximum optimization iterations
            function_tolerance: Function value change tolerance
            gradient_tolerance: Gradient norm tolerance
            parameter_tolerance: Parameter change tolerance
            use_colmap: Use COLMAP's bundle adjustment if True, else scipy
        """
        self.max_iterations = max_iterations
        self.function_tolerance = function_tolerance
        self.gradient_tolerance = gradient_tolerance
        self.parameter_tolerance = parameter_tolerance
        self.use_colmap = use_colmap
    
    def optimize(
        self,
        sfm_result: SfMResult,
        model_path: str,
        colmap_bin: Optional[str] = None
    ) -> Tuple[SfMResult, Dict]:
        """
        Run bundle adjustment optimization.
        
        Args:
            sfm_result: Initial SfM result
            model_path: Path to COLMAP model directory
            colmap_bin: Path to COLMAP binary
            
        Returns:
            (optimized_result, statistics) tuple
            
        Raises:
            BundleAdjustmentError: If optimization fails
        """
        if self.use_colmap:
            return self._optimize_with_colmap(sfm_result, model_path, colmap_bin)
        else:
            return self._optimize_with_scipy(sfm_result)
    
    def _optimize_with_colmap(
        self,
        sfm_result: SfMResult,
        model_path: str,
        colmap_bin: Optional[str] = None
    ) -> Tuple[SfMResult, Dict]:
        """
        Run bundle adjustment using COLMAP (Ceres-based).
        
        Args:
            sfm_result: Initial SfM result
            model_path: Path to COLMAP model directory
            colmap_bin: Path to COLMAP binary
            
        Returns:
            (optimized_result, statistics) tuple
        """
        try:
            model_path = Path(model_path)
            input_path = model_path / "0"  # Input model
            output_path = model_path / "0_ba"  # Output model
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Find COLMAP binary
            if colmap_bin is None:
                colmap_bin = self._find_colmap()
            
            # Calculate initial error
            initial_error = sfm_result.mean_reprojection_error
            
            # Run bundle adjustment
            cmd = [
                colmap_bin,
                "bundle_adjuster",
                "--input_path", str(input_path),
                "--output_path", str(output_path),
                "--BundleAdjustment.max_num_iterations", str(self.max_iterations),
                "--BundleAdjustment.function_tolerance", str(self.function_tolerance),
                "--BundleAdjustment.gradient_tolerance", str(self.gradient_tolerance),
                "--BundleAdjustment.parameter_tolerance", str(self.parameter_tolerance),
            ]
            
            logger.info("Running COLMAP bundle adjustment...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse optimized result
            from backend.services.colmap_service import COLMAPService
            colmap_service = COLMAPService(colmap_bin)
            optimized_result = colmap_service.parse_sfm_result(str(output_path))
            
            # Calculate final error
            final_error = optimized_result.mean_reprojection_error
            
            # Validate monotonicity
            if final_error > initial_error:
                logger.warning(
                    f"Bundle adjustment increased error: {initial_error:.4f} -> {final_error:.4f}"
                )
            
            statistics = {
                'success': True,
                'initial_error': float(initial_error),
                'final_error': float(final_error),
                'error_reduction': float(initial_error - final_error),
                'error_reduction_percent': float((initial_error - final_error) / initial_error * 100) if initial_error > 0 else 0.0,
                'iterations': self.max_iterations,  # COLMAP doesn't report actual iterations
                'method': 'colmap_ceres'
            }
            
            logger.info(f"Bundle adjustment complete: {initial_error:.4f} -> {final_error:.4f}")
            
            return optimized_result, statistics
            
        except subprocess.CalledProcessError as e:
            raise BundleAdjustmentError(f"COLMAP bundle adjustment failed: {e.stderr}")
        except Exception as e:
            raise BundleAdjustmentError(f"Bundle adjustment failed: {e}")
    
    def _optimize_with_scipy(
        self,
        sfm_result: SfMResult
    ) -> Tuple[SfMResult, Dict]:
        """
        Run bundle adjustment using scipy (pure Python).
        
        Args:
            sfm_result: Initial SfM result
            
        Returns:
            (optimized_result, statistics) tuple
        """
        try:
            # Extract parameters
            camera_params, point_params, observations = self._extract_parameters(sfm_result)
            
            # Calculate initial error
            initial_residuals = self._compute_residuals(
                camera_params,
                point_params,
                observations,
                sfm_result.cameras
            )
            initial_error = np.mean(np.abs(initial_residuals))
            
            # Optimize
            logger.info("Running scipy bundle adjustment...")
            result = least_squares(
                self._residual_function,
                np.concatenate([camera_params.ravel(), point_params.ravel()]),
                args=(observations, sfm_result.cameras, camera_params.shape[0]),
                max_nfev=self.max_iterations,
                ftol=self.function_tolerance,
                gtol=self.gradient_tolerance,
                xtol=self.parameter_tolerance,
                verbose=2
            )
            
            # Extract optimized parameters
            n_cameras = camera_params.shape[0]
            camera_param_size = camera_params.shape[1]
            
            optimized_camera_params = result.x[:n_cameras * camera_param_size].reshape(camera_params.shape)
            optimized_point_params = result.x[n_cameras * camera_param_size:].reshape(point_params.shape)
            
            # Calculate final error
            final_residuals = self._compute_residuals(
                optimized_camera_params,
                optimized_point_params,
                observations,
                sfm_result.cameras
            )
            final_error = np.mean(np.abs(final_residuals))
            
            # Update SfM result
            optimized_result = self._update_sfm_result(
                sfm_result,
                optimized_camera_params,
                optimized_point_params
            )
            
            statistics = {
                'success': result.success,
                'initial_error': float(initial_error),
                'final_error': float(final_error),
                'error_reduction': float(initial_error - final_error),
                'error_reduction_percent': float((initial_error - final_error) / initial_error * 100) if initial_error > 0 else 0.0,
                'iterations': result.nfev,
                'method': 'scipy_least_squares',
                'message': result.message
            }
            
            logger.info(f"Bundle adjustment complete: {initial_error:.4f} -> {final_error:.4f}")
            
            return optimized_result, statistics
            
        except Exception as e:
            raise BundleAdjustmentError(f"Scipy bundle adjustment failed: {e}")
    
    def _extract_parameters(
        self,
        sfm_result: SfMResult
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract optimization parameters from SfM result.
        
        Returns:
            (camera_params, point_params, observations) tuple
        """
        # Camera parameters: [qw, qx, qy, qz, tx, ty, tz] for each camera
        n_cameras = len(sfm_result.images)
        camera_params = np.zeros((n_cameras, 7))
        
        image_id_to_idx = {}
        for idx, (img_id, image) in enumerate(sfm_result.images.items()):
            camera_params[idx, :4] = image.qvec
            camera_params[idx, 4:] = image.tvec
            image_id_to_idx[img_id] = idx
        
        # Point parameters: [x, y, z] for each point
        n_points = len(sfm_result.points3D)
        point_params = np.zeros((n_points, 3))
        
        point_id_to_idx = {}
        for idx, (pt_id, point) in enumerate(sfm_result.points3D.items()):
            point_params[idx] = point.xyz
            point_id_to_idx[pt_id] = idx
        
        # Observations: [camera_idx, point_idx, x, y]
        observations = []
        for pt_id, point in sfm_result.points3D.items():
            point_idx = point_id_to_idx[pt_id]
            
            for img_id, pt2d_idx in zip(point.image_ids, point.point2D_idxs):
                if img_id in image_id_to_idx:
                    camera_idx = image_id_to_idx[img_id]
                    image = sfm_result.images[img_id]
                    
                    if pt2d_idx < len(image.xys):
                        x, y = image.xys[pt2d_idx]
                        observations.append([camera_idx, point_idx, x, y])
        
        observations = np.array(observations)
        
        return camera_params, point_params, observations
    
    def _compute_residuals(
        self,
        camera_params: np.ndarray,
        point_params: np.ndarray,
        observations: np.ndarray,
        cameras: Dict[int, Camera]
    ) -> np.ndarray:
        """Compute reprojection residuals."""
        residuals = []
        
        for obs in observations:
            camera_idx, point_idx, x_obs, y_obs = obs
            
            # Get camera parameters
            qvec = camera_params[camera_idx, :4]
            tvec = camera_params[camera_idx, 4:]
            
            # Get 3D point
            point_3d = point_params[point_idx]
            
            # Project point
            x_proj, y_proj = self._project_point(point_3d, qvec, tvec)
            
            # Compute residual
            residuals.append(x_proj - x_obs)
            residuals.append(y_proj - y_obs)
        
        return np.array(residuals)
    
    def _residual_function(
        self,
        params: np.ndarray,
        observations: np.ndarray,
        cameras: Dict[int, Camera],
        n_cameras: int
    ) -> np.ndarray:
        """Residual function for optimization."""
        # Split parameters
        camera_param_size = 7
        camera_params = params[:n_cameras * camera_param_size].reshape((n_cameras, camera_param_size))
        point_params = params[n_cameras * camera_param_size:].reshape((-1, 3))
        
        return self._compute_residuals(camera_params, point_params, observations, cameras)
    
    def _project_point(
        self,
        point_3d: np.ndarray,
        qvec: np.ndarray,
        tvec: np.ndarray,
        focal_length: float = 1000.0
    ) -> Tuple[float, float]:
        """Project 3D point to 2D using camera parameters."""
        # Rotation matrix from quaternion
        R = self._quat_to_rotation(qvec)
        
        # Transform to camera coordinates
        point_cam = R @ (point_3d - tvec)
        
        # Project to image plane (simple pinhole model)
        if point_cam[2] > 0:
            x = focal_length * point_cam[0] / point_cam[2]
            y = focal_length * point_cam[1] / point_cam[2]
        else:
            x, y = 0.0, 0.0
        
        return x, y
    
    def _quat_to_rotation(self, qvec: np.ndarray) -> np.ndarray:
        """Convert quaternion to rotation matrix."""
        w, x, y, z = qvec
        
        R = np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
            [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
            [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
        ])
        
        return R
    
    def _update_sfm_result(
        self,
        sfm_result: SfMResult,
        camera_params: np.ndarray,
        point_params: np.ndarray
    ) -> SfMResult:
        """Update SfM result with optimized parameters."""
        # Update camera poses
        for idx, (img_id, image) in enumerate(sfm_result.images.items()):
            image.qvec = camera_params[idx, :4]
            image.tvec = camera_params[idx, 4:]
        
        # Update 3D points
        for idx, (pt_id, point) in enumerate(sfm_result.points3D.items()):
            point.xyz = point_params[idx]
        
        # Recalculate mean error
        errors = [p.error for p in sfm_result.points3D.values()]
        sfm_result.mean_reprojection_error = np.mean(errors) if errors else 0.0
        
        return sfm_result
    
    def _find_colmap(self) -> str:
        """Find COLMAP binary."""
        locations = [
            "colmap",
            "/usr/local/bin/colmap",
            "/usr/bin/colmap",
            str(Path.cwd() / "reconstruction" / "colmap" / "build" / "src" / "colmap" / "exe" / "colmap"),
        ]
        
        for loc in locations:
            try:
                result = subprocess.run(
                    [loc, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return loc
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise BundleAdjustmentError("COLMAP binary not found")


def run_bundle_adjustment(
    sfm_result: SfMResult,
    model_path: str,
    max_iterations: int = 100,
    use_colmap: bool = True
) -> Tuple[SfMResult, Dict]:
    """
    Convenience function to run bundle adjustment.
    
    Args:
        sfm_result: Initial SfM result
        model_path: Path to COLMAP model directory
        max_iterations: Maximum iterations
        use_colmap: Use COLMAP if True, else scipy
        
    Returns:
        (optimized_result, statistics) tuple
    """
    adjuster = BundleAdjuster(
        max_iterations=max_iterations,
        use_colmap=use_colmap
    )
    
    return adjuster.optimize(sfm_result, model_path)
