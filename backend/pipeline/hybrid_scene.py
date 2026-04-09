"""Hybrid scene manager combining Gaussians, meshes, and dynamic objects."""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from pathlib import Path

from backend.pipeline.gaussian_splatting import GaussianParameters, GaussianSplattingTrainer
from backend.pipeline.dynamic_gaussians import DynamicGaussianParameters, DynamicGaussianTrainer
from backend.pipeline.mesh_extraction import Mesh, MeshExtractor

logger = logging.getLogger(__name__)


class RepresentationType(Enum):
    """Type of 3D representation."""
    GAUSSIAN = "gaussian"  # Static Gaussian splatting
    DYNAMIC_GAUSSIAN = "dynamic_gaussian"  # Time-varying Gaussians
    MESH = "mesh"  # Triangle mesh
    HYBRID = "hybrid"  # Combination of representations


@dataclass
class SceneObject:
    """Object in the hybrid scene."""
    object_id: int
    track_id: Optional[int]  # Track ID from object tracking
    label: str
    representation_type: RepresentationType
    
    # Representation data
    gaussians: Optional[GaussianParameters] = None
    dynamic_gaussians: Optional[DynamicGaussianParameters] = None
    mesh: Optional[Mesh] = None
    
    # Properties
    is_static: bool = True
    is_editable: bool = False
    
    # Bounding box
    bbox_min: Optional[np.ndarray] = None
    bbox_max: Optional[np.ndarray] = None
    
    def compute_bbox(self):
        """Compute bounding box from representation."""
        if self.gaussians is not None:
            positions = self.gaussians.positions
        elif self.dynamic_gaussians is not None:
            # Use first frame
            positions = self.dynamic_gaussians.positions[0]
        elif self.mesh is not None:
            positions = self.mesh.vertices
        else:
            return
        
        self.bbox_min = np.min(positions, axis=0)
        self.bbox_max = np.max(positions, axis=0)


@dataclass
class HybridScene:
    """Hybrid scene containing multiple representation types."""
    scene_id: str
    objects: List[SceneObject] = field(default_factory=list)
    
    # Scene metadata
    scene_type: str = "unknown"  # indoor, outdoor, mixed
    room_type: Optional[str] = None  # for indoor scenes
    
    # Scene bounds
    scene_bbox_min: Optional[np.ndarray] = None
    scene_bbox_max: Optional[np.ndarray] = None
    
    # Background (full scene reconstruction)
    background_gaussians: Optional[GaussianParameters] = None
    
    def add_object(self, obj: SceneObject):
        """Add object to scene."""
        self.objects.append(obj)
        logger.debug(f"Added object {obj.object_id} ({obj.label}) to scene")
    
    def compute_scene_bounds(self):
        """Compute scene bounding box encompassing all objects."""
        if not self.objects:
            logger.warning("No objects in scene, cannot compute bounds")
            return
        
        # Ensure all objects have bboxes
        for obj in self.objects:
            if obj.bbox_min is None or obj.bbox_max is None:
                obj.compute_bbox()
        
        # Compute scene bounds
        all_mins = [obj.bbox_min for obj in self.objects if obj.bbox_min is not None]
        all_maxs = [obj.bbox_max for obj in self.objects if obj.bbox_max is not None]
        
        if all_mins and all_maxs:
            self.scene_bbox_min = np.min(all_mins, axis=0)
            self.scene_bbox_max = np.max(all_maxs, axis=0)
            
            logger.info(
                f"Scene bounds: min={self.scene_bbox_min}, max={self.scene_bbox_max}"
            )
    
    def validate_completeness(self) -> Tuple[bool, str]:
        """
        Validate that all objects have valid representations.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.objects:
            return False, "Scene has no objects"
        
        for obj in self.objects:
            # Check representation matches type
            if obj.representation_type == RepresentationType.GAUSSIAN:
                if obj.gaussians is None:
                    return False, f"Object {obj.object_id} missing Gaussian representation"
            
            elif obj.representation_type == RepresentationType.DYNAMIC_GAUSSIAN:
                if obj.dynamic_gaussians is None:
                    return False, f"Object {obj.object_id} missing dynamic Gaussian representation"
            
            elif obj.representation_type == RepresentationType.MESH:
                if obj.mesh is None:
                    return False, f"Object {obj.object_id} missing mesh representation"
                if not obj.mesh.is_valid():
                    return False, f"Object {obj.object_id} has invalid mesh"
            
            elif obj.representation_type == RepresentationType.HYBRID:
                if obj.gaussians is None and obj.mesh is None:
                    return False, f"Object {obj.object_id} missing hybrid representations"
        
        return True, "Valid"
    
    def get_static_objects(self) -> List[SceneObject]:
        """Get all static objects."""
        return [obj for obj in self.objects if obj.is_static]
    
    def get_dynamic_objects(self) -> List[SceneObject]:
        """Get all dynamic objects."""
        return [obj for obj in self.objects if not obj.is_static]
    
    def get_editable_objects(self) -> List[SceneObject]:
        """Get all editable objects."""
        return [obj for obj in self.objects if obj.is_editable]
    
    def export_metadata(self, output_path: str):
        """Export scene metadata to JSON."""
        metadata = {
            'scene_id': self.scene_id,
            'scene_type': self.scene_type,
            'room_type': self.room_type,
            'num_objects': len(self.objects),
            'scene_bounds': {
                'min': self.scene_bbox_min.tolist() if self.scene_bbox_min is not None else None,
                'max': self.scene_bbox_max.tolist() if self.scene_bbox_max is not None else None
            },
            'objects': [
                {
                    'object_id': obj.object_id,
                    'track_id': obj.track_id,
                    'label': obj.label,
                    'representation_type': obj.representation_type.value,
                    'is_static': obj.is_static,
                    'is_editable': obj.is_editable,
                    'bbox_min': obj.bbox_min.tolist() if obj.bbox_min is not None else None,
                    'bbox_max': obj.bbox_max.tolist() if obj.bbox_max is not None else None
                }
                for obj in self.objects
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Exported scene metadata to {output_path}")


class HybridSceneManager:
    """Manager for creating and managing hybrid scenes."""
    
    def __init__(
        self,
        gaussian_trainer: GaussianSplattingTrainer,
        dynamic_trainer: DynamicGaussianTrainer,
        mesh_extractor: MeshExtractor,
        config: Optional[Dict] = None
    ):
        """
        Initialize hybrid scene manager.
        
        Args:
            gaussian_trainer: Static Gaussian trainer
            dynamic_trainer: Dynamic Gaussian trainer
            mesh_extractor: Mesh extractor
            config: Configuration dictionary
        """
        self.gaussian_trainer = gaussian_trainer
        self.dynamic_trainer = dynamic_trainer
        self.mesh_extractor = mesh_extractor
        self.config = config or {}
    
    def create_hybrid_scene(
        self,
        scene_id: str,
        tracked_objects: List[Dict],
        sparse_points: np.ndarray,
        scene_classification: Dict,
        images: List[np.ndarray],
        camera_poses: List[np.ndarray],
        camera_intrinsics: np.ndarray
    ) -> HybridScene:
        """
        Create hybrid scene from tracked objects and scene understanding.
        
        Args:
            scene_id: Unique scene identifier
            tracked_objects: List of tracked objects with labels, masks, etc.
            sparse_points: Sparse 3D point cloud
            scene_classification: Scene type and room type
            images: Input images
            camera_poses: Camera poses
            camera_intrinsics: Camera intrinsic matrix
            
        Returns:
            Hybrid scene
        """
        logger.info(f"Creating hybrid scene: {scene_id}")
        
        scene = HybridScene(
            scene_id=scene_id,
            scene_type=scene_classification.get('scene_type', 'unknown'),
            room_type=scene_classification.get('room_type')
        )
        
        # Process each tracked object
        for obj_data in tracked_objects:
            obj = self._create_scene_object(
                obj_data=obj_data,
                sparse_points=sparse_points,
                images=images,
                camera_poses=camera_poses,
                camera_intrinsics=camera_intrinsics
            )
            
            if obj is not None:
                scene.add_object(obj)
        
        # Create background representation
        logger.info("Creating background Gaussian representation")
        scene.background_gaussians = self.gaussian_trainer.initialize_from_sparse_points(
            sparse_points=sparse_points,
            num_points=self.config.get('background_num_gaussians', 100000)
        )
        
        # Compute scene bounds
        scene.compute_scene_bounds()
        
        # Validate scene
        is_valid, error_msg = scene.validate_completeness()
        if not is_valid:
            logger.error(f"Scene validation failed: {error_msg}")
        else:
            logger.info(f"Scene created successfully with {len(scene.objects)} objects")
        
        return scene
    
    def _create_scene_object(
        self,
        obj_data: Dict,
        sparse_points: np.ndarray,
        images: List[np.ndarray],
        camera_poses: List[np.ndarray],
        camera_intrinsics: np.ndarray
    ) -> Optional[SceneObject]:
        """
        Create scene object with appropriate representation.
        
        Args:
            obj_data: Object data (track_id, label, is_static, detections, masks)
            sparse_points: Sparse point cloud
            images: Input images
            camera_poses: Camera poses
            camera_intrinsics: Camera intrinsics
            
        Returns:
            Scene object or None if creation failed
        """
        track_id = obj_data['track_id']
        label = obj_data['label']
        is_static = obj_data.get('is_static', True)
        
        logger.info(f"Creating object: track_id={track_id}, label={label}, static={is_static}")
        
        # Determine representation type based on object properties
        representation_type, is_editable = self._determine_representation_type(
            label=label,
            is_static=is_static
        )
        
        obj = SceneObject(
            object_id=len(self.config.get('existing_objects', [])),
            track_id=track_id,
            label=label,
            representation_type=representation_type,
            is_static=is_static,
            is_editable=is_editable
        )
        
        try:
            # Create representation based on type
            if representation_type == RepresentationType.GAUSSIAN:
                obj.gaussians = self._create_static_gaussian(obj_data, sparse_points)
            
            elif representation_type == RepresentationType.DYNAMIC_GAUSSIAN:
                obj.dynamic_gaussians = self._create_dynamic_gaussian(
                    obj_data, images, camera_poses, camera_intrinsics
                )
            
            elif representation_type == RepresentationType.MESH:
                # First create Gaussians, then extract mesh
                gaussians = self._create_static_gaussian(obj_data, sparse_points)
                obj.mesh = self.mesh_extractor.extract_from_gaussians(gaussians)
                
                if obj.mesh is None:
                    logger.warning(f"Mesh extraction failed for {label}, falling back to Gaussian")
                    obj.representation_type = RepresentationType.GAUSSIAN
                    obj.gaussians = gaussians
                    obj.is_editable = False
            
            elif representation_type == RepresentationType.HYBRID:
                # Create both Gaussian and mesh
                obj.gaussians = self._create_static_gaussian(obj_data, sparse_points)
                obj.mesh = self.mesh_extractor.extract_from_gaussians(obj.gaussians)
                
                if obj.mesh is None:
                    logger.warning(f"Mesh extraction failed, using Gaussian only")
                    obj.representation_type = RepresentationType.GAUSSIAN
            
            # Compute bounding box
            obj.compute_bbox()
            
            return obj
            
        except Exception as e:
            logger.error(f"Failed to create object {track_id}: {e}")
            return None
    
    def _determine_representation_type(
        self,
        label: str,
        is_static: bool
    ) -> Tuple[RepresentationType, bool]:
        """
        Determine appropriate representation type for object.
        
        Args:
            label: Object label
            is_static: Whether object is static
            
        Returns:
            Tuple of (representation_type, is_editable)
        """
        # Dynamic objects use dynamic Gaussians
        if not is_static:
            return RepresentationType.DYNAMIC_GAUSSIAN, False
        
        # Editable objects (furniture, etc.) use meshes
        editable_labels = self.config.get('editable_labels', [
            'chair', 'table', 'sofa', 'bed', 'desk', 'cabinet'
        ])
        
        if label in editable_labels:
            return RepresentationType.MESH, True
        
        # Default to static Gaussians
        return RepresentationType.GAUSSIAN, False
    
    def _create_static_gaussian(
        self,
        obj_data: Dict,
        sparse_points: np.ndarray
    ) -> GaussianParameters:
        """Create static Gaussian representation for object."""
        # Filter sparse points to object region (simplified)
        # In practice, would use masks to filter points
        
        num_points = self.config.get('num_gaussians_per_object', 5000)
        
        gaussians = self.gaussian_trainer.initialize_from_sparse_points(
            sparse_points=sparse_points,
            num_points=num_points
        )
        
        return gaussians
    
    def _create_dynamic_gaussian(
        self,
        obj_data: Dict,
        images: List[np.ndarray],
        camera_poses: List[np.ndarray],
        camera_intrinsics: np.ndarray
    ) -> DynamicGaussianParameters:
        """Create dynamic Gaussian representation for object."""
        track_id = obj_data['track_id']
        label = obj_data['label']
        frames = obj_data.get('frames', [])
        masks = obj_data.get('masks', [])
        
        dynamic_gaussians = self.dynamic_trainer.train_dynamic_object(
            track_id=track_id,
            label=label,
            frames=frames,
            images=[images[f] for f in frames],
            masks=masks,
            camera_poses=[camera_poses[f] for f in frames],
            camera_intrinsics=camera_intrinsics
        )
        
        return dynamic_gaussians
    
    def save_scene(
        self,
        scene: HybridScene,
        output_dir: str
    ):
        """
        Save hybrid scene to disk.
        
        Args:
            scene: Hybrid scene
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving scene to {output_dir}")
        
        # Save metadata
        scene.export_metadata(str(output_path / "scene_metadata.json"))
        
        # Save object representations
        for obj in scene.objects:
            obj_dir = output_path / f"object_{obj.object_id}"
            obj_dir.mkdir(exist_ok=True)
            
            # Save based on representation type
            if obj.gaussians is not None:
                # Save Gaussian parameters (simplified)
                np.savez(
                    obj_dir / "gaussians.npz",
                    positions=obj.gaussians.positions,
                    opacities=obj.gaussians.opacities,
                    scales=obj.gaussians.scales,
                    rotations=obj.gaussians.rotations,
                    colors=obj.gaussians.colors
                )
            
            if obj.mesh is not None:
                # Save mesh
                self.mesh_extractor.export_to_obj(
                    obj.mesh,
                    str(obj_dir / "mesh.obj")
                )
            
            if obj.dynamic_gaussians is not None:
                # Save dynamic Gaussians (simplified)
                np.savez(
                    obj_dir / "dynamic_gaussians.npz",
                    timestamps=obj.dynamic_gaussians.timestamps,
                    num_timesteps=obj.dynamic_gaussians.num_timesteps
                )
        
        # Save background
        if scene.background_gaussians is not None:
            np.savez(
                output_path / "background_gaussians.npz",
                positions=scene.background_gaussians.positions,
                opacities=scene.background_gaussians.opacities,
                scales=scene.background_gaussians.scales,
                rotations=scene.background_gaussians.rotations,
                colors=scene.background_gaussians.colors
            )
        
        logger.info("Scene saved successfully")
