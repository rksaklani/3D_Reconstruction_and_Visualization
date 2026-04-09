"""SfM result validation."""

import numpy as np
from typing import Dict, List, Tuple
from .colmap_service import SfMResult, Camera, Image, Point3D
import logging

logger = logging.getLogger(__name__)


class SfMValidationError(Exception):
    """SfM validation error."""
    pass


class SfMValidator:
    """Validate Structure-from-Motion results."""
    
    def __init__(
        self,
        min_features_per_image: int = 100,
        max_reprojection_error: float = 2.0,
        min_triangulation_angle: float = 1.5
    ):
        """
        Initialize validator.
        
        Args:
            min_features_per_image: Minimum features required per image
            max_reprojection_error: Maximum allowed reprojection error (pixels)
            min_triangulation_angle: Minimum triangulation angle (degrees)
        """
        self.min_features_per_image = min_features_per_image
        self.max_reprojection_error = max_reprojection_error
        self.min_triangulation_angle = min_triangulation_angle
    
    def validate(self, sfm_result: SfMResult) -> Dict[str, any]:
        """
        Validate SfM result.
        
        Args:
            sfm_result: SfM result to validate
            
        Returns:
            Validation report dictionary
            
        Raises:
            SfMValidationError: If validation fails
        """
        report = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        # Validate feature counts
        feature_validation = self._validate_feature_counts(sfm_result)
        report['statistics']['features'] = feature_validation
        if not feature_validation['valid']:
            report['valid'] = False
            report['errors'].append(feature_validation['error'])
        
        # Validate match graph connectivity
        connectivity_validation = self._validate_connectivity(sfm_result)
        report['statistics']['connectivity'] = connectivity_validation
        if not connectivity_validation['valid']:
            report['valid'] = False
            report['errors'].append(connectivity_validation['error'])
        
        # Validate reprojection errors
        reprojection_validation = self._validate_reprojection_errors(sfm_result)
        report['statistics']['reprojection'] = reprojection_validation
        if not reprojection_validation['valid']:
            report['valid'] = False
            report['errors'].append(reprojection_validation['error'])
        
        # Validate camera poses
        pose_validation = self._validate_camera_poses(sfm_result)
        report['statistics']['poses'] = pose_validation
        if not pose_validation['valid']:
            report['valid'] = False
            report['errors'].append(pose_validation['error'])
        
        # Validate cheirality
        cheirality_validation = self._validate_cheirality(sfm_result)
        report['statistics']['cheirality'] = cheirality_validation
        if not cheirality_validation['valid']:
            report['valid'] = False
            report['errors'].append(cheirality_validation['error'])
        
        if not report['valid']:
            logger.error(f"SfM validation failed: {report['errors']}")
            raise SfMValidationError(f"Validation failed: {', '.join(report['errors'])}")
        
        logger.info("SfM validation passed")
        return report
    
    def _validate_feature_counts(self, sfm_result: SfMResult) -> Dict:
        """Validate minimum feature count per image."""
        feature_counts = []
        
        for image in sfm_result.images.values():
            # Count valid features (those with 3D points)
            valid_features = np.sum(image.point3D_ids != -1)
            feature_counts.append(valid_features)
        
        min_count = min(feature_counts) if feature_counts else 0
        mean_count = np.mean(feature_counts) if feature_counts else 0
        
        valid = min_count >= self.min_features_per_image
        
        return {
            'valid': valid,
            'min_features': int(min_count),
            'mean_features': float(mean_count),
            'threshold': self.min_features_per_image,
            'error': f"Insufficient features: min={min_count}, required={self.min_features_per_image}" if not valid else None
        }
    
    def _validate_connectivity(self, sfm_result: SfMResult) -> Dict:
        """Check match graph connectivity."""
        # Build adjacency matrix
        num_images = len(sfm_result.images)
        adjacency = np.zeros((num_images, num_images), dtype=bool)
        
        image_ids = list(sfm_result.images.keys())
        id_to_idx = {img_id: idx for idx, img_id in enumerate(image_ids)}
        
        # Mark connections based on shared 3D points
        for point in sfm_result.points3D.values():
            image_indices = [id_to_idx[img_id] for img_id in point.image_ids if img_id in id_to_idx]
            
            for i in range(len(image_indices)):
                for j in range(i + 1, len(image_indices)):
                    adjacency[image_indices[i], image_indices[j]] = True
                    adjacency[image_indices[j], image_indices[i]] = True
        
        # Check connectivity using BFS
        visited = np.zeros(num_images, dtype=bool)
        queue = [0]
        visited[0] = True
        
        while queue:
            current = queue.pop(0)
            for neighbor in range(num_images):
                if adjacency[current, neighbor] and not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)
        
        connected = np.all(visited)
        num_connected = np.sum(visited)
        
        return {
            'valid': connected,
            'num_connected': int(num_connected),
            'num_total': num_images,
            'connectivity_ratio': float(num_connected / num_images) if num_images > 0 else 0.0,
            'error': f"Disconnected match graph: {num_connected}/{num_images} images connected" if not connected else None
        }
    
    def _validate_reprojection_errors(self, sfm_result: SfMResult) -> Dict:
        """Validate reprojection errors."""
        errors = [p.error for p in sfm_result.points3D.values()]
        
        if not errors:
            return {
                'valid': False,
                'error': "No 3D points found"
            }
        
        mean_error = np.mean(errors)
        max_error = np.max(errors)
        median_error = np.median(errors)
        
        valid = mean_error < self.max_reprojection_error
        
        return {
            'valid': valid,
            'mean_error': float(mean_error),
            'max_error': float(max_error),
            'median_error': float(median_error),
            'threshold': self.max_reprojection_error,
            'error': f"High reprojection error: mean={mean_error:.2f}, threshold={self.max_reprojection_error}" if not valid else None
        }
    
    def _validate_camera_poses(self, sfm_result: SfMResult) -> Dict:
        """Validate camera pose validity (SE(3) transformations)."""
        invalid_poses = []
        
        for image in sfm_result.images.values():
            # Check quaternion is unit length
            qvec = image.qvec
            qnorm = np.linalg.norm(qvec)
            
            if not np.isclose(qnorm, 1.0, atol=1e-6):
                invalid_poses.append(image.id)
        
        valid = len(invalid_poses) == 0
        
        return {
            'valid': valid,
            'num_invalid': len(invalid_poses),
            'num_total': len(sfm_result.images),
            'invalid_image_ids': invalid_poses,
            'error': f"Invalid camera poses: {len(invalid_poses)} images have non-unit quaternions" if not valid else None
        }
    
    def _validate_cheirality(self, sfm_result: SfMResult) -> Dict:
        """Validate cheirality constraint (points in front of cameras)."""
        violations = 0
        total_observations = 0
        
        for point in sfm_result.points3D.values():
            for img_id in point.image_ids:
                if img_id not in sfm_result.images:
                    continue
                
                image = sfm_result.images[img_id]
                
                # Transform point to camera coordinates
                # R = quat_to_rotation(qvec)
                # P_cam = R @ (P_world - tvec)
                R = self._quat_to_rotation(image.qvec)
                P_world = point.xyz
                P_cam = R @ (P_world - image.tvec)
                
                # Check if point is in front of camera (positive Z)
                if P_cam[2] <= 0:
                    violations += 1
                
                total_observations += 1
        
        violation_ratio = violations / total_observations if total_observations > 0 else 0.0
        valid = violations == 0
        
        return {
            'valid': valid,
            'num_violations': violations,
            'num_observations': total_observations,
            'violation_ratio': float(violation_ratio),
            'error': f"Cheirality violations: {violations}/{total_observations} observations behind camera" if not valid else None
        }
    
    def _quat_to_rotation(self, qvec: np.ndarray) -> np.ndarray:
        """Convert quaternion to rotation matrix."""
        w, x, y, z = qvec
        
        R = np.array([
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y],
            [2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x],
            [2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y]
        ])
        
        return R
