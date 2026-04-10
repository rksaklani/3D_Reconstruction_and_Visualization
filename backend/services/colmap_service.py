"""COLMAP Structure-from-Motion service wrapper."""

import os
import subprocess
import struct
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Camera:
    """Camera parameters."""
    id: int
    model: str
    width: int
    height: int
    params: np.ndarray  # Intrinsic parameters


@dataclass
class Image:
    """Image with camera pose."""
    id: int
    qvec: np.ndarray  # Quaternion (w, x, y, z)
    tvec: np.ndarray  # Translation vector
    camera_id: int
    name: str
    xys: np.ndarray  # 2D keypoint coordinates
    point3D_ids: np.ndarray  # Corresponding 3D point IDs


@dataclass
class Point3D:
    """3D point."""
    id: int
    xyz: np.ndarray  # 3D coordinates
    rgb: np.ndarray  # Color (uint8)
    error: float  # Reprojection error
    image_ids: np.ndarray  # Images observing this point
    point2D_idxs: np.ndarray  # 2D point indices in those images


@dataclass
class SfMResult:
    """Structure-from-Motion result."""
    cameras: Dict[int, Camera]
    images: Dict[int, Image]
    points3D: Dict[int, Point3D]
    num_cameras: int
    num_images: int
    num_points: int
    mean_reprojection_error: float


class COLMAPError(Exception):
    """COLMAP execution error."""
    pass


class COLMAPService:
    """Service for running COLMAP Structure-from-Motion."""
    
    def __init__(
        self,
        colmap_bin: Optional[str] = None,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize COLMAP service.
        
        Args:
            colmap_bin: Path to COLMAP binary (auto-detected if None)
            workspace_dir: Working directory for COLMAP operations
        """
        self.colmap_bin = colmap_bin or self._find_colmap()
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd() / "colmap_workspace"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"COLMAP binary: {self.colmap_bin}")
        logger.info(f"Workspace: {self.workspace_dir}")
    
    def _find_colmap(self) -> str:
        """Find COLMAP binary."""
        # Try common locations
        locations = [
            "/home/rk/aditya/reconstruction/colmap/build/src/colmap/exe/colmap",  # Local GPU build (absolute path)
            str(Path.cwd() / "reconstruction" / "colmap" / "build" / "src" / "colmap" / "exe" / "colmap"),  # Relative path
            "colmap",  # In PATH
            "/usr/local/bin/colmap",
            "/usr/bin/colmap",
        ]
        
        for loc in locations:
            try:
                result = subprocess.run(
                    [loc, "help"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and "COLMAP" in result.stdout:
                    return loc
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise COLMAPError("COLMAP binary not found. Please install COLMAP or specify path.")
    
    def run_sfm(
        self,
        image_dir: str,
        output_dir: Optional[str] = None,
        camera_model: str = "SIMPLE_RADIAL",
        single_camera: bool = False,
        gpu_index: int = 0,
        matcher: str = "sequential"  # Added matcher parameter
    ) -> SfMResult:
        """
        Run complete SfM pipeline.
        
        Args:
            image_dir: Directory containing input images
            output_dir: Output directory for results
            camera_model: Camera model type
            single_camera: Use single camera for all images
            gpu_index: GPU device index
            
        Returns:
            SfM result
            
        Raises:
            COLMAPError: If SfM fails
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            raise COLMAPError(f"Image directory not found: {image_dir}")
        
        output_dir = Path(output_dir) if output_dir else self.workspace_dir / "sparse"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        database_path = output_dir / "database.db"
        
        try:
            # Step 1: Feature extraction
            logger.info("Extracting features...")
            self._extract_features(
                image_dir,
                database_path,
                camera_model,
                single_camera,
                gpu_index
            )
            
            # Step 2: Feature matching
            logger.info(f"Matching features ({matcher} matcher)...")
            self._match_features(database_path, gpu_index, matcher)
            
            # Step 3: Incremental mapping
            logger.info("Running incremental mapping...")
            self._incremental_mapping(
                database_path,
                image_dir,
                output_dir
            )
            
            # Step 4: Parse results
            logger.info("Parsing results...")
            result = self.parse_sfm_result(output_dir / "0")
            
            logger.info(f"SfM complete: {result.num_cameras} cameras, "
                       f"{result.num_images} images, {result.num_points} points")
            
            return result
            
        except subprocess.CalledProcessError as e:
            raise COLMAPError(f"COLMAP failed: {e.stderr}")
        except Exception as e:
            raise COLMAPError(f"SfM pipeline failed: {e}")
    
    def _extract_features(
        self,
        image_dir: Path,
        database_path: Path,
        camera_model: str,
        single_camera: bool,
        gpu_index: int
    ) -> None:
        """Extract SIFT features from images."""
        cmd = [
            self.colmap_bin,
            "feature_extractor",
            "--database_path", str(database_path),
            "--image_path", str(image_dir),
            "--ImageReader.camera_model", camera_model,
            "--ImageReader.single_camera", "1" if single_camera else "0",
            "--FeatureExtraction.use_gpu", "1",
            "--FeatureExtraction.gpu_index", str(gpu_index),
            "--FeatureExtraction.num_threads", "8",
            "--FeatureExtraction.max_image_size", "3200",
        ]
        
        # Set environment to disable Qt GUI (headless mode)
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['DISPLAY'] = ''
        
        subprocess.run(cmd, check=True, capture_output=True, env=env)
    
    def _match_features(self, database_path: Path, gpu_index: int, matcher: str = "sequential") -> None:
        """Match features between images."""
        if matcher == "sequential":
            cmd = [
                self.colmap_bin,
                "sequential_matcher",
                "--database_path", str(database_path),
                "--FeatureMatching.use_gpu", "1",
                "--FeatureMatching.gpu_index", str(gpu_index),
                "--SequentialMatching.overlap", "10",  # Match with 10 neighboring images
            ]
        else:  # exhaustive
            cmd = [
                self.colmap_bin,
                "exhaustive_matcher",
                "--database_path", str(database_path),
                "--FeatureMatching.use_gpu", "1",
                "--FeatureMatching.gpu_index", str(gpu_index),
                "--FeatureMatching.max_num_matches", "32768",
                "--FeatureMatching.max_ratio", "0.8",
            ]
        
        # Set environment to disable Qt GUI (headless mode)
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['DISPLAY'] = ''
        
        subprocess.run(cmd, check=True, capture_output=True, env=env)
    
    def _incremental_mapping(
        self,
        database_path: Path,
        image_dir: Path,
        output_dir: Path
    ) -> None:
        """Run incremental Structure-from-Motion."""
        cmd = [
            self.colmap_bin,
            "mapper",
            "--database_path", str(database_path),
            "--image_path", str(image_dir),
            "--output_path", str(output_dir),
        ]
        
        # Set environment to disable Qt GUI (headless mode)
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'offscreen'
        env['DISPLAY'] = ''
        
        subprocess.run(cmd, check=True, capture_output=True, env=env)
    
    def parse_sfm_result(self, model_dir: str) -> SfMResult:
        """
        Parse COLMAP binary output files.
        
        Args:
            model_dir: Directory containing cameras.bin, images.bin, points3D.bin
            
        Returns:
            Parsed SfM result
        """
        model_dir = Path(model_dir)
        
        cameras = self._read_cameras_binary(model_dir / "cameras.bin")
        images = self._read_images_binary(model_dir / "images.bin")
        points3D = self._read_points3D_binary(model_dir / "points3D.bin")
        
        # Calculate mean reprojection error
        errors = [p.error for p in points3D.values()]
        mean_error = np.mean(errors) if errors else 0.0
        
        return SfMResult(
            cameras=cameras,
            images=images,
            points3D=points3D,
            num_cameras=len(cameras),
            num_images=len(images),
            num_points=len(points3D),
            mean_reprojection_error=mean_error
        )
    
    def _read_cameras_binary(self, path: Path) -> Dict[int, Camera]:
        """Read cameras.bin file."""
        cameras = {}
        
        with open(path, "rb") as f:
            num_cameras = struct.unpack("Q", f.read(8))[0]
            
            for _ in range(num_cameras):
                camera_id = struct.unpack("I", f.read(4))[0]
                model_id = struct.unpack("I", f.read(4))[0]
                width = struct.unpack("Q", f.read(8))[0]
                height = struct.unpack("Q", f.read(8))[0]
                
                # Read parameters (number depends on model)
                num_params = self._get_num_params(model_id)
                params = np.frombuffer(f.read(8 * num_params), dtype=np.float64)
                
                model_name = self._get_model_name(model_id)
                
                cameras[camera_id] = Camera(
                    id=camera_id,
                    model=model_name,
                    width=width,
                    height=height,
                    params=params
                )
        
        return cameras
    
    def _read_images_binary(self, path: Path) -> Dict[int, Image]:
        """Read images.bin file."""
        images = {}
        
        with open(path, "rb") as f:
            num_images = struct.unpack("Q", f.read(8))[0]
            
            for _ in range(num_images):
                image_id = struct.unpack("I", f.read(4))[0]
                qvec = np.frombuffer(f.read(32), dtype=np.float64)
                tvec = np.frombuffer(f.read(24), dtype=np.float64)
                camera_id = struct.unpack("I", f.read(4))[0]
                
                # Read image name
                name_bytes = b""
                while True:
                    char = f.read(1)
                    if char == b"\x00":
                        break
                    name_bytes += char
                name = name_bytes.decode("utf-8")
                
                # Read 2D points
                num_points2D = struct.unpack("Q", f.read(8))[0]
                xys = np.zeros((num_points2D, 2))
                point3D_ids = np.zeros(num_points2D, dtype=np.int64)
                
                for i in range(num_points2D):
                    xys[i] = np.frombuffer(f.read(16), dtype=np.float64)
                    point3D_ids[i] = struct.unpack("Q", f.read(8))[0]
                
                images[image_id] = Image(
                    id=image_id,
                    qvec=qvec,
                    tvec=tvec,
                    camera_id=camera_id,
                    name=name,
                    xys=xys,
                    point3D_ids=point3D_ids
                )
        
        return images
    
    def _read_points3D_binary(self, path: Path) -> Dict[int, Point3D]:
        """Read points3D.bin file."""
        points3D = {}
        
        with open(path, "rb") as f:
            num_points = struct.unpack("Q", f.read(8))[0]
            
            for _ in range(num_points):
                point_id = struct.unpack("Q", f.read(8))[0]
                xyz = np.frombuffer(f.read(24), dtype=np.float64)
                rgb = np.frombuffer(f.read(3), dtype=np.uint8)
                error = struct.unpack("d", f.read(8))[0]
                
                # Read track
                track_length = struct.unpack("Q", f.read(8))[0]
                image_ids = np.zeros(track_length, dtype=np.int32)
                point2D_idxs = np.zeros(track_length, dtype=np.int32)
                
                for i in range(track_length):
                    image_ids[i] = struct.unpack("I", f.read(4))[0]
                    point2D_idxs[i] = struct.unpack("I", f.read(4))[0]
                
                points3D[point_id] = Point3D(
                    id=point_id,
                    xyz=xyz,
                    rgb=rgb,
                    error=error,
                    image_ids=image_ids,
                    point2D_idxs=point2D_idxs
                )
        
        return points3D
    
    def _get_num_params(self, model_id: int) -> int:
        """Get number of parameters for camera model."""
        params_map = {
            0: 3,  # SIMPLE_PINHOLE
            1: 4,  # PINHOLE
            2: 4,  # SIMPLE_RADIAL
            3: 5,  # RADIAL
            4: 8,  # OPENCV
            5: 12, # FULL_OPENCV
        }
        return params_map.get(model_id, 4)
    
    def _get_model_name(self, model_id: int) -> str:
        """Get camera model name."""
        models = {
            0: "SIMPLE_PINHOLE",
            1: "PINHOLE",
            2: "SIMPLE_RADIAL",
            3: "RADIAL",
            4: "OPENCV",
            5: "FULL_OPENCV",
        }
        return models.get(model_id, "UNKNOWN")


# Global COLMAP service instance
_colmap_service: Optional[COLMAPService] = None


def get_colmap_service(
    colmap_bin: Optional[str] = None,
    workspace_dir: Optional[str] = None
) -> COLMAPService:
    """
    Get or create global COLMAP service instance.
    
    Args:
        colmap_bin: Path to COLMAP binary
        workspace_dir: Working directory
        
    Returns:
        COLMAPService instance
    """
    global _colmap_service
    
    if _colmap_service is None:
        _colmap_service = COLMAPService(colmap_bin, workspace_dir)
    
    return _colmap_service
