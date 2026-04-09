"""Configuration management module."""

from .loader import ConfigLoader, load_config, get_config_loader

def get_config():
    """Get configuration dictionary."""
    loader = get_config_loader()
    return loader.config

__all__ = ['ConfigLoader', 'load_config', 'get_config_loader', 'get_config']
