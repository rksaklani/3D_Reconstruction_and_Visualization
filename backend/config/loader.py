"""Configuration loader for YAML files with validation and merging."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ConfigPaths:
    """Default configuration file paths."""
    pipeline: str = "configs/pipeline.yaml"
    model: str = "configs/model.yaml"
    colmap: str = "configs/colmap.yaml"
    gaussian: str = "configs/gaussian.yaml"
    physics: str = "configs/physics.yaml"
    minio: str = "configs/minio.yaml"


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigLoader:
    """Load and validate YAML configuration files."""
    
    def __init__(self, config_dir: str = "configs", project_root: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
            project_root: Project root directory (defaults to current working directory)
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_dir = self.project_root / config_dir
        self.configs: Dict[str, Dict[str, Any]] = {}
        self._defaults = self._load_defaults()
    
    def _load_defaults(self) -> Dict[str, Dict[str, Any]]:
        """Load default configurations."""
        return {
            'pipeline': {
                'preprocessing': {
                    'resize': {'enabled': False},
                    'normalize': {'enabled': True},
                    'denoise': {'enabled': False}
                },
                'sfm': {
                    'feature_extraction': {'max_features': 8192},
                    'feature_matching': {'max_ratio': 0.8}
                }
            },
            'model': {
                'yolov8': {'confidence_threshold': 0.5},
                'sam': {'model_type': 'vit_b'},
                'clip': {'model_name': 'ViT-B/32'}
            },
            'colmap': {
                'feature_extraction': {'max_num_features': 8192},
                'mapper': {'min_num_matches': 15}
            },
            'gaussian': {
                'training': {'iterations': 30000},
                'rendering': {'image_height': 1080, 'image_width': 1920}
            },
            'physics': {
                'engine': {'gravity': [0.0, -9.81, 0.0], 'time_step': 0.016667},
                'rigid_bodies': {'default_mass': 1.0, 'default_friction': 0.5}
            },
            'minio': {
                'endpoint': 'localhost:9000',
                'access_key': 'minioadmin',
                'secret_key': 'minioadmin',
                'secure': False
            }
        }
    
    def load(self, config_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            config_name: Name of the configuration (e.g., 'pipeline', 'model')
            config_path: Optional custom path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ConfigValidationError: If configuration is invalid
        """
        if config_path:
            file_path = Path(config_path)
        else:
            file_path = self.config_dir / f"{config_name}.yaml"
        
        if not file_path.exists():
            print(f"Warning: Configuration file {file_path} not found, using defaults")
            return self._defaults.get(config_name, {})
        
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                config = {}
            
            # Merge with defaults
            merged_config = self._merge_configs(
                self._defaults.get(config_name, {}),
                config
            )
            
            # Validate
            self._validate_config(config_name, merged_config)
            
            # Cache
            self.configs[config_name] = merged_config
            
            return merged_config
            
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Failed to parse {file_path}: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Failed to load {file_path}: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge override config into default config.
        
        Args:
            default: Default configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _validate_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """
        Validate configuration values.
        
        Args:
            config_name: Name of the configuration
            config: Configuration dictionary
            
        Raises:
            ConfigValidationError: If validation fails
        """
        validators = {
            'pipeline': self._validate_pipeline,
            'model': self._validate_model,
            'colmap': self._validate_colmap,
            'gaussian': self._validate_gaussian,
            'physics': self._validate_physics,
            'minio': self._validate_minio
        }
        
        validator = validators.get(config_name)
        if validator:
            validator(config)
    
    def _validate_pipeline(self, config: Dict[str, Any]) -> None:
        """Validate pipeline configuration."""
        # Add specific validation rules
        pass
    
    def _validate_model(self, config: Dict[str, Any]) -> None:
        """Validate model configuration."""
        if 'yolov8' in config:
            confidence = config['yolov8'].get('confidence_threshold', 0.5)
            if not 0.0 <= confidence <= 1.0:
                raise ConfigValidationError(
                    f"YOLOv8 confidence_threshold must be in [0, 1], got {confidence}"
                )
    
    def _validate_colmap(self, config: Dict[str, Any]) -> None:
        """Validate COLMAP configuration."""
        if 'feature_extraction' in config:
            max_features = config['feature_extraction'].get('sift', {}).get('max_num_features', 8192)
            if max_features < 100:
                raise ConfigValidationError(
                    f"COLMAP max_num_features must be >= 100, got {max_features}"
                )
    
    def _validate_gaussian(self, config: Dict[str, Any]) -> None:
        """Validate Gaussian splatting configuration."""
        if 'training' in config:
            iterations = config['training'].get('iterations', 30000)
            if iterations < 1000:
                raise ConfigValidationError(
                    f"Gaussian training iterations must be >= 1000, got {iterations}"
                )
    
    def _validate_physics(self, config: Dict[str, Any]) -> None:
        """Validate physics configuration."""
        if 'engine' in config:
            time_step = config['engine'].get('time_step', 0.016667)
            if not 0.001 <= time_step <= 0.1:
                raise ConfigValidationError(
                    f"Physics time_step must be in [0.001, 0.1], got {time_step}"
                )
    
    def _validate_minio(self, config: Dict[str, Any]) -> None:
        """Validate MinIO configuration."""
        required_fields = ['endpoint', 'access_key', 'secret_key']
        for field in required_fields:
            if field not in config:
                raise ConfigValidationError(f"MinIO config missing required field: {field}")
    
    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files.
        
        Returns:
            Dictionary mapping config names to their configurations
        """
        config_names = ['pipeline', 'model', 'colmap', 'gaussian', 'physics', 'minio']
        
        for name in config_names:
            try:
                self.load(name)
            except Exception as e:
                print(f"Warning: Failed to load {name} config: {e}")
        
        return self.configs
    
    def get(self, config_name: str, key_path: Optional[str] = None, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            config_name: Name of the configuration
            key_path: Dot-separated path to nested key (e.g., 'engine.gravity')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if config_name not in self.configs:
            self.load(config_name)
        
        config = self.configs.get(config_name, {})
        
        if key_path is None:
            return config
        
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def reload(self, config_name: str) -> Dict[str, Any]:
        """
        Reload a configuration file.
        
        Args:
            config_name: Name of the configuration to reload
            
        Returns:
            Reloaded configuration
        """
        if config_name in self.configs:
            del self.configs[config_name]
        
        return self.load(config_name)


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: str = "configs", project_root: Optional[str] = None) -> ConfigLoader:
    """
    Get or create global configuration loader instance.
    
    Args:
        config_dir: Directory containing configuration files
        project_root: Project root directory
        
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir, project_root)
    
    return _config_loader


def load_config(config_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a configuration file using the global loader.
    
    Args:
        config_name: Name of the configuration
        config_path: Optional custom path to configuration file
        
    Returns:
        Configuration dictionary
    """
    loader = get_config_loader()
    return loader.load(config_name, config_path)


def get_config(config_name: str, key_path: Optional[str] = None, default: Any = None) -> Any:
    """
    Get a configuration value using the global loader.
    
    Args:
        config_name: Name of the configuration
        key_path: Dot-separated path to nested key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    loader = get_config_loader()
    return loader.get(config_name, key_path, default)
