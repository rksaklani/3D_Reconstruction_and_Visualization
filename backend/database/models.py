"""MongoDB document models using Beanie ODM."""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    CREATED = "created"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    FEATURE_EXTRACTION = "feature_extraction"
    FEATURE_MATCHING = "feature_matching"
    SFM = "sfm"
    AI_PROCESSING = "ai_processing"
    GAUSSIAN_TRAINING = "gaussian_training"
    MESH_EXTRACTION = "mesh_extraction"
    PHYSICS_SIMULATION = "physics_simulation"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""
    UPLOAD = "upload"
    PREPROCESSING = "preprocessing"
    SFM = "sfm"
    AI = "ai"
    RECONSTRUCTION = "reconstruction"
    PHYSICS = "physics"
    RENDERING = "rendering"
    EXPORT = "export"


class Job(Document):
    """Job document model."""
    
    # Job identification
    job_id: Indexed(str, unique=True)  # Unique job identifier
    user_id: Indexed(str)  # User who created the job
    name: Optional[str] = None  # Job name
    description: Optional[str] = None  # Job description
    
    # Status
    status: JobStatus = JobStatus.CREATED
    stage: Optional[PipelineStage] = None
    progress: float = 0.0  # 0.0 to 1.0
    pid: Optional[int] = None  # Process ID for subprocess control
    
    # Configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Input files
    input_files: List[str] = Field(default_factory=list)  # MinIO object names
    input_type: Optional[str] = None  # "images" or "video"
    num_files: int = 0
    
    # Output files
    output_files: Dict[str, str] = Field(default_factory=dict)  # {type: minio_path}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error handling
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Statistics
    stats: Dict[str, Any] = Field(default_factory=dict)
    
    # Logs
    log_file: Optional[str] = None  # MinIO path to log file
    
    class Settings:
        name = "jobs"
        indexes = [
            "job_id",
            "user_id",
            "status",
            "created_at",
        ]
    
    def update_progress(self, progress: float, stage: Optional[PipelineStage] = None):
        """Update job progress."""
        self.progress = max(0.0, min(1.0, progress))
        if stage:
            self.stage = stage
        self.updated_at = datetime.utcnow()
    
    def mark_started(self):
        """Mark job as started."""
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.progress = 1.0
    
    def mark_failed(self, error: str, details: Optional[Dict[str, Any]] = None):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error = error
        self.error_details = details
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class User(Document):
    """User document model."""
    
    user_id: Indexed(str, unique=True)
    email: Optional[str] = None
    name: Optional[str] = None
    
    # API access
    api_key: Optional[str] = None
    api_key_created_at: Optional[datetime] = None
    
    # Quotas
    max_jobs: int = 100
    max_storage_gb: float = 10.0
    
    # Statistics
    total_jobs: int = 0
    active_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "email",
        ]


class Result(Document):
    """Reconstruction result document model."""
    
    job_id: Indexed(str)
    user_id: Indexed(str)
    
    # Result files
    files: Dict[str, str] = Field(default_factory=dict)  # {type: minio_path}
    
    # Reconstruction statistics
    num_cameras: int = 0
    num_images: int = 0
    num_points: int = 0
    num_gaussians: int = 0
    num_triangles: int = 0
    
    # Quality metrics
    mean_reprojection_error: Optional[float] = None
    reconstruction_quality: Optional[str] = None  # "low", "medium", "high"
    
    # AI results
    detected_objects: List[Dict[str, Any]] = Field(default_factory=list)
    scene_classification: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_sizes: Dict[str, int] = Field(default_factory=dict)  # {type: size_bytes}
    
    class Settings:
        name = "results"
        indexes = [
            "job_id",
            "user_id",
            "created_at",
        ]
