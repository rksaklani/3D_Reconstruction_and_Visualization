"""Job-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class JobCreate(BaseModel):
    """Job creation request."""
    user_id: str = Field(..., description="User identifier")
    name: Optional[str] = Field(None, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")


class JobUpdate(BaseModel):
    """Job update request."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
    """Job response model."""
    job_id: str
    user_id: str
    name: Optional[str]
    description: Optional[str]
    status: str
    stage: Optional[str]
    progress: float
    config: Dict[str, Any]
    input_files: List[str]
    input_type: Optional[str]
    num_files: int
    output_files: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]
    stats: Dict[str, Any]
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Job list response."""
    jobs: List[JobResponse]
    total: int
    limit: int
    skip: int
