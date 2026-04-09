"""Status and progress endpoints."""

from fastapi import APIRouter, HTTPException
from backend.database import get_database
from backend.api.models.status import StatusResponse

router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("/{job_id}", response_model=StatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status with progress information
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate estimated time remaining
    estimated_time = None
    if job["progress"] > 0 and job["progress"] < 1.0 and job.get("started_at"):
        from datetime import datetime
        elapsed = (datetime.utcnow() - job["started_at"]).total_seconds()
        estimated_time = (elapsed / job["progress"]) * (1.0 - job["progress"])
    
    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        stage=job.get("stage"),
        progress=job["progress"],
        error=job.get("error"),
        estimated_time_remaining=estimated_time
    )
