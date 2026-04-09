"""Segment Anything Model (SAM) segmentation service."""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

try:
    from segment_anything import sam_model_registry, SamPredictor
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False
    logging.warning("segment-anything not installed. SAM segmentation will not be available.")

logger = logging.getLogger(__name__)


@dataclass
class SegmentationMask:
    """Segmentation mask result."""
    mask: np.ndarray  # Binary mask (H, W)
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    area: int


class SAMSegmenter:
    """Segment Anything Model segmenter."""
    
    def __init__(
        self,
        model_type: str = "vit_h",
        checkpoint_path: str = "sam_vit_h_4b8939.pth",
        device: str = "cuda:0"
    ):
        """
        Initialize SAM segmenter.
        
        Args:
            model_type: SAM model type ('vit_h', 'vit_l', 'vit_b')
            checkpoint_path: Path to SAM checkpoint
            device: Device to run inference on
        """
        if not SAM_AVAILABLE:
            raise ImportError(
                "segment-anything package not installed. "
                "Install with: pip install git+https://github.com/facebookresearch/segment-anything.git"
            )
        
        self.device = device
        self.model_type = model_type
        
        try:
            sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
            sam.to(device=device)
            self.predictor = SamPredictor(sam)
            logger.info(f"Loaded SAM model: {model_type} on {device}")
        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            raise
    
    def segment_from_bbox(
        self,
        image: np.ndarray,
        bbox: Tuple[float, float, float, float],
        fallback_to_bbox: bool = True
    ) -> Optional[SegmentationMask]:
        """
        Segment object using bounding box prompt.
        
        Args:
            image: Input image (RGB format, H x W x 3)
            bbox: Bounding box (x1, y1, x2, y2)
            fallback_to_bbox: If True, return bbox mask if segmentation fails
            
        Returns:
            Segmentation mask or None if failed
        """
        try:
            # Set image for predictor
            self.predictor.set_image(image)
            
            # Convert bbox to SAM format
            x1, y1, x2, y2 = bbox
            input_box = np.array([x1, y1, x2, y2])
            
            # Run segmentation
            masks, scores, logits = self.predictor.predict(
                point_coords=None,
                point_labels=None,
                box=input_box[None, :],
                multimask_output=False
            )
            
            # Get best mask
            mask = masks[0]  # (H, W)
            confidence = float(scores[0])
            
            # Validate mask dimensions
            if mask.shape[:2] != image.shape[:2]:
                logger.error(
                    f"Mask dimensions {mask.shape[:2]} don't match image {image.shape[:2]}"
                )
                if fallback_to_bbox:
                    return self._create_bbox_mask(image.shape[:2], bbox)
                return None
            
            # Calculate mask area
            area = int(np.sum(mask))
            
            if area == 0:
                logger.warning("Segmentation produced empty mask")
                if fallback_to_bbox:
                    return self._create_bbox_mask(image.shape[:2], bbox)
                return None
            
            return SegmentationMask(
                mask=mask.astype(np.uint8),
                bbox=bbox,
                confidence=confidence,
                area=area
            )
            
        except Exception as e:
            logger.error(f"Segmentation failed: {e}")
            if fallback_to_bbox:
                logger.info("Falling back to bounding box mask")
                return self._create_bbox_mask(image.shape[:2], bbox)
            return None
    
    def segment_batch_from_bboxes(
        self,
        image: np.ndarray,
        bboxes: List[Tuple[float, float, float, float]],
        fallback_to_bbox: bool = True
    ) -> List[Optional[SegmentationMask]]:
        """
        Segment multiple objects in single image using bbox prompts.
        
        Args:
            image: Input image (RGB format)
            bboxes: List of bounding boxes
            fallback_to_bbox: If True, return bbox mask if segmentation fails
            
        Returns:
            List of segmentation masks
        """
        masks = []
        
        # Set image once for all predictions
        try:
            self.predictor.set_image(image)
        except Exception as e:
            logger.error(f"Failed to set image: {e}")
            if fallback_to_bbox:
                return [self._create_bbox_mask(image.shape[:2], bbox) for bbox in bboxes]
            return [None] * len(bboxes)
        
        # Segment each bbox
        for bbox in bboxes:
            try:
                x1, y1, x2, y2 = bbox
                input_box = np.array([x1, y1, x2, y2])
                
                masks_pred, scores, logits = self.predictor.predict(
                    point_coords=None,
                    point_labels=None,
                    box=input_box[None, :],
                    multimask_output=False
                )
                
                mask = masks_pred[0]
                confidence = float(scores[0])
                
                # Validate dimensions
                if mask.shape[:2] != image.shape[:2]:
                    logger.error(f"Mask dimensions mismatch for bbox {bbox}")
                    if fallback_to_bbox:
                        masks.append(self._create_bbox_mask(image.shape[:2], bbox))
                    else:
                        masks.append(None)
                    continue
                
                area = int(np.sum(mask))
                
                if area == 0:
                    logger.warning(f"Empty mask for bbox {bbox}")
                    if fallback_to_bbox:
                        masks.append(self._create_bbox_mask(image.shape[:2], bbox))
                    else:
                        masks.append(None)
                    continue
                
                masks.append(SegmentationMask(
                    mask=mask.astype(np.uint8),
                    bbox=bbox,
                    confidence=confidence,
                    area=area
                ))
                
            except Exception as e:
                logger.error(f"Segmentation failed for bbox {bbox}: {e}")
                if fallback_to_bbox:
                    masks.append(self._create_bbox_mask(image.shape[:2], bbox))
                else:
                    masks.append(None)
        
        logger.info(f"Segmented {len(masks)} objects, "
                   f"{sum(1 for m in masks if m is not None)} successful")
        
        return masks
    
    def _create_bbox_mask(
        self,
        image_shape: Tuple[int, int],
        bbox: Tuple[float, float, float, float]
    ) -> SegmentationMask:
        """
        Create binary mask from bounding box (fallback).
        
        Args:
            image_shape: Image dimensions (H, W)
            bbox: Bounding box (x1, y1, x2, y2)
            
        Returns:
            Segmentation mask covering bbox region
        """
        h, w = image_shape
        mask = np.zeros((h, w), dtype=np.uint8)
        
        x1, y1, x2, y2 = bbox
        x1, y1 = int(max(0, x1)), int(max(0, y1))
        x2, y2 = int(min(w, x2)), int(min(h, y2))
        
        mask[y1:y2, x1:x2] = 1
        area = int(np.sum(mask))
        
        return SegmentationMask(
            mask=mask,
            bbox=bbox,
            confidence=1.0,  # Bbox mask has perfect confidence
            area=area
        )
    
    def validate_mask(
        self,
        mask: SegmentationMask,
        image_shape: Tuple[int, int]
    ) -> bool:
        """
        Validate segmentation mask.
        
        Args:
            mask: Segmentation mask to validate
            image_shape: Expected image dimensions (H, W)
            
        Returns:
            True if valid
        """
        # Check mask dimensions match image
        if mask.mask.shape != image_shape:
            logger.error(
                f"Mask dimensions {mask.mask.shape} don't match image {image_shape}"
            )
            return False
        
        # Check mask is binary
        unique_values = np.unique(mask.mask)
        if not np.all(np.isin(unique_values, [0, 1])):
            logger.error(f"Mask contains non-binary values: {unique_values}")
            return False
        
        # Check area matches mask sum
        if mask.area != np.sum(mask.mask):
            logger.error(f"Mask area {mask.area} doesn't match sum {np.sum(mask.mask)}")
            return False
        
        # Check confidence in valid range
        if not 0.0 <= mask.confidence <= 1.0:
            logger.error(f"Invalid confidence: {mask.confidence}")
            return False
        
        return True
    
    def get_mask_stats(self, mask: SegmentationMask) -> dict:
        """Get statistics about segmentation mask."""
        return {
            'area': mask.area,
            'confidence': mask.confidence,
            'bbox': mask.bbox,
            'bbox_area': (mask.bbox[2] - mask.bbox[0]) * (mask.bbox[3] - mask.bbox[1]),
            'coverage_ratio': mask.area / ((mask.bbox[2] - mask.bbox[0]) * (mask.bbox[3] - mask.bbox[1]))
        }


def download_sam_model(
    model_type: str = "vit_h",
    save_dir: str = "ai/models"
) -> str:
    """
    Download SAM model checkpoint.
    
    Args:
        model_type: Model type ('vit_h', 'vit_l', 'vit_b')
        save_dir: Directory to save model
        
    Returns:
        Path to downloaded checkpoint
    """
    from pathlib import Path
    import urllib.request
    
    model_urls = {
        'vit_h': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth',
        'vit_l': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth',
        'vit_b': 'https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth'
    }
    
    if model_type not in model_urls:
        raise ValueError(f"Invalid model type: {model_type}")
    
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    filename = model_urls[model_type].split('/')[-1]
    checkpoint_path = save_path / filename
    
    if checkpoint_path.exists():
        logger.info(f"Model already exists: {checkpoint_path}")
        return str(checkpoint_path)
    
    try:
        logger.info(f"Downloading SAM model: {model_type}")
        urllib.request.urlretrieve(model_urls[model_type], checkpoint_path)
        logger.info(f"Downloaded to: {checkpoint_path}")
        return str(checkpoint_path)
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise
