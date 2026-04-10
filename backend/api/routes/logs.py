"""Log retrieval endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pathlib import Path
from backend.database import get_database
import logging

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = logging.getLogger(__name__)


@router.get("/{job_id}", response_class=PlainTextResponse)
def get_job_logs(job_id: str, tail: int = 6000):
    """
    Get job logs.
    
    Args:
        job_id: Job identifier
        tail: Maximum number of characters to return (default: 6000)
        
    Returns:
        Log file content as plain text
    """
    db = get_database()
    
    # Get job to verify it exists
    job = db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get log path
    log_path = Path(f"/tmp/reconstruction_jobs/{job_id}/live.log")
    
    # Return empty string if log file doesn't exist
    if not log_path.exists():
        return PlainTextResponse("")
    
    # Read log file
    try:
        data = log_path.read_text(encoding="utf-8", errors="replace")
        
        # Tail if requested
        if tail > 0 and len(data) > tail:
            data = data[-tail:]
        
        return PlainTextResponse(data)
    
    except Exception as e:
        logger.error(f"Failed to read log file for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")
