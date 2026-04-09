"""MinIO object storage service."""

import os
import io
from datetime import timedelta
from pathlib import Path
from typing import Optional, List, BinaryIO, Dict, Any
from minio import Minio
from minio.error import S3Error
from urllib.parse import urlparse


class MinIOServiceError(Exception):
    """Base exception for MinIO service errors."""
    pass


class MinIOService:
    """MinIO object storage service for managing pipeline data."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        bucket_name: str = "3d-pipeline"
    ):
        """
        Initialize MinIO service.
        
        Args:
            endpoint: MinIO server endpoint (e.g., 'localhost:9000')
            access_key: Access key for authentication
            secret_key: Secret key for authentication
            secure: Use HTTPS if True
            bucket_name: Default bucket name
        """
        self.endpoint = endpoint
        self.bucket_name = bucket_name
        
        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                
        except S3Error as e:
            raise MinIOServiceError(f"Failed to initialize MinIO client: {e}")
    
    def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            file_path: Path to local file
            object_name: Object name in MinIO (path in bucket)
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
            
        Returns:
            Object name in MinIO
            
        Raises:
            MinIOServiceError: If upload fails
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise MinIOServiceError(f"File not found: {file_path}")
            
            # Auto-detect content type if not provided
            if content_type is None:
                content_type = self._get_content_type(file_path)
            
            self.client.fput_object(
                self.bucket_name,
                object_name,
                str(file_path),
                content_type=content_type,
                metadata=metadata
            )
            
            return object_name
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to upload file: {e}")
    
    def upload_data(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload binary data to MinIO.
        
        Args:
            data: Binary data to upload
            object_name: Object name in MinIO
            content_type: MIME type
            metadata: Optional metadata dictionary
            
        Returns:
            Object name in MinIO
            
        Raises:
            MinIOServiceError: If upload fails
        """
        try:
            data_stream = io.BytesIO(data)
            data_length = len(data)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                data_length,
                content_type=content_type,
                metadata=metadata
            )
            
            return object_name
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to upload data: {e}")
    
    def download_file(
        self,
        object_name: str,
        file_path: str
    ) -> str:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Object name in MinIO
            file_path: Local path to save file
            
        Returns:
            Local file path
            
        Raises:
            MinIOServiceError: If download fails
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.fget_object(
                self.bucket_name,
                object_name,
                file_path
            )
            
            return file_path
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to download file: {e}")
    
    def download_data(self, object_name: str) -> bytes:
        """
        Download binary data from MinIO.
        
        Args:
            object_name: Object name in MinIO
            
        Returns:
            Binary data
            
        Raises:
            MinIOServiceError: If download fails
        """
        try:
            response = self.client.get_object(
                self.bucket_name,
                object_name
            )
            
            data = response.read()
            response.close()
            response.release_conn()
            
            return data
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to download data: {e}")
    
    def list_objects(
        self,
        prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List objects in MinIO bucket.
        
        Args:
            prefix: Filter objects by prefix
            recursive: List recursively if True
            
        Returns:
            List of object information dictionaries
            
        Raises:
            MinIOServiceError: If listing fails
        """
        try:
            objects = []
            
            for obj in self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=recursive
            ):
                objects.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'content_type': obj.content_type
                })
            
            return objects
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to list objects: {e}")
    
    def delete_object(self, object_name: str) -> None:
        """
        Delete an object from MinIO.
        
        Args:
            object_name: Object name in MinIO
            
        Raises:
            MinIOServiceError: If deletion fails
        """
        try:
            self.client.remove_object(
                self.bucket_name,
                object_name
            )
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to delete object: {e}")
    
    def delete_objects(self, object_names: List[str]) -> None:
        """
        Delete multiple objects from MinIO.
        
        Args:
            object_names: List of object names
            
        Raises:
            MinIOServiceError: If deletion fails
        """
        try:
            errors = self.client.remove_objects(
                self.bucket_name,
                object_names
            )
            
            # Check for errors
            error_list = list(errors)
            if error_list:
                raise MinIOServiceError(f"Failed to delete some objects: {error_list}")
                
        except S3Error as e:
            raise MinIOServiceError(f"Failed to delete objects: {e}")
    
    def object_exists(self, object_name: str) -> bool:
        """
        Check if an object exists in MinIO.
        
        Args:
            object_name: Object name in MinIO
            
        Returns:
            True if object exists, False otherwise
        """
        try:
            self.client.stat_object(
                self.bucket_name,
                object_name
            )
            return True
            
        except S3Error:
            return False
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a presigned URL for temporary access to an object.
        
        Args:
            object_name: Object name in MinIO
            expires: URL expiration time
            
        Returns:
            Presigned URL
            
        Raises:
            MinIOServiceError: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to generate presigned URL: {e}")
    
    def get_presigned_upload_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate a presigned URL for uploading an object.
        
        Args:
            object_name: Object name in MinIO
            expires: URL expiration time
            
        Returns:
            Presigned upload URL
            
        Raises:
            MinIOServiceError: If URL generation fails
        """
        try:
            url = self.client.presigned_put_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            raise MinIOServiceError(f"Failed to generate presigned upload URL: {e}")
    
    def get_object_path(self, user_id: str, job_id: str, *path_parts: str) -> str:
        """
        Generate hierarchical object path.
        
        Args:
            user_id: User identifier
            job_id: Job identifier
            *path_parts: Additional path components
            
        Returns:
            Object path string
        """
        parts = [user_id, job_id] + list(path_parts)
        return "/".join(parts)
    
    def _get_content_type(self, file_path: Path) -> str:
        """
        Determine content type from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            MIME type string
        """
        extension_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.ply': 'application/octet-stream',
            '.obj': 'application/octet-stream',
            '.json': 'application/json',
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.txt': 'text/plain',
            '.log': 'text/plain',
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, 'application/octet-stream')


# Global MinIO service instance
_minio_service: Optional[MinIOService] = None


def get_minio_service(
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    secure: Optional[bool] = None,
    bucket_name: Optional[str] = None
) -> MinIOService:
    """
    Get or create global MinIO service instance.
    
    Args:
        endpoint: MinIO server endpoint
        access_key: Access key
        secret_key: Secret key
        secure: Use HTTPS
        bucket_name: Bucket name
        
    Returns:
        MinIOService instance
    """
    global _minio_service
    
    if _minio_service is None:
        # Get from environment or use defaults
        endpoint = endpoint or os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        access_key = access_key or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        secure = secure if secure is not None else os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        bucket_name = bucket_name or os.getenv('MINIO_BUCKET', '3d-pipeline')
        
        _minio_service = MinIOService(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            bucket_name=bucket_name
        )
    
    return _minio_service
