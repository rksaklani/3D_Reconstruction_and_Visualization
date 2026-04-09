"""3D Reconstruction API endpoints."""

import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.pipeline.orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reconstruction"])

# Job storage (in production, use database)
jobs_db = {}


class JobStatus(BaseModel):
    """Job status response model."""
    job_id: str
    status: str
    stage: Optional[str] = None
    progress: float
    error: Optional[str] = None
    estimated_time_remaining: Optional[float] = None


class JobResult(BaseModel):
    """Job result response model."""
    job_id: str
    status: str
    download_urls: dict


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    user_id: str = Form(default="default_user")
):
    """
    Upload images or video for 3D reconstruction.
    
    Args:
        files: List of image files or single video file
        user_id: User identifier
        
    Returns:
        Job ID and upload status
    """
    try:
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Create job directory
        job_dir = Path(f"uploads/{user_id}/{job_id}")
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded files
        saved_files = []
        for file in files:
            file_path = job_dir / file.filename
            
            # Validate file extension
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi'}
            if file_path.suffix.lower() not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file_path.suffix}"
                )
            
            # Save file
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            saved_files.append(str(file_path))
        
        # Create job entry
        jobs_db[job_id] = {
            'job_id': job_id,
            'user_id': user_id,
            'status': 'uploaded',
            'files': saved_files,
            'stage': 'upload',
            'progress': 0.0
        }
        
        logger.info(f"Created job {job_id} with {len(saved_files)} files")
        
        return JSONResponse({
            'job_id': job_id,
            'status': 'uploaded',
            'num_files': len(saved_files)
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reconstruct/{job_id}")
async def start_reconstruction(job_id: str):
    """
    Start 3D reconstruction pipeline for uploaded files.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status
    """
    try:
        if job_id not in jobs_db:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs_db[job_id]
        
        if job['status'] != 'uploaded':
            raise HTTPException(
                status_code=400,
                detail=f"Job already {job['status']}"
            )
        
        # Update job status
        job['status'] = 'processing'
        job['stage'] = 'preprocessing'
        
        # Start pipeline (in production, use Celery task queue)
        # For now, just update status
        logger.info(f"Starting reconstruction for job {job_id}")
        
        # TODO: Start actual pipeline
        # orchestrator = PipelineOrchestrator()
        # orchestrator.execute_pipeline(job_id, job['files'][0], f"output/{job_id}")
        
        return JSONResponse({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Reconstruction started'
        })
        
    except Exception as e:
        logger.error(f"Reconstruction start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get job status and progress.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status with progress information
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    # Calculate estimated time remaining (simplified)
    estimated_time = None
    if job['progress'] > 0 and job['progress'] < 1.0:
        # Rough estimate: 5 minutes total
        estimated_time = (1.0 - job['progress']) * 300
    
    return JobStatus(
        job_id=job_id,
        status=job['status'],
        stage=job.get('stage'),
        progress=job['progress'],
        error=job.get('error'),
        estimated_time_remaining=estimated_time
    )


@router.get("/download/{job_id}", response_model=JobResult)
async def get_download_links(job_id: str):
    """
    Get download links for reconstruction results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Download URLs for various formats
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    # Generate presigned URLs (in production, use MinIO presigned URLs)
    download_urls = {
        'ply': f"/downloads/{job_id}/gaussians.ply",
        'obj': f"/downloads/{job_id}/mesh.obj",
        'json': f"/downloads/{job_id}/scene.json",
        'zip': f"/downloads/{job_id}/complete.zip"
    }
    
    return JobResult(
        job_id=job_id,
        status='completed',
        download_urls=download_urls
    )


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete job and associated files.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Deletion confirmation
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete job files
    job = jobs_db[job_id]
    
    try:
        # Delete uploaded files
        for file_path in job.get('files', []):
            Path(file_path).unlink(missing_ok=True)
        
        # Delete job directory
        job_dir = Path(f"uploads/{job['user_id']}/{job_id}")
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir)
        
        # Remove from database
        del jobs_db[job_id]
        
        logger.info(f"Deleted job {job_id}")
        
        return JSONResponse({
            'job_id': job_id,
            'status': 'deleted'
        })
        
    except Exception as e:
        logger.error(f"Job deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        'status': 'healthy',
        'service': '3D Reconstruction API',
        'version': '1.0.0'
    })
