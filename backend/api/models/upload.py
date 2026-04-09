"""Upload-related Pydantic models."""

from pydantic import BaseModel
from typing import List, Dict, Any


class UploadResponse(BaseModel):
    """Upload response model."""
    job_id: str
    status: str
    num_files: int
    total_size: int
    files: List[Dict[str, Any]]
