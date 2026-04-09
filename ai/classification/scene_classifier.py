"""Scene classification using CLIP or simple CNN."""

import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# CLIP is not compatible with Python 3.13 yet
CLIP_AVAILABLE = False


@dataclass
class SceneClassification:
    """Scene classification result."""
    scene_type: str
    confidence: float
    top_k_predictions: List[Tuple[str, float]]


class SceneClassifier:
    """Scene classifier for 3D reconstruction context."""
    
    # Common scene types for 3D reconstruction
    SCENE_TYPES = [
        "indoor",
        "outdoor",
        "urban",
        "natural",
        "object",
        "room",
        "building",
        "landscape"
    ]
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        device: str = "cuda:0"
    ):
        """
        Initialize scene classifier.
        
        Args:
            model_path: Path to model weights
            device: Device to run inference on
        """
        self.device = device
        
        if CLIP_AVAILABLE:
            # TODO: Use CLIP when available
            # import clip
            # self.model, self.preprocess = clip.load("ViT-B/32", device=device)
            logger.info("CLIP not available, using fallback classifier")
            self.model = self._create_fallback_model()
        else:
            logger.info("Using fallback scene classifier")
            self.model = self._create_fallback_model()
    
    def classify(
        self,
        image: np.ndarray,
        top_k: int = 3
    ) -> SceneClassification:
        """
        Classify scene type.
        
        Args:
            image: Input image (BGR format)
            top_k: Number of top predictions to return
            
        Returns:
            Scene classification result
        """
        if CLIP_AVAILABLE:
            return self._classify_with_clip(image, top_k)
        else:
            return self._classify_fallback(image, top_k)
    
    def classify_batch(
        self,
        images: List[np.ndarray],
        top_k: int = 3
    ) -> List[SceneClassification]:
        """
        Classify multiple images.
        
        Args:
            images: List of input images
            top_k: Number of top predictions
            
        Returns:
            List of classification results
        """
        return [self.classify(img, top_k) for img in images]
    
    def classify_from_file(
        self,
        image_path: str,
        top_k: int = 3
    ) -> SceneClassification:
        """
        Classify scene from image file.
        
        Args:
            image_path: Path to image file
            top_k: Number of top predictions
            
        Returns:
            Scene classification result
        """
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        return self.classify(image, top_k)
    
    def _classify_with_clip(
        self,
        image: np.ndarray,
        top_k: int
    ) -> SceneClassification:
        """Classify using CLIP (when available)."""
        # TODO: Implement CLIP classification
        # Convert image to RGB
        # image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # image_pil = Image.fromarray(image_rgb)
        # image_input = self.preprocess(image_pil).unsqueeze(0).to(self.device)
        # 
        # # Create text prompts
        # text_inputs = torch.cat([clip.tokenize(f"a photo of a {c}") for c in self.SCENE_TYPES]).to(self.device)
        # 
        # # Get predictions
        # with torch.no_grad():
        #     image_features = self.model.encode_image(image_input)
        #     text_features = self.model.encode_text(text_inputs)
        #     
        #     # Calculate similarity
        #     similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        #     values, indices = similarity[0].topk(top_k)
        
        return self._classify_fallback(image, top_k)
    
    def _classify_fallback(
        self,
        image: np.ndarray,
        top_k: int
    ) -> SceneClassification:
        """
        Fallback classification using simple heuristics.
        
        Args:
            image: Input image
            top_k: Number of top predictions
            
        Returns:
            Scene classification
        """
        # Simple heuristics based on image statistics
        
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate features
        brightness = np.mean(hsv[:, :, 2])
        saturation = np.mean(hsv[:, :, 1])
        
        # Edge density (complexity)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Color variance
        color_variance = np.var(image)
        
        # Simple rules
        scores = {}
        
        # Indoor scenes tend to have lower saturation and moderate brightness
        scores['indoor'] = 0.5 + (1 - saturation / 255) * 0.3 + (brightness / 255) * 0.2
        
        # Outdoor scenes tend to have higher saturation
        scores['outdoor'] = 0.5 + (saturation / 255) * 0.5
        
        # Urban scenes have high edge density
        scores['urban'] = 0.5 + edge_density * 0.5
        
        # Natural scenes have high color variance
        scores['natural'] = 0.5 + min(color_variance / 10000, 1.0) * 0.5
        
        # Object scenes have lower edge density
        scores['object'] = 0.5 + (1 - edge_density) * 0.5
        
        # Room is similar to indoor
        scores['room'] = scores['indoor'] * 0.9
        
        # Building is similar to urban
        scores['building'] = scores['urban'] * 0.9
        
        # Landscape is similar to natural
        scores['landscape'] = scores['natural'] * 0.9
        
        # Normalize scores
        total = sum(scores.values())
        scores = {k: v / total for k, v in scores.items()}
        
        # Get top k
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_k_predictions = sorted_scores[:top_k]
        
        scene_type, confidence = top_k_predictions[0]
        
        return SceneClassification(
            scene_type=scene_type,
            confidence=confidence,
            top_k_predictions=top_k_predictions
        )
    
    def _create_fallback_model(self):
        """Create a simple fallback model."""
        # Placeholder - returns None since we use heuristics
        return None
    
    def get_scene_statistics(
        self,
        classifications: List[SceneClassification]
    ) -> Dict[str, Any]:
        """
        Get statistics from classification results.
        
        Args:
            classifications: List of classification results
            
        Returns:
            Statistics dictionary
        """
        scene_counts = {}
        avg_confidence = []
        
        for cls in classifications:
            scene_counts[cls.scene_type] = scene_counts.get(cls.scene_type, 0) + 1
            avg_confidence.append(cls.confidence)
        
        # Determine dominant scene type
        dominant_scene = max(scene_counts.items(), key=lambda x: x[1])[0] if scene_counts else "unknown"
        
        return {
            'total_images': len(classifications),
            'scene_counts': scene_counts,
            'dominant_scene': dominant_scene,
            'avg_confidence': np.mean(avg_confidence) if avg_confidence else 0.0,
            'unique_scenes': len(scene_counts)
        }


# Global classifier instance
_classifier: Optional[SceneClassifier] = None


def get_classifier(
    model_path: Optional[str] = None,
    device: str = "cuda:0"
) -> SceneClassifier:
    """
    Get or create global scene classifier instance.
    
    Args:
        model_path: Path to model weights
        device: Device to use
        
    Returns:
        SceneClassifier instance
    """
    global _classifier
    
    if _classifier is None:
        _classifier = SceneClassifier(
            model_path=model_path,
            device=device
        )
    
    return _classifier
