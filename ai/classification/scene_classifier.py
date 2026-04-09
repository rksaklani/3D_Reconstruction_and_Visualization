"""CLIP-based scene classification service."""

import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
import logging

try:
    import torch
    import clip
    from PIL import Image
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logging.warning("CLIP not installed. Scene classification will not be available.")

logger = logging.getLogger(__name__)


@dataclass
class SceneClassification:
    """Scene classification result."""
    scene_type: str  # 'indoor', 'outdoor', 'mixed'
    scene_type_confidence: float
    room_type: str  # 'living_room', 'bedroom', 'kitchen', 'office', 'other', 'n/a'
    room_type_confidence: float
    all_scores: Dict[str, float]


class SceneClassifier:
    """CLIP-based scene classifier."""
    
    # Scene type categories
    SCENE_TYPES = ['indoor', 'outdoor', 'mixed indoor and outdoor']
    
    # Room type categories (for indoor scenes)
    ROOM_TYPES = [
        'living room',
        'bedroom',
        'kitchen',
        'office',
        'bathroom',
        'dining room',
        'hallway',
        'other room'
    ]
    
    def __init__(
        self,
        model_name: str = "ViT-B/32",
        device: str = "cuda:0"
    ):
        """
        Initialize CLIP scene classifier.
        
        Args:
            model_name: CLIP model name ('ViT-B/32', 'ViT-B/16', 'ViT-L/14')
            device: Device to run inference on
        """
        if not CLIP_AVAILABLE:
            raise ImportError(
                "CLIP not installed. "
                "Install with: pip install git+https://github.com/openai/CLIP.git"
            )
        
        self.device = device
        
        try:
            self.model, self.preprocess = clip.load(model_name, device=device)
            logger.info(f"Loaded CLIP model: {model_name} on {device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
        
        # Precompute text embeddings for scene types
        self.scene_type_embeddings = self._encode_text(
            [f"a photo of {scene}" for scene in self.SCENE_TYPES]
        )
        
        # Precompute text embeddings for room types
        self.room_type_embeddings = self._encode_text(
            [f"a photo of a {room}" for room in self.ROOM_TYPES]
        )
    
    def _encode_text(self, texts: List[str]) -> torch.Tensor:
        """Encode text prompts to embeddings."""
        with torch.no_grad():
            text_tokens = clip.tokenize(texts).to(self.device)
            text_features = self.model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features
    
    def _encode_image(self, image: np.ndarray) -> torch.Tensor:
        """
        Encode image to embedding.
        
        Args:
            image: Input image (RGB format, H x W x 3)
            
        Returns:
            Image embedding tensor
        """
        # Convert numpy to PIL
        pil_image = Image.fromarray(image.astype(np.uint8))
        
        # Preprocess and encode
        with torch.no_grad():
            image_input = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        
        return image_features
    
    def classify(self, image: np.ndarray) -> SceneClassification:
        """
        Classify scene type and room type.
        
        Args:
            image: Input image (RGB format)
            
        Returns:
            Scene classification result
        """
        try:
            # Encode image
            image_features = self._encode_image(image)
            
            # Compute similarities for scene types
            scene_similarities = (image_features @ self.scene_type_embeddings.T).squeeze(0)
            scene_probs = torch.softmax(scene_similarities * 100, dim=0).cpu().numpy()
            
            # Get best scene type
            scene_idx = int(np.argmax(scene_probs))
            scene_type = self.SCENE_TYPES[scene_idx]
            scene_confidence = float(scene_probs[scene_idx])
            
            # Map to simplified scene type
            if 'indoor' in scene_type and 'outdoor' not in scene_type:
                simplified_scene = 'indoor'
            elif 'outdoor' in scene_type and 'indoor' not in scene_type:
                simplified_scene = 'outdoor'
            else:
                simplified_scene = 'mixed'
            
            # Classify room type if indoor
            room_type = 'n/a'
            room_confidence = 0.0
            
            if simplified_scene == 'indoor':
                room_similarities = (image_features @ self.room_type_embeddings.T).squeeze(0)
                room_probs = torch.softmax(room_similarities * 100, dim=0).cpu().numpy()
                
                room_idx = int(np.argmax(room_probs))
                room_type = self.ROOM_TYPES[room_idx].replace(' ', '_')
                room_confidence = float(room_probs[room_idx])
            
            # Collect all scores
            all_scores = {
                'scene_types': {
                    self.SCENE_TYPES[i]: float(scene_probs[i])
                    for i in range(len(self.SCENE_TYPES))
                }
            }
            
            if simplified_scene == 'indoor':
                all_scores['room_types'] = {
                    self.ROOM_TYPES[i].replace(' ', '_'): float(room_probs[i])
                    for i in range(len(self.ROOM_TYPES))
                }
            
            logger.debug(
                f"Scene: {simplified_scene} ({scene_confidence:.3f}), "
                f"Room: {room_type} ({room_confidence:.3f})"
            )
            
            return SceneClassification(
                scene_type=simplified_scene,
                scene_type_confidence=scene_confidence,
                room_type=room_type,
                room_type_confidence=room_confidence,
                all_scores=all_scores
            )
            
        except Exception as e:
            logger.error(f"Scene classification failed: {e}")
            # Return default classification
            return SceneClassification(
                scene_type='unknown',
                scene_type_confidence=0.0,
                room_type='n/a',
                room_type_confidence=0.0,
                all_scores={}
            )
    
    def classify_batch(self, images: List[np.ndarray]) -> List[SceneClassification]:
        """
        Classify multiple images.
        
        Args:
            images: List of input images
            
        Returns:
            List of scene classifications
        """
        classifications = []
        
        for image in images:
            classification = self.classify(image)
            classifications.append(classification)
        
        logger.info(f"Classified {len(images)} scenes")
        
        return classifications
    
    def classify_with_custom_labels(
        self,
        image: np.ndarray,
        labels: List[str]
    ) -> Dict[str, float]:
        """
        Classify image with custom text labels.
        
        Args:
            image: Input image
            labels: List of text labels to classify against
            
        Returns:
            Dictionary mapping labels to confidence scores
        """
        try:
            # Encode image
            image_features = self._encode_image(image)
            
            # Encode custom labels
            label_embeddings = self._encode_text(
                [f"a photo of {label}" for label in labels]
            )
            
            # Compute similarities
            similarities = (image_features @ label_embeddings.T).squeeze(0)
            probs = torch.softmax(similarities * 100, dim=0).cpu().numpy()
            
            return {
                labels[i]: float(probs[i])
                for i in range(len(labels))
            }
            
        except Exception as e:
            logger.error(f"Custom classification failed: {e}")
            return {label: 0.0 for label in labels}
    
    def get_scene_stats(
        self,
        classifications: List[SceneClassification]
    ) -> Dict:
        """Get statistics about scene classifications."""
        if not classifications:
            return {
                'num_scenes': 0,
                'scene_types': {},
                'room_types': {}
            }
        
        scene_types = [c.scene_type for c in classifications]
        room_types = [c.room_type for c in classifications if c.room_type != 'n/a']
        
        return {
            'num_scenes': len(classifications),
            'scene_types': {
                st: scene_types.count(st) for st in set(scene_types)
            },
            'room_types': {
                rt: room_types.count(rt) for rt in set(room_types)
            } if room_types else {},
            'avg_scene_confidence': np.mean([c.scene_type_confidence for c in classifications]),
            'avg_room_confidence': np.mean([
                c.room_type_confidence for c in classifications
                if c.room_type != 'n/a'
            ]) if room_types else 0.0
        }


def download_clip_model(model_name: str = "ViT-B/32") -> str:
    """
    Download CLIP model.
    
    Args:
        model_name: Model name to download
        
    Returns:
        Model name (CLIP handles download automatically)
    """
    try:
        logger.info(f"Downloading CLIP model: {model_name}")
        clip.load(model_name, device="cpu")
        logger.info(f"Downloaded CLIP model: {model_name}")
        return model_name
    except Exception as e:
        logger.error(f"Failed to download CLIP model: {e}")
        raise
