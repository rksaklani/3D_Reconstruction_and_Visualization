"""Reconstruction configuration from environment variables."""

import os
from pathlib import Path
from typing import Optional


class ReconstructionConfig:
    """Configuration for 3D reconstruction pipeline."""
    
    # Gaussian Splatting Repository (required)
    GS_REPO: str = os.getenv('GS_REPO', '/home/rk/aditya/reconstruction/gaussian-splatting')
    
    # Video processing
    DEFAULT_FPS: int = int(os.getenv('DEFAULT_FPS', '2'))
    DEFAULT_JPG_QUALITY: int = int(os.getenv('DEFAULT_JPG_QUALITY', '2'))
    
    # COLMAP configuration
    DEFAULT_MATCHER: str = os.getenv('DEFAULT_MATCHER', 'sequential')
    DEFAULT_OVERLAP: int = int(os.getenv('DEFAULT_OVERLAP', '20'))
    ENABLE_LOOP_DETECTION: bool = os.getenv('ENABLE_LOOP_DETECTION', 'false').lower() == 'true'
    VOCAB_TREE_PATH: str = os.getenv('VOCAB_TREE_PATH', '/path/to/vocab_tree.bin')
    
    # COLMAP paths
    COLMAP_EXECUTABLE: str = os.getenv('COLMAP_EXECUTABLE', '/usr/local/bin/colmap')
    COLMAP_DATABASE: str = os.getenv('COLMAP_DATABASE', 'database.db')
    
    # Gaussian Splatting training
    GS_ITERATIONS: int = int(os.getenv('GS_ITERATIONS', '30000'))
    GS_RESOLUTION: int = int(os.getenv('GS_RESOLUTION', '1'))
    GS_TEST_ITERATIONS: str = os.getenv('GS_TEST_ITERATIONS', '7000,30000')
    
    # Output formats
    EXPORT_FORMATS: str = os.getenv('EXPORT_FORMATS', 'ply,splat,obj,glb')
    
    # Processing limits
    MAX_IMAGES: int = int(os.getenv('MAX_IMAGES', '1000'))
    MAX_VIDEO_DURATION: int = int(os.getenv('MAX_VIDEO_DURATION', '600'))
    MAX_RESOLUTION: int = int(os.getenv('MAX_RESOLUTION', '4096'))
    
    # Temporary workspace (no longer using fixed workspace path)
    TEMP_WORKSPACE: str = os.getenv('TEMP_WORKSPACE', '/tmp/reconstruction_jobs')
    
    @classmethod
    def get_job_config(cls, custom_config: Optional[dict] = None) -> dict:
        """
        Get job configuration with defaults from environment.
        
        Args:
            custom_config: Optional custom configuration to override defaults
            
        Returns:
            Complete job configuration dictionary
        """
        config = {
            'gs_repo': cls.GS_REPO,
            'fps': cls.DEFAULT_FPS,
            'jpg_quality': cls.DEFAULT_JPG_QUALITY,
            'matcher': cls.DEFAULT_MATCHER,
            'overlap': cls.DEFAULT_OVERLAP,
            'loop_detection': cls.ENABLE_LOOP_DETECTION,
            'vocab_tree_path': cls.VOCAB_TREE_PATH,
            'colmap_executable': cls.COLMAP_EXECUTABLE,
            'colmap_database': cls.COLMAP_DATABASE,
            'gs_iterations': cls.GS_ITERATIONS,
            'gs_resolution': cls.GS_RESOLUTION,
            'gs_test_iterations': cls.GS_TEST_ITERATIONS,
            'export_formats': cls.EXPORT_FORMATS.split(','),
            'max_images': cls.MAX_IMAGES,
            'max_video_duration': cls.MAX_VIDEO_DURATION,
            'max_resolution': cls.MAX_RESOLUTION,
        }
        
        # Override with custom config if provided
        if custom_config:
            config.update(custom_config)
        
        return config
    
    @classmethod
    def validate_paths(cls) -> dict:
        """
        Validate that required paths exist.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'gs_repo': Path(cls.GS_REPO).exists(),
            'colmap': Path(cls.COLMAP_EXECUTABLE).exists() if cls.COLMAP_EXECUTABLE != '/usr/local/bin/colmap' else None,
            'vocab_tree': Path(cls.VOCAB_TREE_PATH).exists() if cls.VOCAB_TREE_PATH != '/path/to/vocab_tree.bin' else None,
            'temp_workspace': True,  # Will be created as needed
        }
        return results
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """
        Get a summary of current configuration.
        
        Returns:
            Configuration summary dictionary
        """
        return {
            'gs_repo': cls.GS_REPO,
            'default_fps': cls.DEFAULT_FPS,
            'default_matcher': cls.DEFAULT_MATCHER,
            'colmap_executable': cls.COLMAP_EXECUTABLE,
            'gs_iterations': cls.GS_ITERATIONS,
            'max_images': cls.MAX_IMAGES,
            'export_formats': cls.EXPORT_FORMATS.split(','),
            'temp_workspace': cls.TEMP_WORKSPACE,
        }


# Create singleton instance
recon_config = ReconstructionConfig()
