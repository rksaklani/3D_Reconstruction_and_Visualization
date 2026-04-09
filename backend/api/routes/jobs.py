"""Job management endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import uuid

from backend.database import get_database
from backend.api.models.job import (
    JobCreate,
    JobResponse,
    JobUpdate,
    JobListResponse
)
from backend.config.reconstruction_config import recon_config

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """
    Create a new reconstruction job.
    
    Args:
        job_data: Job creation data
        
    Returns:
        Created job with configuration from .env
    """
    db = get_database()
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Get default configuration from .env
    default_config = recon_config.get_job_config()
    
    # Merge with any custom config provided
    if job_data.config:
        default_config.update(job_data.config)
    
    # Create job document
    job_doc = {
        "job_id": job_id,
        "user_id": job_data.user_id,
        "name": job_data.name,
        "description": job_data.description,
        "config": default_config,  # Configuration from .env
        "status": "created",
        "stage": None,
        "progress": 0.0,
        "input_files": [],
        "input_type": None,
        "num_files": 0,
        "output_files": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "error": None,
        "error_details": None,
        "stats": {},
        "log_file": None
    }
    
    # Insert into MongoDB
    result = await db.jobs.insert_one(job_doc)
    
    # Return response
    return JobResponse(**job_doc)


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of jobs to return"),
    skip: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """
    List jobs with optional filtering.
    
    Args:
        user_id: Filter by user ID
        status: Filter by status
        limit: Maximum number of jobs to return
        skip: Number of jobs to skip (pagination)
        
    Returns:
        List of jobs
    """
    db = get_database()
    
    # Build query
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status:
        query["status"] = status
    
    # Get jobs
    cursor = db.jobs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    jobs = await cursor.to_list(length=limit)
    
    # Get total count
    total = await db.jobs.count_documents(query)
    
    # Convert to response models
    job_responses = [JobResponse(**job) for job in jobs]
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        limit=limit,
        skip=skip
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get job by ID.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job details
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(**job)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_update: JobUpdate):
    """
    Update job.
    
    Args:
        job_id: Job identifier
        job_update: Job update data
        
    Returns:
        Updated job
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    if job_update.name is not None:
        update_doc["name"] = job_update.name
    if job_update.description is not None:
        update_doc["description"] = job_update.description
    if job_update.config is not None:
        update_doc["config"] = {**job.get("config", {}), **job_update.config}
    
    # Update in database
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": update_doc}
    )
    
    # Get updated job
    updated_job = await db.jobs.find_one({"job_id": job_id})
    
    return JobResponse(**updated_job)


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """
    Delete job and associated data.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Deletion confirmation
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # TODO: Delete associated files from MinIO
    # TODO: Delete associated results
    
    # Delete job
    await db.jobs.delete_one({"job_id": job_id})
    
    return {
        "job_id": job_id,
        "status": "deleted",
        "message": "Job deleted successfully"
    }


@router.get("/{job_id}/stats")
async def get_job_stats(job_id: str):
    """
    Get job statistics.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job statistics
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate duration
    duration = None
    if job.get("started_at") and job.get("completed_at"):
        duration = (job["completed_at"] - job["started_at"]).total_seconds()
    elif job.get("started_at"):
        duration = (datetime.utcnow() - job["started_at"]).total_seconds()
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "duration_seconds": duration,
        "num_files": job["num_files"],
        "stats": job.get("stats", {})
    }



@router.get("/{job_id}/log")
async def get_job_log(
    job_id: str,
    tail: int = Query(6000, description="Number of lines to return from end of log")
):
    """
    Get job processing log.
    
    Args:
        job_id: Job identifier
        tail: Number of lines to return from end
        
    Returns:
        Log content
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if log file exists
    log_file = job.get("log_file")
    
    if not log_file:
        # Return empty log if no log file yet
        return {
            "job_id": job_id,
            "log": f"Job created at {job['created_at']}\nStatus: {job['status']}\nNo processing log available yet.",
            "lines": 3
        }
    
    # TODO: Fetch log from MinIO or local file
    # For now, return status info
    log_content = f"""Job: {job['name']}
ID: {job_id}
Status: {job['status']}
Stage: {job.get('stage', 'N/A')}
Progress: {job['progress']}%
Created: {job['created_at']}
Updated: {job['updated_at']}

Configuration:
{'-' * 50}
"""
    
    # Add config details
    config = job.get('config', {})
    for key, value in config.items():
        log_content += f"{key}: {value}\n"
    
    log_content += f"\n{'-' * 50}\n"
    
    # Add status messages
    if job['status'] == 'created':
        log_content += "\n✓ Job created successfully\n⏳ Waiting for file upload...\n"
    elif job['status'] == 'uploaded':
        log_content += f"\n✓ Job created successfully\n✓ {job['num_files']} files uploaded\n⏳ Ready to start processing...\n"
    elif job['status'] == 'processing':
        log_content += f"\n✓ Job created successfully\n✓ Files uploaded\n⚙️  Processing in progress...\nStage: {job.get('stage', 'unknown')}\nProgress: {job['progress']}%\n"
    elif job['status'] == 'completed':
        log_content += f"\n✓ Job created successfully\n✓ Files uploaded\n✓ Processing completed\n\nResults:\n"
        output_files = job.get('output_files', {})
        for key, path in output_files.items():
            log_content += f"  - {key}: {path}\n"
    elif job['status'] == 'failed':
        log_content += f"\n✓ Job created successfully\n✓ Files uploaded\n❌ Processing failed\n\nError: {job.get('error', 'Unknown error')}\n"
        if job.get('error_details'):
            log_content += f"\nDetails:\n{job['error_details']}\n"
    
    # Add input files info
    if job.get('input_files'):
        log_content += f"\nInput Files ({len(job['input_files'])}):\n"
        for i, file_path in enumerate(job['input_files'][:10], 1):
            log_content += f"  {i}. {file_path.split('/')[-1]}\n"
        if len(job['input_files']) > 10:
            log_content += f"  ... and {len(job['input_files']) - 10} more\n"
    
    return {
        "job_id": job_id,
        "log": log_content,
        "lines": len(log_content.split('\n'))
    }
