"""Download and results endpoints."""

from fastapi import APIRouter, HTTPException
from backend.database import get_database
from backend.services.minio_service import get_minio_service
from datetime import timedelta

router = APIRouter(prefix="/api/download", tags=["download"])


@router.get("/{job_id}")
async def get_download_links(job_id: str):
    """
    Get download links for reconstruction results.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Download URLs for various formats
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    # Get MinIO service
    minio = get_minio_service()
    
    # Generate presigned URLs (valid for 1 hour)
    download_urls = {}
    
    for file_type, object_name in job["output_files"].items():
        try:
            url = minio.get_presigned_url(object_name, expires=timedelta(hours=1))
            download_urls[file_type] = url
        except Exception as e:
            print(f"Failed to generate URL for {file_type}: {e}")
    
    return {
        "job_id": job_id,
        "status": "completed",
        "download_urls": download_urls
    }


@router.get("/{job_id}/results")
async def get_results(job_id: str):
    """
    Get reconstruction results and statistics.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Reconstruction results
    """
    db = get_database()
    
    job = await db.jobs.find_one({"job_id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get result document
    result = await db.results.find_one({"job_id": job_id})
    
    if not result:
        return {
            "job_id": job_id,
            "status": job["status"],
            "message": "Results not available yet"
        }
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "num_cameras": result.get("num_cameras", 0),
        "num_images": result.get("num_images", 0),
        "num_points": result.get("num_points", 0),
        "num_gaussians": result.get("num_gaussians", 0),
        "num_triangles": result.get("num_triangles", 0),
        "mean_reprojection_error": result.get("mean_reprojection_error"),
        "reconstruction_quality": result.get("reconstruction_quality"),
        "detected_objects": result.get("detected_objects", []),
        "scene_classification": result.get("scene_classification"),
        "files": result.get("files", {})
    }
