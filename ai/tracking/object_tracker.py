"""Object tracking for dynamic scene reconstruction."""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Track:
    """Object track across frames."""
    track_id: int
    class_name: str
    bboxes: List[Tuple[int, int, int, int]] = field(default_factory=list)  # List of (x1, y1, x2, y2)
    frame_ids: List[int] = field(default_factory=list)
    confidences: List[float] = field(default_factory=list)
    is_active: bool = True
    
    @property
    def length(self) -> int:
        """Get track length."""
        return len(self.frame_ids)
    
    @property
    def avg_confidence(self) -> float:
        """Get average confidence."""
        return np.mean(self.confidences) if self.confidences else 0.0


@dataclass
class TrackingResult:
    """Tracking result for a frame."""
    frame_id: int
    tracks: List[Track]
    num_active_tracks: int


class ObjectTracker:
    """Multi-object tracker using IoU matching."""
    
    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_age: int = 30,
        min_hits: int = 3
    ):
        """
        Initialize object tracker.
        
        Args:
            iou_threshold: Minimum IoU for matching
            max_age: Maximum frames to keep track without detection
            min_hits: Minimum detections before track is confirmed
        """
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        
        self.tracks: Dict[int, Track] = {}
        self.next_track_id = 0
        self.frame_count = 0
        
        logger.info(f"Initialized tracker (IoU={iou_threshold}, max_age={max_age})")
    
    def update(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], str, float]]
    ) -> TrackingResult:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of (bbox, class_name, confidence) tuples
            
        Returns:
            Tracking result
        """
        self.frame_count += 1
        
        # Match detections to existing tracks
        matched_tracks, unmatched_detections = self._match_detections(detections)
        
        # Update matched tracks
        for track_id, (bbox, class_name, confidence) in matched_tracks:
            track = self.tracks[track_id]
            track.bboxes.append(bbox)
            track.frame_ids.append(self.frame_count)
            track.confidences.append(confidence)
            track.is_active = True
        
        # Create new tracks for unmatched detections
        for bbox, class_name, confidence in unmatched_detections:
            track_id = self.next_track_id
            self.next_track_id += 1
            
            track = Track(
                track_id=track_id,
                class_name=class_name,
                bboxes=[bbox],
                frame_ids=[self.frame_count],
                confidences=[confidence],
                is_active=True
            )
            
            self.tracks[track_id] = track
        
        # Mark tracks as inactive if not updated
        for track_id, track in self.tracks.items():
            if track.frame_ids[-1] < self.frame_count:
                # Check if track should be deleted
                age = self.frame_count - track.frame_ids[-1]
                if age > self.max_age:
                    track.is_active = False
        
        # Get active tracks
        active_tracks = [t for t in self.tracks.values() if t.is_active and t.length >= self.min_hits]
        
        return TrackingResult(
            frame_id=self.frame_count,
            tracks=active_tracks,
            num_active_tracks=len(active_tracks)
        )
    
    def _match_detections(
        self,
        detections: List[Tuple[Tuple[int, int, int, int], str, float]]
    ) -> Tuple[List[Tuple[int, Tuple]], List[Tuple]]:
        """
        Match detections to existing tracks using IoU.
        
        Args:
            detections: List of detections
            
        Returns:
            (matched_tracks, unmatched_detections)
        """
        if not self.tracks or not detections:
            return [], detections
        
        # Get active tracks from last frame
        active_tracks = [
            (tid, t) for tid, t in self.tracks.items()
            if t.is_active and (self.frame_count - t.frame_ids[-1]) <= 1
        ]
        
        if not active_tracks:
            return [], detections
        
        # Calculate IoU matrix
        iou_matrix = np.zeros((len(active_tracks), len(detections)))
        
        for i, (track_id, track) in enumerate(active_tracks):
            last_bbox = track.bboxes[-1]
            for j, (det_bbox, _, _) in enumerate(detections):
                iou_matrix[i, j] = self._calculate_iou(last_bbox, det_bbox)
        
        # Match using greedy algorithm
        matched_tracks = []
        matched_det_indices = set()
        
        # Sort by IoU (highest first)
        matches = []
        for i in range(len(active_tracks)):
            for j in range(len(detections)):
                if iou_matrix[i, j] >= self.iou_threshold:
                    matches.append((iou_matrix[i, j], i, j))
        
        matches.sort(reverse=True)
        
        matched_track_indices = set()
        
        for iou, track_idx, det_idx in matches:
            if track_idx not in matched_track_indices and det_idx not in matched_det_indices:
                track_id = active_tracks[track_idx][0]
                matched_tracks.append((track_id, detections[det_idx]))
                matched_track_indices.add(track_idx)
                matched_det_indices.add(det_idx)
        
        # Get unmatched detections
        unmatched_detections = [
            det for i, det in enumerate(detections)
            if i not in matched_det_indices
        ]
        
        return matched_tracks, unmatched_detections
    
    def _calculate_iou(
        self,
        bbox1: Tuple[int, int, int, int],
        bbox2: Tuple[int, int, int, int]
    ) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: First bounding box (x1, y1, x2, y2)
            bbox2: Second bounding box (x1, y1, x2, y2)
            
        Returns:
            IoU value
        """
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def get_track(self, track_id: int) -> Optional[Track]:
        """Get track by ID."""
        return self.tracks.get(track_id)
    
    def get_all_tracks(self) -> List[Track]:
        """Get all tracks."""
        return list(self.tracks.values())
    
    def get_active_tracks(self) -> List[Track]:
        """Get currently active tracks."""
        return [t for t in self.tracks.values() if t.is_active]
    
    def get_confirmed_tracks(self) -> List[Track]:
        """Get confirmed tracks (length >= min_hits)."""
        return [t for t in self.tracks.values() if t.length >= self.min_hits]
    
    def visualize(
        self,
        image: np.ndarray,
        result: TrackingResult,
        show_ids: bool = True,
        show_trails: bool = False
    ) -> np.ndarray:
        """
        Visualize tracking results.
        
        Args:
            image: Input image
            result: Tracking result
            show_ids: Show track IDs
            show_trails: Show track trails
            
        Returns:
            Visualized image
        """
        vis_image = image.copy()
        
        for track in result.tracks:
            if not track.bboxes:
                continue
            
            # Get current bbox
            bbox = track.bboxes[-1]
            x1, y1, x2, y2 = bbox
            
            # Generate color based on track ID
            color = self._get_color(track.track_id)
            
            # Draw bounding box
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw track ID
            if show_ids:
                label = f"ID:{track.track_id} {track.class_name}"
                cv2.putText(
                    vis_image,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )
            
            # Draw trail
            if show_trails and len(track.bboxes) > 1:
                centers = []
                for bbox in track.bboxes[-10:]:  # Last 10 positions
                    cx = (bbox[0] + bbox[2]) // 2
                    cy = (bbox[1] + bbox[3]) // 2
                    centers.append((cx, cy))
                
                for i in range(len(centers) - 1):
                    cv2.line(vis_image, centers[i], centers[i + 1], color, 2)
        
        return vis_image
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracking statistics."""
        all_tracks = self.get_all_tracks()
        active_tracks = self.get_active_tracks()
        confirmed_tracks = self.get_confirmed_tracks()
        
        # Track lengths
        track_lengths = [t.length for t in all_tracks]
        
        # Class distribution
        class_counts = defaultdict(int)
        for track in confirmed_tracks:
            class_counts[track.class_name] += 1
        
        return {
            'total_tracks': len(all_tracks),
            'active_tracks': len(active_tracks),
            'confirmed_tracks': len(confirmed_tracks),
            'avg_track_length': np.mean(track_lengths) if track_lengths else 0,
            'max_track_length': max(track_lengths) if track_lengths else 0,
            'class_distribution': dict(class_counts),
            'current_frame': self.frame_count
        }
    
    def reset(self):
        """Reset tracker state."""
        self.tracks.clear()
        self.next_track_id = 0
        self.frame_count = 0
        logger.info("Tracker reset")
    
    def _get_color(self, track_id: int) -> Tuple[int, int, int]:
        """Get consistent color for track ID."""
        np.random.seed(track_id)
        color = tuple(np.random.randint(0, 255, 3).tolist())
        return color


# Global tracker instance
_tracker: Optional[ObjectTracker] = None


def get_tracker(
    iou_threshold: float = 0.3,
    max_age: int = 30,
    min_hits: int = 3
) -> ObjectTracker:
    """
    Get or create global object tracker instance.
    
    Args:
        iou_threshold: IoU threshold for matching
        max_age: Maximum age for tracks
        min_hits: Minimum hits for confirmation
        
    Returns:
        ObjectTracker instance
    """
    global _tracker
    
    if _tracker is None:
        _tracker = ObjectTracker(
            iou_threshold=iou_threshold,
            max_age=max_age,
            min_hits=min_hits
        )
    
    return _tracker
