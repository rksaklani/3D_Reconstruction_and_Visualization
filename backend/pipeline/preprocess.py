"""Input handling and preprocessing for images and videos."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Image metadata."""
    width: int
    height: int
    channels: int
    format: str
    path: str


@dataclass
class VideoMetadata:
    """Video metadata."""
    frame_count: int
    fps: float
    duration: float
    width: int
    height: int
    codec: str
    path: str


@dataclass
class PreprocessConfig:
    """Preprocessing configuration."""
    resize_enabled: bool = False
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    normalize_enabled: bool = True
    denoise_enabled: bool = False
    blur_detection_enabled: bool = True
    blur_threshold: float = 100.0
    exposure_normalization: bool = False


class InputValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ImageLoader:
    """Load and validate images."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
    
    def __init__(self, min_images: int = 3):
        """
        Initialize image loader.
        
        Args:
            min_images: Minimum number of images required
        """
        self.min_images = min_images
    
    def load_images(self, image_paths: List[str]) -> List[Tuple[np.ndarray, ImageMetadata]]:
        """
        Load images from file paths.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of (image, metadata) tuples
            
        Raises:
            InputValidationError: If validation fails
        """
        # Validate input
        if len(image_paths) < self.min_images:
            raise InputValidationError(
                f"Insufficient images: got {len(image_paths)}, need at least {self.min_images}"
            )
        
        images = []
        
        for path_str in image_paths:
            path = Path(path_str)
            
            # Validate file exists
            if not path.exists():
                logger.warning(f"Image not found: {path}")
                continue
            
            # Validate format
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                logger.warning(f"Unsupported format: {path.suffix}")
                continue
            
            try:
                # Load image
                image = cv2.imread(str(path))
                
                if image is None:
                    logger.warning(f"Failed to load image: {path}")
                    continue
                
                # Extract metadata
                metadata = ImageMetadata(
                    width=image.shape[1],
                    height=image.shape[0],
                    channels=image.shape[2] if len(image.shape) == 3 else 1,
                    format=path.suffix.lower(),
                    path=str(path)
                )
                
                images.append((image, metadata))
                
            except Exception as e:
                logger.error(f"Error loading image {path}: {e}")
                continue
        
        # Final validation
        if len(images) < self.min_images:
            raise InputValidationError(
                f"Successfully loaded {len(images)} images, need at least {self.min_images}"
            )
        
        logger.info(f"Loaded {len(images)} images")
        return images
    
    def validate_image(self, image: np.ndarray) -> bool:
        """
        Validate image data.
        
        Args:
            image: Image array
            
        Returns:
            True if valid
        """
        if image is None or image.size == 0:
            return False
        
        if len(image.shape) not in [2, 3]:
            return False
        
        if image.shape[0] < 100 or image.shape[1] < 100:
            logger.warning("Image too small")
            return False
        
        return True


class VideoDecoder:
    """Decode video and extract frames."""
    
    SUPPORTED_CODECS = {'h264', 'h265', 'hevc', 'vp9', 'vp8', 'mpeg4'}
    
    def __init__(self, sampling_rate: int = 1):
        """
        Initialize video decoder.
        
        Args:
            sampling_rate: Extract every Nth frame (1 = all frames)
        """
        self.sampling_rate = sampling_rate
    
    def load_video(self, video_path: str) -> VideoMetadata:
        """
        Load video and extract metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Video metadata
            
        Raises:
            InputValidationError: If video cannot be loaded
        """
        path = Path(video_path)
        
        if not path.exists():
            raise InputValidationError(f"Video not found: {path}")
        
        try:
            cap = cv2.VideoCapture(str(path))
            
            if not cap.isOpened():
                raise InputValidationError(f"Failed to open video: {path}")
            
            # Extract metadata
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            # Decode codec
            codec = self._decode_fourcc(fourcc)
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            metadata = VideoMetadata(
                frame_count=frame_count,
                fps=fps,
                duration=duration,
                width=width,
                height=height,
                codec=codec,
                path=str(path)
            )
            
            logger.info(f"Video metadata: {metadata}")
            return metadata
            
        except Exception as e:
            raise InputValidationError(f"Failed to load video: {e}")
    
    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None
    ) -> List[Tuple[np.ndarray, int]]:
        """
        Extract frames from video.
        
        Args:
            video_path: Path to video file
            output_dir: Optional directory to save frames
            
        Returns:
            List of (frame, frame_number) tuples
            
        Raises:
            InputValidationError: If extraction fails
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise InputValidationError(f"Failed to open video: {video_path}")
            
            frames = []
            frame_idx = 0
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Sample frames
                if frame_idx % self.sampling_rate == 0:
                    frames.append((frame, frame_idx))
                    
                    # Optionally save frame
                    if output_dir:
                        output_path = Path(output_dir) / f"frame_{frame_idx:06d}.jpg"
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        cv2.imwrite(str(output_path), frame)
                
                frame_idx += 1
            
            cap.release()
            
            logger.info(f"Extracted {len(frames)} frames from video")
            return frames
            
        except Exception as e:
            raise InputValidationError(f"Failed to extract frames: {e}")
    
    def _decode_fourcc(self, fourcc: int) -> str:
        """Decode FourCC code to codec name."""
        try:
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return codec.lower()
        except:
            return "unknown"


class ImagePreprocessor:
    """Preprocess images for reconstruction."""
    
    def __init__(self, config: Optional[PreprocessConfig] = None):
        """
        Initialize preprocessor.
        
        Args:
            config: Preprocessing configuration
        """
        self.config = config or PreprocessConfig()
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        processed = image.copy()
        
        # Resize
        if self.config.resize_enabled:
            processed = self._resize(processed)
        
        # Denoise
        if self.config.denoise_enabled:
            processed = self._denoise(processed)
        
        # Normalize exposure
        if self.config.exposure_normalization:
            processed = self._normalize_exposure(processed)
        
        # Normalize
        if self.config.normalize_enabled:
            processed = self._normalize(processed)
        
        return processed
    
    def detect_blur(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Detect if image is blurry using Laplacian variance.
        
        Args:
            image: Input image
            
        Returns:
            (is_blurry, variance) tuple
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Compute Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        is_blurry = variance < self.config.blur_threshold
        
        return is_blurry, variance
    
    def filter_blurry_images(
        self,
        images: List[Tuple[np.ndarray, ImageMetadata]]
    ) -> List[Tuple[np.ndarray, ImageMetadata]]:
        """
        Filter out blurry images.
        
        Args:
            images: List of (image, metadata) tuples
            
        Returns:
            Filtered list
        """
        if not self.config.blur_detection_enabled:
            return images
        
        filtered = []
        
        for image, metadata in images:
            is_blurry, variance = self.detect_blur(image)
            
            if not is_blurry:
                filtered.append((image, metadata))
            else:
                logger.warning(
                    f"Filtered blurry image: {metadata.path} (variance={variance:.2f})"
                )
        
        logger.info(f"Filtered {len(images) - len(filtered)} blurry images")
        return filtered
    
    def _resize(self, image: np.ndarray) -> np.ndarray:
        """Resize image."""
        if self.config.resize_width and self.config.resize_height:
            return cv2.resize(
                image,
                (self.config.resize_width, self.config.resize_height),
                interpolation=cv2.INTER_LANCZOS4
            )
        return image
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Denoise image using Non-local Means."""
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    def _normalize_exposure(self, image: np.ndarray) -> np.ndarray:
        """Normalize image exposure using CLAHE."""
        if len(image.shape) == 3:
            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(image)
    
    def _normalize(self, image: np.ndarray) -> np.ndarray:
        """Normalize image to [0, 1] range."""
        return image.astype(np.float32) / 255.0
