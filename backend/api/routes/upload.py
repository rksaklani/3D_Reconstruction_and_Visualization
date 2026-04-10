"""File upload endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import logging

from backend.database import get_database
from backend.services.minio_service import get_minio_service
from backend.api.models.upload import UploadResponse
from backend.pipeline.threaded_pipeline import get_threaded_pipeline
from datetime import datetime

router = APIRouter(prefix="/api/upload", tags=["upload"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=UploadResponse)
async def upload_files(
    job_id: str = Form(..., description="Job ID"),
    files: List[UploadFile] = File(..., description="Files to upload"),
    auto_start: bool = Form(True, description="Auto-start processing after upload")
):
    """
    Upload files for a job.
    
    Args:
        job_id: Job identifier
        files: List of files to upload
        auto_start: Automatically start processing after upload (default: True)
        
    Returns:
        Upload confirmation with file details
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate files
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Get MinIO service
    minio = get_minio_service()
    
    # Upload files
    uploaded_files = []
    total_size = 0
    
    for file in files:
        # Validate file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.mp4', '.mov', '.avi', '.mkv'}
        file_ext = file.filename.split('.')[-1].lower()
        
        if f'.{file_ext}' not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        total_size += file_size
        
        # Upload to MinIO with storage structure
        object_name = f"storage/uploads/{job['user_id']}/{job_id}/{file.filename}"
        
        try:
            minio.upload_data(
                content,
                object_name,
                content_type=file.content_type or "application/octet-stream"
            )
            
            uploaded_files.append({
                'filename': file.filename,
                'size': file_size,
                'object_name': object_name
            })
            
            logger.info(f"Uploaded {file.filename} ({file_size} bytes) to {object_name}")
            
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    # Update job
    input_type = "video" if any(f['filename'].endswith(('.mp4', '.mov', '.avi')) for f in uploaded_files) else "images"
    
    # Determine status based on auto_start
    status = "processing" if auto_start else "uploaded"
    
    update_data = {
        "input_files": [f['object_name'] for f in uploaded_files],
        "num_files": len(uploaded_files),
        "status": status,
        "input_type": input_type,
        "updated_at": datetime.utcnow()
    }
    
    # If auto-starting, set initial processing fields
    if auto_start:
        update_data["stage"] = "initializing"
        update_data["progress"] = 0
        update_data["started_at"] = datetime.utcnow()
    
    await db.jobs.update_one(
        {"job_id": job_id},
        {"$set": update_data}
    )
    
    # Auto-start processing if requested
    if auto_start:
        pipeline = get_threaded_pipeline()
        pipeline.start_job(job_id)
        logger.info(f"Auto-starting processing for job: {job_id}")
    
    return UploadResponse(
        job_id=job_id,
        status=status,
        num_files=len(uploaded_files),
        total_size=total_size,
        files=uploaded_files
    )


@router.get("/{job_id}")
async def get_upload_info(job_id: str):
    """
    Get upload information for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Upload information
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job_id,
        "num_files": job["num_files"],
        "input_type": job.get("input_type"),
        "input_files": job["input_files"]
    }
