"""Configuration endpoints."""

from fastapi import APIRouter
from backend.config.reconstruction_config import recon_config

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/")
async def get_config():
    """
    Get current reconstruction configuration.
    
    Returns:
        Configuration summary
    """
    return {
        "config": recon_config.get_config_summary(),
        "validation": recon_config.validate_paths()
    }


@router.get("/defaults")
async def get_defaults():
    """
    Get default job configuration.
    
    Returns:
        Default configuration for new jobs
    """
    return recon_config.get_job_config()
