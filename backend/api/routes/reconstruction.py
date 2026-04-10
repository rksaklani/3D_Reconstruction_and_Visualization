"""Reconstruction data endpoints for serving 3D scene data."""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from backend.database import get_database
from backend.services.minio_service import get_minio_service
import logging
import json
import struct
from typing import Dict, List, Any
from io import BytesIO

router = APIRouter(prefix="/api/reconstruction", tags=["reconstruction"])
logger = logging.getLogger(__name__)


def parse_colmap_cameras_bin(data: bytes) -> List[Dict[str, Any]]:
    """Parse COLMAP cameras.bin file."""
    cameras = []
    offset = 0
    
    # Read number of cameras
    if len(data) < 8:
        return cameras
    
    num_cameras = struct.unpack('<Q', data[offset:offset+8])[0]
    offset += 8
    
    for _ in range(num_cameras):
        if offset + 24 > len(data):
            break
            
        camera_id = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        model_id = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        width = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        
        height = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        
        # Read parameters (varies by model, assume 4 for PINHOLE)
        num_params = 4
        params = []
        for _ in range(num_params):
            if offset + 8 > len(data):
                break
            param = struct.unpack('<d', data[offset:offset+8])[0]
            params.append(param)
            offset += 8
        
        cameras.append({
            'camera_id': camera_id,
            'model_id': model_id,
            'width': width,
            'height': height,
            'params': params
        })
    
    return cameras


def parse_colmap_images_bin(data: bytes) -> List[Dict[str, Any]]:
    """Parse COLMAP images.bin file."""
    images = []
    offset = 0
    
    # Read number of images
    if len(data) < 8:
        return images
    
    num_images = struct.unpack('<Q', data[offset:offset+8])[0]
    offset += 8
    
    for _ in range(num_images):
        if offset + 64 > len(data):
            break
        
        image_id = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        # Quaternion (qw, qx, qy, qz)
        qw = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        qx = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        qy = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        qz = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        
        # Translation
        tx = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        ty = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        tz = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        
        camera_id = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        
        # Read image name (null-terminated string)
        name_bytes = []
        while offset < len(data):
            byte = data[offset]
            offset += 1
            if byte == 0:
                break
            name_bytes.append(byte)
        
        name = bytes(name_bytes).decode('utf-8', errors='ignore')
        
        # Skip points2D data
        if offset + 8 > len(data):
            break
        num_points2d = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        offset += num_points2d * 24  # Each point2D is 24 bytes
        
        images.append({
            'image_id': image_id,
            'qvec': [qw, qx, qy, qz],
            'tvec': [tx, ty, tz],
            'camera_id': camera_id,
            'name': name
        })
    
    return images


def parse_colmap_points3d_bin(data: bytes) -> List[Dict[str, Any]]:
    """Parse COLMAP points3D.bin file."""
    points = []
    offset = 0
    
    # Read number of points
    if len(data) < 8:
        return points
    
    num_points = struct.unpack('<Q', data[offset:offset+8])[0]
    offset += 8
    
    for _ in range(min(num_points, 100000)):  # Limit to 100k points for performance
        if offset + 43 > len(data):
            break
        
        point_id = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        
        # XYZ position
        x = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        y = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        z = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        
        # RGB color
        r = struct.unpack('<B', data[offset:offset+1])[0]
        offset += 1
        g = struct.unpack('<B', data[offset:offset+1])[0]
        offset += 1
        b = struct.unpack('<B', data[offset:offset+1])[0]
        offset += 1
        
        # Error
        error = struct.unpack('<d', data[offset:offset+8])[0]
        offset += 8
        
        # Skip track data
        if offset + 8 > len(data):
            break
        track_length = struct.unpack('<Q', data[offset:offset+8])[0]
        offset += 8
        offset += track_length * 8  # Each track element is 8 bytes
        
        points.append({
            'point_id': point_id,
            'xyz': [x, y, z],
            'rgb': [r / 255.0, g / 255.0, b / 255.0],
            'error': error
        })
    
    return points


@router.get("/{job_id}/scene")
async def get_scene_data(job_id: str):
    """
    Get complete scene data for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Scene data with cameras, images, and point cloud
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    try:
        minio = get_minio_service()
        
        # Load COLMAP binary files from MinIO: storage/processed/{job_id}/sparse/
        cameras_data = minio.download_data(f"storage/processed/{job_id}/sparse/cameras.bin")
        images_data = minio.download_data(f"storage/processed/{job_id}/sparse/images.bin")
        points_data = minio.download_data(f"storage/processed/{job_id}/sparse/points3D.bin")
        
        # Parse binary data
        cameras = parse_colmap_cameras_bin(cameras_data)
        images = parse_colmap_images_bin(images_data)
        points = parse_colmap_points3d_bin(points_data)
        
        logger.info(f"Loaded scene for job {job_id}: {len(cameras)} cameras, {len(images)} images, {len(points)} points")
        
        return {
            "job_id": job_id,
            "cameras": cameras,
            "images": images,
            "points": points,
            "num_cameras": len(cameras),
            "num_images": len(images),
            "num_points": len(points)
        }
        
    except Exception as e:
        logger.error(f"Failed to load scene data for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load scene data: {str(e)}"
        )


@router.get("/{job_id}/points")
async def get_point_cloud(job_id: str, limit: int = 50000):
    """
    Get point cloud data for visualization.
    
    Args:
        job_id: Job identifier
        limit: Maximum number of points to return
        
    Returns:
        Point cloud data as Gaussian splats
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    try:
        minio = get_minio_service()
        
        # Load points3D.bin from storage/processed/{job_id}/sparse/
        points_data = minio.download_data(f"storage/processed/{job_id}/sparse/points3D.bin")
        points = parse_colmap_points3d_bin(points_data)
        
        # Limit number of points
        if len(points) > limit:
            # Sample points evenly
            step = len(points) // limit
            points = points[::step][:limit]
        
        # Convert to Gaussian splat format
        gaussians = []
        for point in points:
            gaussians.append({
                'position': point['xyz'],
                'scale': [0.02, 0.02, 0.02],  # Small uniform scale
                'rotation': [0, 0, 0, 1],  # Identity quaternion
                'color': point['rgb'] + [1.0],  # Add alpha
                'opacity': 0.9
            })
        
        logger.info(f"Returning {len(gaussians)} Gaussian splats for job {job_id}")
        
        return {
            "job_id": job_id,
            "gaussians": gaussians,
            "num_gaussians": len(gaussians)
        }
        
    except Exception as e:
        logger.error(f"Failed to load point cloud for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load point cloud: {str(e)}"
        )


@router.get("/{job_id}/cameras")
async def get_cameras(job_id: str):
    """
    Get camera data for a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Camera intrinsics and extrinsics
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    try:
        minio = get_minio_service()
        
        # Load camera and image data from storage/processed/{job_id}/sparse/
        cameras_data = minio.download_data(f"storage/processed/{job_id}/sparse/cameras.bin")
        images_data = minio.download_data(f"storage/processed/{job_id}/sparse/images.bin")
        
        cameras = parse_colmap_cameras_bin(cameras_data)
        images = parse_colmap_images_bin(images_data)
        
        return {
            "job_id": job_id,
            "cameras": cameras,
            "images": images
        }
        
    except Exception as e:
        logger.error(f"Failed to load cameras for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load cameras: {str(e)}"
        )


@router.get("/{job_id}/download/ply")
async def download_ply(job_id: str):
    """
    Download point cloud as PLY file.
    
    Args:
        job_id: Job identifier
        
    Returns:
        PLY file stream
    """
    db = get_database()
    
    # Get job
    job = await db.jobs.find_one({"job_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job['status']})"
        )
    
    try:
        minio = get_minio_service()
        
        # Load points from storage/processed/{job_id}/sparse/
        points_data = minio.download_data(f"storage/processed/{job_id}/sparse/points3D.bin")
        points = parse_colmap_points3d_bin(points_data)
        
        # Generate PLY file
        ply_content = f"""ply
format ascii 1.0
element vertex {len(points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
        
        for point in points:
            x, y, z = point['xyz']
            r, g, b = [int(c * 255) for c in point['rgb']]
            ply_content += f"{x} {y} {z} {r} {g} {b}\n"
        
        # Return as downloadable file
        return Response(
            content=ply_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={job_id}_pointcloud.ply"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to generate PLY for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PLY: {str(e)}"
        )
