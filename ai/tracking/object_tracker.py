"""Multi-frame object tracking service."""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class TrackedObject:
    """Single detection in a track."""
    frame_id: int
    label: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    world_position: Optional[np.ndarray] = None  # 3D position if triangulated


@dataclass
class Track:
    """Object track across multiple frames."""
    track_id: int
    label: str
    detections: List[TrackedObject] = field(default_factory=list)
    is_static: Optional[bool] = None
    world_positions: List[np.ndarray] = field(default_factory=list)
    position_variance: Optional[float] = None


class ObjectTracker:
    """Multi-frame object tracker using IoU-based matching."""
    
    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_frames_skip: int = 5,
        static_variance_threshold: float = 0.1
    ):
        """
        Initialize object tracker.
        
        Args:
            iou_threshold: Minimum IoU for matching detections to tracks
            max_frames_skip: Maximum frames a track can be missing before deletion
            static_variance_threshold: Position variance threshold for static classification
        """
        self.iou_threshold = iou_threshold
        self.max_frames_skip = max_frames_skip
        self.static_variance_threshold = static_variance_threshold
        
        self.tracks: List[Track] = []
        self.next_track_id = 0
        self.frame_count = 0
    
    def update(
        self,
        detections: List[Dict],
        frame_id: Optional[int] = None
    ) -> List[Track]:
        """
        Update tracks with new detections from current frame.
        
        Args:
            detections: List of detections with 'label', 'confidence', 'bbox'
            frame_id: Frame ID (auto-increments if None)
            
        Returns:
            Updated list of active tracks
        """
        if frame_id is None:
            frame_id = self.frame_count
        
        self.frame_count = frame_id + 1
        
        # Convert detections to TrackedObjects
        current_detections = [
            TrackedObject(
                frame_id=frame_id,
                label=d['label'],
                confidence=d['confidence'],
                bbox=d['bbox']
            )
            for d in detections
        ]
        
        # Match detections to existing tracks
        matched_tracks, matched_detections = self._match_detections_to_tracks(
            current_detections
        )
        
        # Update matched tracks
        for track_idx, det_idx in zip(matched_tracks, matched_detections):
            detection = current_detections[det_idx]
            
            # Validate label consistency
            if self.tracks[track_idx].label != detection.label:
                logger.warning(
                    f"Label mismatch in track {self.tracks[track_idx].track_id}: "
                    f"{self.tracks[track_idx].label} != {detection.label}"
                )
                # Keep original label for consistency
                detection.label = self.tracks[track_idx].label
            
            self.tracks[track_idx].detections.append(detection)
        
        # Create new tracks for unmatched detections
        unmatched_detection_indices = set(range(len(current_detections))) - set(matched_detections)
        
        for det_idx in unmatched_detection_indices:
            detection = current_detections[det_idx]
            new_track = Track(
                track_id=self.next_track_id,
                label=detection.label,
                detections=[detection]
            )
            self.tracks.append(new_track)
            self.next_track_id += 1
            logger.debug(f"Created new track {new_track.track_id} for {detection.label}")
        
        # Remove stale tracks (not updated for max_frames_skip frames)
        self.tracks = [
            track for track in self.tracks
            if frame_id - track.detections[-1].frame_id <= self.max_frames_skip
        ]
        
        return self.tracks
    
    def _match_detections_to_tracks(
        self,
        detections: List[TrackedObject]
    ) -> Tuple[List[int], List[int]]:
        """
        Match detections to existing tracks using IoU and label consistency.
        
        Args:
            detections: Current frame detections
            
        Returns:
            Tuple of (matched_track_indices, matched_detection_indices)
        """
        if not self.tracks or not detections:
            return [], []
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(self.tracks), len(detections)))
        
        for i, track in enumerate(self.tracks):
            last_detection = track.detections[-1]
            
            for j, detection in enumerate(detections):
                # Only match if labels are consistent
                if track.label == detection.label:
                    iou = self._compute_iou(last_detection.bbox, detection.bbox)
                    iou_matrix[i, j] = iou
        
        # Greedy matching: match highest IoU pairs above threshold
        matched_tracks = []
        matched_detections = []
        
        while True:
            # Find maximum IoU
            max_iou = np.max(iou_matrix)
            
            if max_iou < self.iou_threshold:
                break
            
            # Get indices of maximum
            track_idx, det_idx = np.unravel_index(
                np.argmax(iou_matrix),
                iou_matrix.shape
            )
            
            matched_tracks.append(track_idx)
            matched_detections.append(det_idx)
            
            # Remove matched track and detection from consideration
            iou_matrix[track_idx, :] = 0
            iou_matrix[:, det_idx] = 0
        
        return matched_tracks, matched_detections
    
    def _compute_iou(
        self,
        bbox1: Tuple[float, float, float, float],
        bbox2: Tuple[float, float, float, float]
    ) -> float:
        """
        Compute Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: First bbox (x1, y1, x2, y2)
            bbox2: Second bbox (x1, y1, x2, y2)
            
        Returns:
            IoU value in [0, 1]
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Compute intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Compute union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def triangulate_and_classify(
        self,
        camera_poses: List[np.ndarray],
        camera_intrinsics: np.ndarray
    ):
        """
        Triangulate 3D positions for tracks and classify as static/dynamic.
        
        Args:
            camera_poses: List of camera extrinsics (4x4 matrices) for each frame
            camera_intrinsics: Camera intrinsic matrix (3x3)
        """
        for track in self.tracks:
            if len(track.detections) < 2:
                # Need at least 2 observations for triangulation
                track.is_static = True  # Assume static if only one observation
                continue
            
            # Triangulate 3D position for each detection
            world_positions = []
            
            for detection in track.detections:
                frame_id = detection.frame_id
                
                if frame_id >= len(camera_poses):
                    logger.warning(f"No camera pose for frame {frame_id}")
                    continue
                
                # Get bbox center as 2D observation
                x1, y1, x2, y2 = detection.bbox
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Simple triangulation using camera center and ray direction
                camera_pose = camera_poses[frame_id]
                camera_center = camera_pose[:3, 3]
                
                # Compute ray direction (simplified)
                # In practice, use proper triangulation with multiple views
                world_positions.append(camera_center)
                detection.world_position = camera_center
            
            track.world_positions = world_positions
            
            # Compute position variance
            if len(world_positions) >= 2:
                positions_array = np.array(world_positions)
                variance = np.var(positions_array, axis=0).mean()
                track.position_variance = float(variance)
                
                # Classify as static or dynamic
                track.is_static = variance < self.static_variance_threshold
                
                logger.debug(
                    f"Track {track.track_id} ({track.label}): "
                    f"variance={variance:.4f}, static={track.is_static}"
                )
            else:
                track.is_static = True
    
    def get_active_tracks(self) -> List[Track]:
        """Get all active tracks."""
        return self.tracks
    
    def get_static_tracks(self) -> List[Track]:
        """Get tracks classified as static."""
        return [t for t in self.tracks if t.is_static is True]
    
    def get_dynamic_tracks(self) -> List[Track]:
        """Get tracks classified as dynamic."""
        return [t for t in self.tracks if t.is_static is False]
    
    def validate_track_consistency(self, track: Track) -> bool:
        """
        Validate track label consistency.
        
        Args:
            track: Track to validate
            
        Returns:
            True if all detections have same label
        """
        if not track.detections:
            return True
        
        first_label = track.detections[0].label
        
        for detection in track.detections[1:]:
            if detection.label != first_label:
                logger.error(
                    f"Track {track.track_id} has inconsistent labels: "
                    f"{first_label} != {detection.label}"
                )
                return False
        
        return True
    
    def validate_track_ids_unique(self) -> bool:
        """
        Validate that all track IDs are unique.
        
        Returns:
            True if all track IDs are unique
        """
        track_ids = [t.track_id for t in self.tracks]
        
        if len(track_ids) != len(set(track_ids)):
            logger.error("Duplicate track IDs found")
            return False
        
        return True
    
    def get_track_stats(self) -> Dict:
        """Get statistics about tracks."""
        if not self.tracks:
            return {
                'num_tracks': 0,
                'num_static': 0,
                'num_dynamic': 0,
                'labels': []
            }
        
        labels = [t.label for t in self.tracks]
        
        return {
            'num_tracks': len(self.tracks),
            'num_static': len(self.get_static_tracks()),
            'num_dynamic': len(self.get_dynamic_tracks()),
            'labels': list(set(labels)),
            'label_counts': {label: labels.count(label) for label in set(labels)},
            'avg_track_length': np.mean([len(t.detections) for t in self.tracks]),
            'max_track_length': max([len(t.detections) for t in self.tracks]),
            'min_track_length': min([len(t.detections) for t in self.tracks])
        }
