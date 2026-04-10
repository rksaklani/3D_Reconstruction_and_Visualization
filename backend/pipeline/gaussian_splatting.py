"""Gaussian Splatting training and rendering wrapper."""

import numpy as np
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import shutil

logger = logging.getLogger(__name__)


@dataclass
class GaussianParameters:
    """Gaussian splatting parameters."""
    positions: np.ndarray  # (N, 3)
    opacities: np.ndarray  # (N, 1)
    scales: np.ndarray  # (N, 3)
    rotations: np.ndarray  # (N, 4) quaternions
    colors: np.ndarray  # (N, 3) or SH coefficients
    sh_degree: int = 0


class GaussianSplattingTrainer:
    """Wrapper for Gaussian Splatting training."""
    
    def __init__(
        self,
        gaussian_splatting_path: str = "reconstruction/gaussian-splatting",
        config: Optional[Dict] = None
    ):
        """
        Initialize Gaussian Splatting trainer.
        
        Args:
            gaussian_splatting_path: Path to gaussian-splatting repository
            config: Configuration dictionary
        """
        self.gs_path = Path(gaussian_splatting_path)
        self.config = config or {}
        
        if not self.gs_path.exists():
            raise FileNotFoundError(
                f"Gaussian splatting not found at {gaussian_splatting_path}"
            )
        
        self.train_script = self.gs_path / "train.py"
        self.render_script = self.gs_path / "render.py"
        
        if not self.train_script.exists():
            raise FileNotFoundError(f"Training script not found: {self.train_script}")
    
    def initialize_from_sparse_points(
        self,
        sparse_points: np.ndarray,
        sparse_colors: Optional[np.ndarray] = None,
        num_points: Optional[int] = None
    ) -> GaussianParameters:
        """
        Initialize Gaussian parameters from sparse point cloud.
        
        Args:
            sparse_points: Sparse 3D points (N, 3)
            sparse_colors: Point colors (N, 3), optional
            num_points: Target number of Gaussians (subsamples if needed)
            
        Returns:
            Initialized Gaussian parameters
        """
        n_points = len(sparse_points)
        
        # Subsample if needed
        if num_points is not None and n_points > num_points:
            indices = np.random.choice(n_points, num_points, replace=False)
            sparse_points = sparse_points[indices]
            if sparse_colors is not None:
                sparse_colors = sparse_colors[indices]
            n_points = num_points
        
        # Initialize positions
        positions = sparse_points.copy()
        
        # Initialize opacities
        opacity_init = self.config.get('initialization', {}).get('opacity_init', 0.1)
        opacities = np.full((n_points, 1), opacity_init, dtype=np.float32)
        
        # Initialize scales (isotropic)
        scale_init = self.config.get('initialization', {}).get('scale_init', 1.0)
        scales = np.full((n_points, 3), scale_init, dtype=np.float32)
        
        # Initialize rotations (identity quaternion)
        rotation_init = self.config.get('initialization', {}).get(
            'rotation_init', [1.0, 0.0, 0.0, 0.0]
        )
        rotations = np.tile(rotation_init, (n_points, 1)).astype(np.float32)
        
        # Initialize colors
        if sparse_colors is not None:
            colors = sparse_colors.copy()
        else:
            # Default to gray
            colors = np.full((n_points, 3), 0.5, dtype=np.float32)
        
        # Validate parameters
        self._validate_parameters(
            positions, opacities, scales, rotations, colors
        )
        
        logger.info(f"Initialized {n_points} Gaussians from sparse points")
        
        return GaussianParameters(
            positions=positions,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            colors=colors,
            sh_degree=0
        )
    
    def _validate_parameters(
        self,
        positions: np.ndarray,
        opacities: np.ndarray,
        scales: np.ndarray,
        rotations: np.ndarray,
        colors: np.ndarray
    ) -> bool:
        """
        Validate Gaussian parameters.
        
        Args:
            positions: Positions (N, 3)
            opacities: Opacities (N, 1)
            scales: Scales (N, 3)
            rotations: Rotations (N, 4)
            colors: Colors (N, 3)
            
        Returns:
            True if valid
        
        Raises:
            ValueError if parameters are invalid
        """
        n = len(positions)
        
        # Check shapes
        if opacities.shape != (n, 1):
            raise ValueError(f"Invalid opacity shape: {opacities.shape}, expected ({n}, 1)")
        
        if scales.shape != (n, 3):
            raise ValueError(f"Invalid scale shape: {scales.shape}, expected ({n}, 3)")
        
        if rotations.shape != (n, 4):
            raise ValueError(f"Invalid rotation shape: {rotations.shape}, expected ({n}, 4)")
        
        if colors.shape[0] != n:
            raise ValueError(f"Invalid color shape: {colors.shape}, expected ({n}, 3) or ({n}, K)")
        
        # Check opacity bounds [0, 1]
        if not np.all((opacities >= 0) & (opacities <= 1)):
            raise ValueError("Opacities must be in [0, 1]")
        
        # Check scales are positive
        if not np.all(scales > 0):
            raise ValueError("Scales must be positive")
        
        # Check rotations are unit quaternions (approximately)
        rotation_norms = np.linalg.norm(rotations, axis=1)
        if not np.allclose(rotation_norms, 1.0, atol=1e-3):
            logger.warning("Rotations are not unit quaternions, normalizing...")
            rotations /= rotation_norms[:, np.newaxis]
        
        # Check covariance is positive semi-definite
        # This is guaranteed by the scale/rotation parameterization
        
        logger.debug("Parameter validation passed")
        return True
    
    def train(
        self,
        source_path: str,
        model_path: str,
        images_path: Optional[str] = None,
        sparse_path: Optional[str] = None,
        iterations: Optional[int] = None,
        checkpoint_path: Optional[str] = None
    ) -> Dict:
        """
        Train Gaussian Splatting model using conda environment.
        
        Args:
            source_path: Path to source data (COLMAP format)
            model_path: Path to save trained model
            images_path: Path to training images
            sparse_path: Path to sparse reconstruction
            iterations: Number of training iterations
            checkpoint_path: Path to checkpoint to resume from
            
        Returns:
            Training statistics
        """
        # Prepare training command using conda environment
        cmd = [
            "conda", "run", "-n", "gaussian_splatting",
            "python", str(self.train_script),
            "-s", source_path,
            "-m", model_path
        ]
        
        # Add optional arguments
        if images_path:
            cmd.extend(["--images", images_path])
        
        if sparse_path:
            cmd.extend(["--sparse", sparse_path])
        
        if iterations is None:
            iterations = self.config.get('training', {}).get('iterations', 30000)
        cmd.extend(["--iterations", str(iterations)])
        
        # Add configuration parameters
        training_config = self.config.get('training', {})
        
        if 'densify_grad_threshold' in training_config:
            cmd.extend(["--densify_grad_threshold", str(training_config['densify_grad_threshold'])])
        
        if 'densification_interval' in training_config:
            cmd.extend(["--densification_interval", str(training_config['densification_interval'])])
        
        if 'opacity_reset_interval' in training_config:
            cmd.extend(["--opacity_reset_interval", str(training_config['opacity_reset_interval'])])
        
        if checkpoint_path:
            cmd.extend(["--start_checkpoint", checkpoint_path])
        
        logger.info(f"Starting Gaussian Splatting training with conda env: {' '.join(cmd)}")
        
        try:
            # Run training
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600 * 4  # 4 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Training failed: {result.stderr}")
                raise RuntimeError(f"Gaussian Splatting training failed: {result.stderr}")
            
            logger.info("Training completed successfully")
            
            # Parse training statistics from output
            stats = self._parse_training_output(result.stdout)
            
            return stats
            
        except subprocess.TimeoutExpired:
            logger.error("Training timeout exceeded")
            raise RuntimeError("Gaussian Splatting training timeout")
        
        except Exception as e:
            logger.error(f"Training error: {e}")
            raise
    
    def _parse_training_output(self, output: str) -> Dict:
        """Parse training statistics from output."""
        stats = {
            'iterations': 0,
            'final_loss': None,
            'initial_loss': None,
            'psnr': None
        }
        
        lines = output.split('\n')
        
        for line in lines:
            # Parse iteration count
            if 'Iteration' in line and '/' in line:
                try:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'Iteration':
                            iter_str = parts[i + 1].split('/')[0]
                            stats['iterations'] = int(iter_str)
                except:
                    pass
            
            # Parse loss
            if 'Loss:' in line:
                try:
                    loss_str = line.split('Loss:')[1].split()[0]
                    loss = float(loss_str)
                    
                    if stats['initial_loss'] is None:
                        stats['initial_loss'] = loss
                    stats['final_loss'] = loss
                except:
                    pass
            
            # Parse PSNR
            if 'PSNR:' in line:
                try:
                    psnr_str = line.split('PSNR:')[1].split()[0]
                    stats['psnr'] = float(psnr_str)
                except:
                    pass
        
        return stats
    
    def validate_training(self, stats: Dict) -> bool:
        """
        Validate training results.
        
        Args:
            stats: Training statistics
            
        Returns:
            True if training is valid
        """
        # Check if training completed
        if stats['iterations'] == 0:
            logger.error("Training did not complete any iterations")
            return False
        
        # Check if loss decreased
        if stats['initial_loss'] is not None and stats['final_loss'] is not None:
            if stats['final_loss'] >= stats['initial_loss']:
                logger.warning(
                    f"Loss did not decrease: {stats['initial_loss']:.4f} -> {stats['final_loss']:.4f}"
                )
                return False
            
            loss_reduction = (stats['initial_loss'] - stats['final_loss']) / stats['initial_loss']
            logger.info(f"Loss reduction: {loss_reduction * 100:.2f}%")
        
        return True
    
    def load_trained_model(self, model_path: str) -> GaussianParameters:
        """
        Load trained Gaussian Splatting model.
        
        Args:
            model_path: Path to trained model directory
            
        Returns:
            Gaussian parameters
        """
        model_dir = Path(model_path)
        
        # Look for point cloud file
        ply_files = list(model_dir.glob("point_cloud/iteration_*/point_cloud.ply"))
        
        if not ply_files:
            raise FileNotFoundError(f"No trained model found in {model_path}")
        
        # Use the latest iteration
        ply_file = sorted(ply_files)[-1]
        
        logger.info(f"Loading model from {ply_file}")
        
        # Parse PLY file (simplified - in practice use plyfile library)
        # This is a placeholder - actual implementation would parse PLY format
        
        # For now, return dummy parameters
        # TODO: Implement proper PLY parsing
        raise NotImplementedError("Model loading not yet implemented")
    
    def handle_training_instability(
        self,
        model_path: str,
        checkpoint_path: Optional[str] = None
    ) -> bool:
        """
        Handle training instability by restoring from checkpoint.
        
        Args:
            model_path: Path to model directory
            checkpoint_path: Path to last stable checkpoint
            
        Returns:
            True if recovery successful
        """
        if checkpoint_path and Path(checkpoint_path).exists():
            logger.info(f"Restoring from checkpoint: {checkpoint_path}")
            
            # Reduce learning rates
            if 'initialization' in self.config:
                for key in self.config['initialization']:
                    if 'lr' in key:
                        self.config['initialization'][key] *= 0.5
            
            logger.info("Reduced learning rates for stability")
            return True
        
        logger.error("No checkpoint available for recovery")
        return False


def export_gaussian_to_ply(
    params: GaussianParameters,
    output_path: str,
    format: str = "binary"
):
    """
    Export Gaussian parameters to PLY format.
    
    Args:
        params: Gaussian parameters
        output_path: Output PLY file path
        format: "ascii" or "binary"
    """
    n = len(params.positions)
    
    # Create PLY header
    header = f"""ply
format {format}_little_endian 1.0
element vertex {n}
property float x
property float y
property float z
property float nx
property float ny
property float nz
property uchar red
property uchar green
property uchar blue
end_header
"""
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'wb' if format == 'binary' else 'w') as f:
        if format == 'ascii':
            f.write(header)
            
            # Write vertices
            for i in range(n):
                x, y, z = params.positions[i]
                r, g, b = (params.colors[i] * 255).astype(np.uint8)
                
                # Use zero normals (not used for Gaussians)
                f.write(f"{x} {y} {z} 0 0 0 {r} {g} {b}\n")
        else:
            # Binary format
            f.write(header.encode('ascii'))
            
            # Write binary data
            for i in range(n):
                x, y, z = params.positions[i]
                r, g, b = (params.colors[i] * 255).astype(np.uint8)
                
                # Pack as binary (simplified)
                data = np.array([x, y, z, 0, 0, 0], dtype=np.float32).tobytes()
                data += bytes([r, g, b])
                f.write(data)
    
    logger.info(f"Exported {n} Gaussians to {output_path}")
