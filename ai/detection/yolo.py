"""YOLOv8 object detection service."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("Ultralytics not available. YOLO detection will be disabled.")

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Object detection result."""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    mask: Optional[np.ndarray] = None  # Segmentation mask if available


@dataclass
class DetectionResult:
    """Detection results for an image."""
    image_path: str
    detections: List[Detection]
    num_detections: int
    inference_time: float  # milliseconds


class YOLODetector:
    """YOLOv8 object detector."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "cuda:0"
    ):
        """
        Initialize YOLO detector.
        
        Args:
            model_path: Path to YOLO model weights (uses yolov8n.pt if None)
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on
        """
        if not YOLO_AVAILABLE:
            raise RuntimeError("Ultralytics not installed. Install with: pip install ultralytics")
        
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        # Load model
        if model_path is None:
            # Use default YOLOv8n model (will auto-download)
            model_path = "yolov8n.pt"
            logger.info("Using default YOLOv8n model")
        
        try:
            self.model = YOLO(model_path)
            self.model.to(device)
            logger.info(f"Loaded YOLO model from {model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}")
        
        # Get class names
        self.class_names = self.model.names
    
    def detect(
        self,
        image: np.ndarray,
        image_path: Optional[str] = None
    ) -> DetectionResult:
        """
        Detect objects in an image.
        
        Args:
            image: Input image (BGR format)
            image_path: Optional path for metadata
            
        Returns:
            Detection result
        """
        import time
        start_time = time.time()
        
        # Run inference
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Parse results
        detections = []
        
        if len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            for i in range(len(boxes)):
                box = boxes[i]
                
                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                
                # Get class and confidence
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.class_names[class_id]
                
                # Get mask if available (for instance segmentation)
                mask = None
                if hasattr(result, 'masks') and result.masks is not None:
                    mask = result.masks[i].data.cpu().numpy()
                
                detection = Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2),
                    mask=mask
                )
                
                detections.append(detection)
        
        return DetectionResult(
            image_path=image_path or "unknown",
            detections=detections,
            num_detections=len(detections),
            inference_time=inference_time
        )
    
    def detect_batch(
        self,
        images: List[np.ndarray],
        image_paths: Optional[List[str]] = None
    ) -> List[DetectionResult]:
        """
        Detect objects in multiple images.
        
        Args:
            images: List of input images
            image_paths: Optional list of paths for metadata
            
        Returns:
            List of detection results
        """
        if image_paths is None:
            image_paths = [f"image_{i}" for i in range(len(images))]
        
        results = []
        
        for i, image in enumerate(images):
            result = self.detect(image, image_paths[i])
            results.append(result)
        
        return results
    
    def detect_from_file(self, image_path: str) -> DetectionResult:
        """
        Detect objects from image file.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Detection result
        """
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        return self.detect(image, image_path)
    
    def visualize(
        self,
        image: np.ndarray,
        detections: List[Detection],
        show_labels: bool = True,
        show_confidence: bool = True
    ) -> np.ndarray:
        """
        Visualize detections on image.
        
        Args:
            image: Input image
            detections: List of detections
            show_labels: Show class labels
            show_confidence: Show confidence scores
            
        Returns:
            Image with visualized detections
        """
        vis_image = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            
            # Draw bounding box
            color = self._get_color(det.class_id)
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            if show_labels or show_confidence:
                label_parts = []
                if show_labels:
                    label_parts.append(det.class_name)
                if show_confidence:
                    label_parts.append(f"{det.confidence:.2f}")
                
                label = " ".join(label_parts)
                
                # Draw label background
                (label_w, label_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    vis_image,
                    (x1, y1 - label_h - 10),
                    (x1 + label_w, y1),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    vis_image,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return vis_image
    
    def filter_by_class(
        self,
        detections: List[Detection],
        class_names: List[str]
    ) -> List[Detection]:
        """
        Filter detections by class names.
        
        Args:
            detections: List of detections
            class_names: List of class names to keep
            
        Returns:
            Filtered detections
        """
        return [d for d in detections if d.class_name in class_names]
    
    def filter_by_confidence(
        self,
        detections: List[Detection],
        min_confidence: float
    ) -> List[Detection]:
        """
        Filter detections by confidence threshold.
        
        Args:
            detections: List of detections
            min_confidence: Minimum confidence
            
        Returns:
            Filtered detections
        """
        return [d for d in detections if d.confidence >= min_confidence]
    
    def get_detection_stats(
        self,
        results: List[DetectionResult]
    ) -> Dict[str, Any]:
        """
        Get statistics from detection results.
        
        Args:
            results: List of detection results
            
        Returns:
            Statistics dictionary
        """
        total_detections = sum(r.num_detections for r in results)
        avg_inference_time = np.mean([r.inference_time for r in results])
        
        # Count detections per class
        class_counts = {}
        for result in results:
            for det in result.detections:
                class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
        
        return {
            'total_images': len(results),
            'total_detections': total_detections,
            'avg_detections_per_image': total_detections / len(results) if results else 0,
            'avg_inference_time_ms': avg_inference_time,
            'class_counts': class_counts,
            'unique_classes': len(class_counts)
        }
    
    def _get_color(self, class_id: int) -> Tuple[int, int, int]:
        """Get color for class ID."""
        # Generate consistent color based on class ID
        np.random.seed(class_id)
        color = tuple(np.random.randint(0, 255, 3).tolist())
        return color


# Global detector instance
_detector: Optional[YOLODetector] = None


def get_detector(
    model_path: Optional[str] = None,
    confidence_threshold: float = 0.25,
    device: str = "cuda:0"
) -> YOLODetector:
    """
    Get or create global YOLO detector instance.
    
    Args:
        model_path: Path to model weights
        confidence_threshold: Confidence threshold
        device: Device to use
        
    Returns:
        YOLODetector instance
    """
    global _detector
    
    if _detector is None:
        _detector = YOLODetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            device=device
        )
    
    return _detector
