"""Log viewing endpoints."""

from fastapi import APIRouter, HTTPException, Query, Response
from backend.database import get_database
from backend.services.minio_service import get_minio_service
import logging

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = logging.getLogger(__name__)


@router.get("/{job_id}")
async def get_job_logs(
    job_id: str,
    tail: int = Query(6000, description="Number of characters to return from end of log")
):
    """
    Get job processing logs from MinIO.
    
    Args:
        job_id: Job identifier
        tail: Number of characters to return from end
        
    Returns:
        Log content as plain text
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Try to get logs from MinIO
    try:
        minio = get_minio_service()
        log_object = f"storage/processed/{job_id}/logs/processing.log"
        
        # Check if log exists in MinIO
        if minio.object_exists(log_object):
            log_data = minio.download_data(log_object)
            log_content = log_data.decode('utf-8', errors='ignore')
            
            # Return last N characters if tail is specified
            if tail and len(log_content) > tail:
                log_content = "...[truncated]\n" + log_content[-tail:]
            
            return Response(content=log_content, media_type="text/plain")
    except Exception as e:
        logger.warning(f"Could not fetch logs from MinIO for job {job_id}: {e}")
    
    # Fallback: Generate status-based log
    log_content = f"""Job: {job.get('name', 'Unnamed')}
ID: {job_id}
User: {job['user_id']}
Status: {job['status']}
Stage: {job.get('stage', 'N/A')}
Progress: {job.get('progress', 0)*100:.1f}%
Created: {job['created_at']}
Updated: {job['updated_at']}

{'='*60}
Configuration:
{'='*60}
"""
    
    # Add config details
    config = job.get('config', {})
    for key, value in sorted(config.items()):
        if isinstance(value, list):
            log_content += f"{key}: {', '.join(map(str, value))}\n"
        else:
            log_content += f"{key}: {value}\n"
    
    log_content += f"\n{'='*60}\n"
    log_content += "Processing Status:\n"
    log_content += f"{'='*60}\n\n"
    
    # Add status messages
    if job['status'] == 'created':
        log_content += "✓ Job created successfully\n"
        log_content += "⏳ Waiting for file upload...\n"
    elif job['status'] == 'uploaded':
        log_content += f"✓ Job created successfully\n"
        log_content += f"✓ {job['num_files']} files uploaded\n"
        log_content += f"⏳ Ready to start processing...\n"
    elif job['status'] == 'processing':
        log_content += f"✓ Job created successfully\n"
        log_content += f"✓ Files uploaded\n"
        log_content += f"⚙️  Processing in progress...\n"
        log_content += f"   Stage: {job.get('stage', 'unknown')}\n"
        log_content += f"   Progress: {job.get('progress', 0)*100:.1f}%\n"
        
        if job.get('pid'):
            log_content += f"   Process ID: {job['pid']}\n"
    elif job['status'] == 'completed':
        log_content += f"✓ Job created successfully\n"
        log_content += f"✓ Files uploaded\n"
        log_content += f"✓ Processing completed\n\n"
        
        if job.get('started_at') and job.get('completed_at'):
            from datetime import datetime
            started = job['started_at']
            completed = job['completed_at']
            if isinstance(started, str):
                started = datetime.fromisoformat(started.replace('Z', ''))
            if isinstance(completed, str):
                completed = datetime.fromisoformat(completed.replace('Z', ''))
            duration = (completed - started).total_seconds()
            log_content += f"Duration: {int(duration//60)}m {int(duration%60)}s\n\n"
        
        log_content += "Results:\n"
        output_files = job.get('output_files', {})
        if output_files:
            for key, path in output_files.items():
                log_content += f"  - {key}: {path}\n"
        else:
            log_content += "  (No output files recorded)\n"
    elif job['status'] == 'failed':
        log_content += f"✓ Job created successfully\n"
        log_content += f"✓ Files uploaded\n"
        log_content += f"❌ Processing failed\n\n"
        log_content += f"Error: {job.get('error', 'Unknown error')}\n"
        
        if job.get('error_details'):
            log_content += f"\nDetails:\n{job['error_details']}\n"
    elif job['status'] == 'stopped':
        log_content += f"✓ Job created successfully\n"
        log_content += f"✓ Files uploaded\n"
        log_content += f"⚠️  Processing stopped by user\n"
    
    # Add input files info
    if job.get('input_files'):
        log_content += f"\n{'='*60}\n"
        log_content += f"Input Files ({len(job['input_files'])}):\n"
        log_content += f"{'='*60}\n"
        for i, file_path in enumerate(job['input_files'][:20], 1):
            filename = file_path.split('/')[-1]
            log_content += f"  {i}. {filename}\n"
        if len(job['input_files']) > 20:
            log_content += f"  ... and {len(job['input_files']) - 20} more\n"
    
    # Add stats if available
    if job.get('stats'):
        log_content += f"\n{'='*60}\n"
        log_content += "Statistics:\n"
        log_content += f"{'='*60}\n"
        for key, value in job['stats'].items():
            log_content += f"  {key}: {value}\n"
    
    log_content += f"\n{'='*60}\n"
    log_content += "Note: Detailed processing logs will be available in MinIO after job completion.\n"
    log_content += f"{'='*60}\n"
    
    return Response(content=log_content, media_type="text/plain")
