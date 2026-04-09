"""Status-related Pydantic models."""

from pydantic import BaseModel
from typing import Optional


class StatusResponse(BaseModel):
    """Status response model."""
    job_id: str
    status: str
    stage: Optional[str]
    progress: float
    error: Optional[str]
    estimated_time_remaining: Optional[float]
