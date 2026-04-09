"""YOLOv8 object detection service."""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("ultralytics not installed. YOLOv8 detection will not be available.")

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Object detection result."""
    label: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    class_id: int


class YOLODetector:
    """YOLOv8 object detector."""
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = "cuda:0"
    ):
        """
        Initialize YOLO detector.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run inference on ('cuda:0', 'cpu')
        """
        if not YOLO_AVAILABLE:
            raise ImportError("ultralytics package not installed. Install with: pip install ultralytics")
        
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        
        try:
            self.model = YOLO(model_path)
            self.model.to(device)
            logger.info(f"Loaded YOLO model: {model_path} on {device}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def detect(
        self,
        image: np.ndarray,
        confidence_threshold: Optional[float] = None
    ) -> List[Detection]:
        """
        Detect objects in a single image.
        
        Args:
            image: Input image (BGR format)
            confidence_threshold: Override default confidence threshold
            
        Returns:
            List of detections
        """
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        
        try:
            # Run inference
            results = self.model(
                image,
                conf=conf_thresh,
                iou=self.iou_threshold,
                verbose=False
            )
            
            # Parse results
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    # Extract box data
                    box = boxes.xyxy[i].cpu().numpy()  # [x1, y1, x2, y2]
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls = int(boxes.cls[i].cpu().numpy())
                    label = result.names[cls]
                    
                    # Validate bbox
                    if box[2] > box[0] and box[3] > box[1]:
                        detection = Detection(
                            label=label,
                            confidence=conf,
                            bbox=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                            class_id=cls
                        )
                        detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def detect_batch(
        self,
        images: List[np.ndarray],
        confidence_threshold: Optional[float] = None,
        fallback_to_full_scene: bool = True
    ) -> List[List[Detection]]:
        """
        Detect objects in multiple images (batch processing).
        
        Args:
            images: List of input images
            confidence_threshold: Override default confidence threshold
            fallback_to_full_scene: If True, enable full-scene reconstruction when no objects detected
            
        Returns:
            List of detection lists (one per image)
        """
        conf_thresh = confidence_threshold if confidence_threshold is not None else self.confidence_threshold
        
        try:
            # Run batch inference
            results = self.model(
                images,
                conf=conf_thresh,
                iou=self.iou_threshold,
                verbose=False
            )
            
            # Parse results for each image
            all_detections = []
            images_with_no_detections = 0
            
            for idx, result in enumerate(results):
                detections = []
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    box = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls = int(boxes.cls[i].cpu().numpy())
                    label = result.names[cls]
                    
                    if box[2] > box[0] and box[3] > box[1]:
                        detection = Detection(
                            label=label,
                            confidence=conf,
                            bbox=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                            class_id=cls
                        )
                        detections.append(detection)
                
                # Handle edge case: no objects detected
                if len(detections) == 0:
                    images_with_no_detections += 1
                    logger.warning(f"No objects detected in image {idx} with confidence >= {conf_thresh}")
                    
                    if fallback_to_full_scene:
                        logger.info(f"Fallback enabled: Will reconstruct full scene for image {idx}")
                
                all_detections.append(detections)
            
            # Log summary
            total_detections = sum(len(d) for d in all_detections)
            logger.info(f"Batch detection complete: {len(images)} images, {total_detections} total detections")
            
            if images_with_no_detections > 0:
                logger.warning(f"{images_with_no_detections}/{len(images)} images had no detections")
                
                # Suggest lowering threshold if many images have no detections
                if images_with_no_detections > len(images) * 0.5:
                    suggested_threshold = max(0.3, conf_thresh - 0.1)
                    logger.info(f"Consider lowering confidence threshold to {suggested_threshold:.2f}")
            
            return all_detections
            
        except Exception as e:
            logger.error(f"Batch detection failed: {e}")
            return [[] for _ in images]
    
    def validate_detection(self, detection: Detection) -> bool:
        """
        Validate detection parameters.
        
        Args:
            detection: Detection to validate
            
        Returns:
            True if valid
        """
        # Check confidence in [0, 1]
        if not 0.0 <= detection.confidence <= 1.0:
            return False
        
        # Check bbox dimensions are positive
        x1, y1, x2, y2 = detection.bbox
        if x2 <= x1 or y2 <= y1:
            return False
        
        return True
    
    def filter_by_confidence(
        self,
        detections: List[Detection],
        min_confidence: float
    ) -> List[Detection]:
        """Filter detections by confidence threshold."""
        return [d for d in detections if d.confidence >= min_confidence]
    
    def filter_by_labels(
        self,
        detections: List[Detection],
        labels: List[str]
    ) -> List[Detection]:
        """Filter detections by label."""
        return [d for d in detections if d.label in labels]
    
    def get_detection_stats(
        self,
        detections: List[Detection]
    ) -> Dict[str, Any]:
        """Get statistics about detections."""
        if not detections:
            return {
                'num_detections': 0,
                'labels': [],
                'mean_confidence': 0.0
            }
        
        labels = [d.label for d in detections]
        confidences = [d.confidence for d in detections]
        
        return {
            'num_detections': len(detections),
            'labels': list(set(labels)),
            'label_counts': {label: labels.count(label) for label in set(labels)},
            'mean_confidence': float(np.mean(confidences)),
            'min_confidence': float(np.min(confidences)),
            'max_confidence': float(np.max(confidences))
        }


def download_yolo_model(model_name: str = "yolov8n.pt", save_dir: str = "ai/models") -> str:
    """
    Download YOLO model weights.
    
    Args:
        model_name: Model name (yolov8n, yolov8s, yolov8m, yolov8l, yolov8x)
        save_dir: Directory to save model
        
    Returns:
        Path to downloaded model
    """
    from pathlib import Path
    
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    model_path = save_path / model_name
    
    if model_path.exists():
        logger.info(f"Model already exists: {model_path}")
        return str(model_path)
    
    try:
        # YOLO will auto-download if model doesn't exist
        model = YOLO(model_name)
        logger.info(f"Downloaded YOLO model: {model_name}")
        return model_name
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise
