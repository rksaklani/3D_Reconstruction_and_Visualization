"""Processing endpoints for running the reconstruction pipeline."""

from fastapi import APIRouter, HTTPException
from backend.database import get_database
from backend.pipeline.threaded_pipeline import get_threaded_pipeline
import logging

router = APIRouter(prefix="/api/process", tags=["process"])
logger = logging.getLogger(__name__)


@router.post("/{job_id}/start")
async def start_processing(job_id: str):
    """
    Start processing a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Processing confirmation
    """
    from datetime import datetime
    
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if job has files
    if not job.get('input_files') or job['num_files'] == 0:
        raise HTTPException(
            status_code=400,
            detail="Job has no input files. Upload files first."
        )
    
    # Check if already processing
    if job['status'] in ['processing', 'completed']:
        raise HTTPException(
            status_code=400,
            detail=f"Job already {job['status']}"
        )
    
    # Update status to processing immediately
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": "processing",
            "stage": "initializing",
            "progress": 0,
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Start processing in background thread
    pipeline = get_threaded_pipeline()
    pipeline.start_job(job_id)
    
    logger.info(f"Started processing job: {job_id}")
    
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Job processing started"
    }


@router.post("/{job_id}/stop")
async def stop_processing(job_id: str):
    """
    Stop processing a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Stop confirmation
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if processing
    if job['status'] != 'processing':
        raise HTTPException(
            status_code=400,
            detail=f"Job is not processing (status: {job['status']})"
        )
    
    # Stop job
    pipeline = get_threaded_pipeline()
    pipeline.stop_job(job_id)
    
    logger.info(f"Stopped processing job: {job_id}")
    
    return {
        "job_id": job_id,
        "status": "stopped",
        "message": "Job processing stopped"
    }

