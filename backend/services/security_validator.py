"""
Security and validation service for the 3D reconstruction pipeline.
Implements input validation, resource limits, and security checks.
"""

import os
import magic
from pathlib import Path
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_IMAGE_COUNT = 1000
MAX_IMAGE_RESOLUTION = 8192 * 8192  # 8K resolution
OPERATION_TIMEOUT = 3600  # 1 hour


class SecurityValidator:
    """Validates inputs and enforces security policies."""
    
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def validate_file_extension(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file extension against whitelist (Requirement 21.1).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        ext = Path(filename).suffix.lower()
        
        if ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS:
            return True, None
        
        return False, f"File extension '{ext}' is not allowed. Allowed: {ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS}"
    
    def validate_file_size(self, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file size against maximum limit (Requirement 21.2).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size > MAX_FILE_SIZE:
            return False, f"File size {file_size} bytes exceeds maximum {MAX_FILE_SIZE} bytes"
        
        return True, None
    
    def validate_file_header(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Verify file header to prevent malicious files (Requirement 21.3).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            mime_type = self.mime.from_file(file_path)
            
            valid_mime_types = {
                'image/jpeg', 'image/png', 'image/tiff',
                'video/mp4', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'
            }
            
            if mime_type not in valid_mime_types:
                return False, f"Invalid file type: {mime_type}"
            
            return True, None
        except Exception as e:
            logger.error(f"Error validating file header: {e}")
            return False, f"Failed to validate file: {str(e)}"
    
    def sanitize_path(self, path: str, base_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Sanitize file path to prevent directory traversal (Requirement 21.6).
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        try:
            # Resolve absolute paths
            abs_path = Path(path).resolve()
            abs_base = Path(base_dir).resolve()
            
            # Check if path is within base directory
            if not str(abs_path).startswith(str(abs_base)):
                return False, "Path traversal detected"
            
            return True, None
        except Exception as e:
            logger.error(f"Error sanitizing path: {e}")
            return False, f"Invalid path: {str(e)}"
    
    def validate_image_count(self, count: int) -> Tuple[bool, Optional[str]]:
        """
        Validate image count against limits (Requirement 21.4).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if count < 3:
            return False, "At least 3 images are required"
        
        if count > MAX_IMAGE_COUNT:
            return False, f"Image count {count} exceeds maximum {MAX_IMAGE_COUNT}"
        
        return True, None
    
    def validate_image_resolution(self, width: int, height: int) -> Tuple[bool, Optional[str]]:
        """
        Validate image resolution against limits (Requirement 21.5).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        total_pixels = width * height
        
        if total_pixels > MAX_IMAGE_RESOLUTION:
            return False, f"Image resolution {width}x{height} exceeds maximum {MAX_IMAGE_RESOLUTION} pixels"
        
        return True, None
    
    def validate_upload(
        self,
        filename: str,
        file_size: int,
        file_path: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform complete upload validation.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate extension
        valid, error = self.validate_file_extension(filename)
        if not valid:
            return False, error
        
        # Validate size
        valid, error = self.validate_file_size(file_size)
        if not valid:
            return False, error
        
        # Validate file header
        valid, error = self.validate_file_header(file_path)
        if not valid:
            return False, error
        
        return True, None


# Global validator instance
security_validator = SecurityValidator()
