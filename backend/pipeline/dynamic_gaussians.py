"""Dynamic Gaussian Splatting for time-varying objects."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

from backend.pipeline.gaussian_splatting import GaussianParameters, GaussianSplattingTrainer

logger = logging.getLogger(__name__)


@dataclass
class DynamicGaussianParameters:
    """Time-varying Gaussian parameters for dynamic objects."""
    track_id: int
    label: str
    
    # Time-indexed Gaussian parameters
    timestamps: List[float] = field(default_factory=list)
    positions: List[np.ndarray] = field(default_factory=list)  # List of (N, 3)
    opacities: List[np.ndarray] = field(default_factory=list)  # List of (N, 1)
    scales: List[np.ndarray] = field(default_factory=list)  # List of (N, 3)
    rotations: List[np.ndarray] = field(default_factory=list)  # List of (N, 4)
    colors: List[np.ndarray] = field(default_factory=list)  # List of (N, 3)
    
    # Motion parameters
    velocities: Optional[np.ndarray] = None  # (N, 3) linear velocities
    angular_velocities: Optional[np.ndarray] = None  # (N, 3) angular velocities
    
    # Metadata
    num_gaussians: int = 0
    num_timesteps: int = 0
    is_rigid: bool = True  # True if object moves rigidly


class DynamicGaussianTrainer:
    """Trainer for dynamic Gaussian representations."""
    
    def __init__(
        self,
        static_trainer: GaussianSplattingTrainer,
        config: Optional[Dict] = None
    ):
        """
        Initialize dynamic Gaussian trainer.
        
        Args:
            static_trainer: Static Gaussian trainer instance
            config: Configuration dictionary
        """
        self.static_trainer = static_trainer
        self.config = config or {}
    
    def train_dynamic_object(
        self,
        track_id: int,
        label: str,
        frames: List[int],
        images: List[np.ndarray],
        masks: List[np.ndarray],
        camera_poses: List[np.ndarray],
        camera_intrinsics: np.ndarray,
        sparse_points: Optional[np.ndarray] = None
    ) -> DynamicGaussianParameters:
        """
        Train dynamic Gaussian model for a tracked object.
        
        Args:
            track_id: Object track ID
            label: Object label
            frames: Frame indices
            images: List of images containing the object
            masks: List of segmentation masks for the object
            camera_poses: Camera poses for each frame
            camera_intrinsics: Camera intrinsic matrix
            sparse_points: Optional sparse 3D points for initialization
            
        Returns:
            Dynamic Gaussian parameters
        """
        logger.info(f"Training dynamic Gaussians for track {track_id} ({label})")
        
        num_frames = len(frames)
        timestamps = np.array(frames, dtype=np.float32)
        
        # Train separate Gaussian model for each frame
        frame_gaussians = []
        
        for i, (frame_idx, image, mask) in enumerate(zip(frames, images, masks)):
            logger.debug(f"Training frame {i+1}/{num_frames} (frame_idx={frame_idx})")
            
            # Mask the image to focus on the object
            masked_image = image * mask[:, :, np.newaxis]
            
            # Initialize Gaussians for this frame
            if sparse_points is not None and i == 0:
                # Use sparse points for first frame
                gaussians = self.static_trainer.initialize_from_sparse_points(
                    sparse_points=sparse_points,
                    num_points=self.config.get('num_gaussians_per_object', 1000)
                )
            elif i > 0:
                # Use previous frame as initialization
                gaussians = frame_gaussians[-1]
            else:
                # Random initialization
                gaussians = self._random_initialization(
                    num_points=self.config.get('num_gaussians_per_object', 1000)
                )
            
            # TODO: Actual training would happen here
            # For now, we just store the initialized parameters
            
            frame_gaussians.append(gaussians)
        
        # Extract time-varying parameters
        dynamic_params = DynamicGaussianParameters(
            track_id=track_id,
            label=label,
            timestamps=timestamps.tolist(),
            positions=[g.positions for g in frame_gaussians],
            opacities=[g.opacities for g in frame_gaussians],
            scales=[g.scales for g in frame_gaussians],
            rotations=[g.rotations for g in frame_gaussians],
            colors=[g.colors for g in frame_gaussians],
            num_gaussians=frame_gaussians[0].positions.shape[0],
            num_timesteps=num_frames
        )
        
        # Compute velocities
        dynamic_params.velocities = self._compute_velocities(dynamic_params)
        dynamic_params.angular_velocities = self._compute_angular_velocities(dynamic_params)
        
        # Determine if motion is rigid
        dynamic_params.is_rigid = self._check_rigid_motion(dynamic_params)
        
        logger.info(
            f"Trained dynamic Gaussians: {dynamic_params.num_gaussians} Gaussians, "
            f"{dynamic_params.num_timesteps} timesteps, rigid={dynamic_params.is_rigid}"
        )
        
        return dynamic_params
    
    def _random_initialization(self, num_points: int) -> GaussianParameters:
        """Random initialization of Gaussians."""
        positions = np.random.randn(num_points, 3).astype(np.float32)
        opacities = np.full((num_points, 1), 0.1, dtype=np.float32)
        scales = np.full((num_points, 3), 1.0, dtype=np.float32)
        rotations = np.tile([1.0, 0.0, 0.0, 0.0], (num_points, 1)).astype(np.float32)
        colors = np.full((num_points, 3), 0.5, dtype=np.float32)
        
        return GaussianParameters(
            positions=positions,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            colors=colors,
            sh_degree=0
        )
    
    def _compute_velocities(
        self,
        params: DynamicGaussianParameters
    ) -> np.ndarray:
        """
        Compute linear velocities from position changes.
        
        Args:
            params: Dynamic Gaussian parameters
            
        Returns:
            Velocities (N, 3)
        """
        if params.num_timesteps < 2:
            return np.zeros((params.num_gaussians, 3), dtype=np.float32)
        
        # Compute average velocity across all timesteps
        velocities = []
        
        for i in range(params.num_timesteps - 1):
            dt = params.timestamps[i + 1] - params.timestamps[i]
            if dt > 0:
                dp = params.positions[i + 1] - params.positions[i]
                v = dp / dt
                velocities.append(v)
        
        if velocities:
            # Average velocities
            avg_velocity = np.mean(velocities, axis=0)
            return avg_velocity
        
        return np.zeros((params.num_gaussians, 3), dtype=np.float32)
    
    def _compute_angular_velocities(
        self,
        params: DynamicGaussianParameters
    ) -> np.ndarray:
        """
        Compute angular velocities from rotation changes.
        
        Args:
            params: Dynamic Gaussian parameters
            
        Returns:
            Angular velocities (N, 3)
        """
        if params.num_timesteps < 2:
            return np.zeros((params.num_gaussians, 3), dtype=np.float32)
        
        # Simplified: compute rotation differences
        # In practice, would use proper quaternion differentiation
        
        return np.zeros((params.num_gaussians, 3), dtype=np.float32)
    
    def _check_rigid_motion(
        self,
        params: DynamicGaussianParameters,
        threshold: float = 0.1
    ) -> bool:
        """
        Check if object motion is approximately rigid.
        
        Args:
            params: Dynamic Gaussian parameters
            threshold: Variance threshold for rigidity
            
        Returns:
            True if motion is rigid
        """
        if params.num_timesteps < 2:
            return True
        
        # Compute relative position changes
        relative_changes = []
        
        for i in range(params.num_timesteps - 1):
            # Compute pairwise distances at time i
            pos_i = params.positions[i]
            pos_i_next = params.positions[i + 1]
            
            # Sample a few point pairs
            n_samples = min(100, params.num_gaussians)
            indices = np.random.choice(params.num_gaussians, n_samples, replace=False)
            
            for idx1 in indices[:10]:
                for idx2 in indices[10:20]:
                    dist_i = np.linalg.norm(pos_i[idx1] - pos_i[idx2])
                    dist_i_next = np.linalg.norm(pos_i_next[idx1] - pos_i_next[idx2])
                    
                    if dist_i > 0:
                        relative_change = abs(dist_i_next - dist_i) / dist_i
                        relative_changes.append(relative_change)
        
        if relative_changes:
            variance = np.var(relative_changes)
            is_rigid = variance < threshold
            
            logger.debug(f"Rigid motion check: variance={variance:.4f}, rigid={is_rigid}")
            return is_rigid
        
        return True
    
    def interpolate(
        self,
        params: DynamicGaussianParameters,
        timestamp: float
    ) -> GaussianParameters:
        """
        Interpolate Gaussian parameters at arbitrary timestamp.
        
        Args:
            params: Dynamic Gaussian parameters
            timestamp: Target timestamp
            
        Returns:
            Interpolated static Gaussian parameters
        """
        timestamps = np.array(params.timestamps)
        
        # Find surrounding timestamps
        if timestamp <= timestamps[0]:
            idx = 0
            alpha = 0.0
        elif timestamp >= timestamps[-1]:
            idx = len(timestamps) - 2
            alpha = 1.0
        else:
            # Find interval
            idx = np.searchsorted(timestamps, timestamp) - 1
            t0, t1 = timestamps[idx], timestamps[idx + 1]
            alpha = (timestamp - t0) / (t1 - t0)
        
        # Linear interpolation
        positions = (1 - alpha) * params.positions[idx] + alpha * params.positions[idx + 1]
        opacities = (1 - alpha) * params.opacities[idx] + alpha * params.opacities[idx + 1]
        scales = (1 - alpha) * params.scales[idx] + alpha * params.scales[idx + 1]
        colors = (1 - alpha) * params.colors[idx] + alpha * params.colors[idx + 1]
        
        # Quaternion interpolation (SLERP would be better)
        rotations = (1 - alpha) * params.rotations[idx] + alpha * params.rotations[idx + 1]
        # Normalize quaternions
        rotations = rotations / np.linalg.norm(rotations, axis=1, keepdims=True)
        
        return GaussianParameters(
            positions=positions,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            colors=colors,
            sh_degree=0
        )
    
    def extrapolate(
        self,
        params: DynamicGaussianParameters,
        timestamp: float
    ) -> GaussianParameters:
        """
        Extrapolate Gaussian parameters beyond observed timestamps using velocities.
        
        Args:
            params: Dynamic Gaussian parameters
            timestamp: Target timestamp (beyond observed range)
            
        Returns:
            Extrapolated Gaussian parameters
        """
        last_timestamp = params.timestamps[-1]
        dt = timestamp - last_timestamp
        
        # Use last frame as base
        positions = params.positions[-1].copy()
        opacities = params.opacities[-1].copy()
        scales = params.scales[-1].copy()
        rotations = params.rotations[-1].copy()
        colors = params.colors[-1].copy()
        
        # Apply velocities
        if params.velocities is not None:
            positions += params.velocities * dt
        
        # Apply angular velocities (simplified)
        if params.angular_velocities is not None:
            # In practice, would integrate angular velocity properly
            pass
        
        return GaussianParameters(
            positions=positions,
            opacities=opacities,
            scales=scales,
            rotations=rotations,
            colors=colors,
            sh_degree=0
        )


def merge_dynamic_gaussians(
    dynamic_objects: List[DynamicGaussianParameters],
    timestamp: float,
    trainer: DynamicGaussianTrainer
) -> List[GaussianParameters]:
    """
    Merge all dynamic objects at a specific timestamp.
    
    Args:
        dynamic_objects: List of dynamic Gaussian parameters
        timestamp: Target timestamp
        trainer: Dynamic Gaussian trainer for interpolation
        
    Returns:
        List of static Gaussian parameters (one per object)
    """
    merged = []
    
    for dynamic_obj in dynamic_objects:
        # Interpolate or extrapolate to target timestamp
        if timestamp <= dynamic_obj.timestamps[-1]:
            gaussians = trainer.interpolate(dynamic_obj, timestamp)
        else:
            gaussians = trainer.extrapolate(dynamic_obj, timestamp)
        
        merged.append(gaussians)
    
    return merged
