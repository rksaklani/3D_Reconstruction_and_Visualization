"""Configuration loader with validation and merging."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Main configuration container."""
    pipeline: Dict[str, Any] = field(default_factory=dict)
    model: Dict[str, Any] = field(default_factory=dict)
    minio: Dict[str, Any] = field(default_factory=dict)
    colmap: Dict[str, Any] = field(default_factory=dict)
    gaussian: Dict[str, Any] = field(default_factory=dict)
    physics: Dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    """Load and validate YAML configurations."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize config loader.
        
        Args:
            config_dir: Path to config directory. Defaults to project root/configs
        """
        if config_dir is None:
            # Default to configs/ in project root
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "configs"
        
        self.config_dir = Path(config_dir)
        self._config = Config()
        self._loaded = False
    
    def load_all(self) -> Config:
        """Load all configuration files.
        
        Returns:
            Config object with all loaded configurations
        """
        config_files = {
            'pipeline': 'pipeline.yaml',
            'model': 'model.yaml',
            'minio': 'minio.yaml',
            'colmap': 'colmap.yaml',
            'gaussian': 'gaussian.yaml',
            'physics': 'physics.yaml'
        }
        
        for key, filename in config_files.items():
            filepath = self.config_dir / filename
            if filepath.exists():
                setattr(self._config, key, self._load_yaml(filepath))
            else:
                print(f"Warning: Config file not found: {filepath}")
        
        self._loaded = True
        return self._config
    
    def load(self, config_name: str) -> Dict[str, Any]:
        """Load a specific configuration file.
        
        Args:
            config_name: Name of config (e.g., 'pipeline', 'model')
        
        Returns:
            Configuration dictionary
        """
        filepath = self.config_dir / f"{config_name}.yaml"
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        return self._load_yaml(filepath)
    
    def _load_yaml(self, filepath: Path) -> Dict[str, Any]:
        """Load YAML file.
        
        Args:
            filepath: Path to YAML file
        
        Returns:
            Parsed YAML as dictionary
        """
        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
                return config if config is not None else {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {filepath}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'pipeline.preprocessing.resize')
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        if not self._loaded:
            self.load_all()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = getattr(value, k, None)
            
            if value is None:
                return default
        
        return value
    
    def merge(self, config_dict: Dict[str, Any], section: str) -> None:
        """Merge additional configuration into existing config.
        
        Args:
            config_dict: Configuration dictionary to merge
            section: Section to merge into (e.g., 'pipeline', 'model')
        """
        if not self._loaded:
            self.load_all()
        
        current = getattr(self._config, section, {})
        merged = self._deep_merge(current, config_dict)
        setattr(self._config, section, merged)
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
        
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate(self) -> bool:
        """Validate loaded configurations.
        
        Returns:
            True if all configurations are valid
        """
        if not self._loaded:
            self.load_all()
        
        validators = [
            self._validate_pipeline,
            self._validate_model,
            self._validate_minio,
            self._validate_colmap,
            self._validate_gaussian,
            self._validate_physics
        ]
        
        for validator in validators:
            if not validator():
                return False
        
        return True
    
    def _validate_pipeline(self) -> bool:
        """Validate pipeline configuration."""
        required = ['preprocessing', 'sfm', 'optimization']
        return all(key in self._config.pipeline for key in required)
    
    def _validate_model(self) -> bool:
        """Validate model configuration."""
        required = ['detection', 'segmentation', 'classification']
        return all(key in self._config.model for key in required)
    
    def _validate_minio(self) -> bool:
        """Validate MinIO configuration."""
        required = ['endpoint', 'access_key', 'secret_key']
        return all(key in self._config.minio for key in required)
    
    def _validate_colmap(self) -> bool:
        """Validate COLMAP configuration."""
        required = ['feature_extraction', 'feature_matching', 'mapper']
        return all(key in self._config.colmap for key in required)
    
    def _validate_gaussian(self) -> bool:
        """Validate Gaussian splatting configuration."""
        required = ['model', 'optimization', 'rendering']
        return all(key in self._config.gaussian for key in required)
    
    def _validate_physics(self) -> bool:
        """Validate physics configuration."""
        required = ['engine', 'gravity', 'simulation']
        return all(key in self._config.physics for key in required)
    
    @property
    def config(self) -> Config:
        """Get the loaded configuration."""
        if not self._loaded:
            self.load_all()
        return self._config


# Global config loader instance
_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: Optional[str] = None) -> ConfigLoader:
    """Get or create global config loader instance.
    
    Args:
        config_dir: Path to config directory
    
    Returns:
        ConfigLoader instance
    """
    global _loader
    if _loader is None:
        _loader = ConfigLoader(config_dir)
    return _loader


def load_config(config_name: Optional[str] = None) -> Any:
    """Load configuration (convenience function).
    
    Args:
        config_name: Specific config to load, or None for all
    
    Returns:
        Config object or specific configuration dict
    """
    loader = get_config_loader()
    
    if config_name is None:
        return loader.load_all()
    else:
        return loader.load(config_name)
