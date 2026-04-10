"""Integrated pipeline connecting all components."""

import logging
import asyncio
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
import traceback

# Configuration
from backend.config import get_config

# Database
from backend.database import get_database

# Storage
from backend.services.minio_service import get_minio_service

# Preprocessing
from backend.pipeline.preprocess import (
    ImageLoader, VideoDecoder, ImagePreprocessor, PreprocessConfig
)

# COLMAP/SfM
from backend.services.colmap_service import get_colmap_service

# AI Services
from ai.detection.yolo import YOLODetector
from ai.segmentation.sam import SAMSegmenter
from ai.tracking.object_tracker import ObjectTracker
from ai.classification.scene_classifier import SceneClassifier

# Pipeline stages
from backend.pipeline.gaussian_splatting import GaussianSplattingTrainer
from backend.pipeline.export import ExportManager

logger = logging.getLogger(__name__)


class IntegratedPipeline:
    """Complete integrated 3D reconstruction pipeline."""
    
    def __init__(self):
        """Initialize integrated pipeline with all services."""
        logger.info("Initializing integrated pipeline...")
        
        # Load configuration (returns Config object, not dict)
        self.config = get_config()
        
        # Initialize storage
        self.minio = get_minio_service()
        
        # Initialize preprocessing
        self.image_loader = ImageLoader(min_images=3)
        self.video_decoder = VideoDecoder(sampling_rate=1)
        self.preprocessor = ImagePreprocessor(PreprocessConfig(
            resize_enabled=False,
            normalize_enabled=True,
            denoise_enabled=False,
            blur_detection_enabled=True,
            blur_threshold=100.0
        ))
        
        # Initialize COLMAP (required for SfM)
        self.colmap = get_colmap_service()
        logger.info("✓ COLMAP service initialized")
        
        # Initialize AI services (lazy-loaded to avoid CUDA errors at startup)
        self.detector = None
        self.segmenter = None
        self.tracker = None
        self.classifier = None
        
        # Initialize export manager (config is not a dict, use empty dict)
        self.export_manager = ExportManager({})
        
        logger.info("✓ Integrated pipeline initialized")
    
    def _init_ai_services(self):
        """Lazy initialization of AI services."""
        if self.detector is not None:
            return  # Already initialized
        
        try:
            logger.info("Initializing AI services...")
            self.detector = YOLODetector()
            self.segmenter = SAMSegmenter()
            self.tracker = ObjectTracker()
            self.classifier = SceneClassifier()
            logger.info("✓ AI services initialized")
        except Exception as e:
            logger.warning(f"AI services not available: {e}")
            # Create dummy services that return empty results
            self.detector = None
            self.segmenter = None
            self.tracker = None
            self.classifier = None
    
    async def process_job_async(self, job_id: str):
        """
        Async wrapper for process_job to run in background tasks.
        
        Args:
            job_id: Job identifier
        """
        try:
            result = await self.process_job(job_id)
            return result
        except Exception as e:
            logger.error(f"Background task failed for job {job_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def process_job(self, job_id: str) -> Dict:
        """
        Process a complete reconstruction job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Processing results
        """
        logger.info(f"Starting job processing: {job_id}")
        
        db = get_database()
        
        try:
            # Get job from database
            job = await db.jobs.find_one({"job_id": job_id})
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            # Update status
            await self._update_job_status(job_id, "processing", "preprocessing", 0.0)
            
            # Stage 1: Download and preprocess input
            logger.info("Stage 1: Preprocessing")
            preprocess_result = await self._stage_preprocess(job)
            await self._update_job_status(job_id, "processing", "sfm", 0.15)
            
            # Stage 2: Structure from Motion
            logger.info("Stage 2: Structure from Motion")
            sfm_result = await self._stage_sfm(job, preprocess_result)
            await self._update_job_status(job_id, "processing", "ai_analysis", 0.35)
            
            # Stage 3: AI Scene Understanding
            logger.info("Stage 3: AI Scene Understanding")
            ai_result = await self._stage_ai_analysis(job, preprocess_result)
            await self._update_job_status(job_id, "processing", "gaussian_training", 0.50)
            
            # Stage 4: Gaussian Splatting (placeholder)
            logger.info("Stage 4: Gaussian Splatting (placeholder)")
            gaussian_result = await self._stage_gaussian_training(job, sfm_result, ai_result)
            await self._update_job_status(job_id, "processing", "export", 0.85)
            
            # Stage 5: Export results
            logger.info("Stage 5: Export")
            export_result = await self._stage_export(job, sfm_result, ai_result, gaussian_result)
            await self._update_job_status(job_id, "completed", "complete", 1.0)
            
            # Compile final results
            results = {
                'job_id': job_id,
                'status': 'completed',
                'preprocessing': preprocess_result,
                'sfm': sfm_result,
                'ai': ai_result,
                'gaussian': gaussian_result,
                'export': export_result
            }
            
            # Save results to database
            await self._save_results(job_id, results)
            
            logger.info(f"✓ Job completed: {job_id}")
            return results
            
        except Exception as e:
            logger.error(f"Job failed: {job_id} - {e}")
            logger.error(traceback.format_exc())
            
            await self._update_job_status(
                job_id, "failed", None, None,
                error=str(e),
                error_details=traceback.format_exc()
            )
            
            raise
    
    async def _stage_preprocess(self, job: Dict) -> Dict:
        """Preprocessing stage."""
        job_id = job['job_id']
        user_id = job['user_id']
        
        # Use temporary directory for this job (not hardcoded workspace)
        job_temp_dir = Path(f"/tmp/reconstruction_jobs/{job_id}")
        local_dir = job_temp_dir / "input"
        local_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = []
        for object_name in job['input_files']:
            filename = Path(object_name).name
            local_path = local_dir / filename
            
            # Download from MinIO
            data = self.minio.download_data(object_name)
            local_path.write_bytes(data)
            image_paths.append(str(local_path))
        
        # Load images
        if job['input_type'] == 'video':
            # Extract frames from video
            video_path = image_paths[0]
            frames = self.video_decoder.extract_frames(video_path)
            images = [(frame, idx) for frame, idx in frames]
        else:
            # Load images
            images = self.image_loader.load_images(image_paths)
        
        # Filter blurry images
        images = self.preprocessor.filter_blurry_images(images)
        
        # Save preprocessed images
        preprocessed_dir = job_temp_dir / "preprocessed"
        preprocessed_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (image, metadata) in enumerate(images):
            output_path = preprocessed_dir / f"image_{i:04d}.jpg"
            import cv2
            cv2.imwrite(str(output_path), image)
        
        return {
            'num_images': len(images),
            'preprocessed_dir': str(preprocessed_dir),
            'image_paths': [str(preprocessed_dir / f"image_{i:04d}.jpg") for i in range(len(images))],
            'temp_dir': str(job_temp_dir)
        }
    
    async def _stage_sfm(self, job: Dict, preprocess_result: Dict) -> Dict:
        """Structure from Motion stage."""
        job_id = job['job_id']
        
        # Prepare COLMAP workspace in temp directory
        job_temp_dir = Path(preprocess_result['temp_dir'])
        workspace_dir = job_temp_dir / "colmap"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        image_dir = Path(preprocess_result['preprocessed_dir'])
        
        try:
            # Run COLMAP pipeline (GPU-accelerated)
            logger.info(f"Running COLMAP SfM on {image_dir}")
            logger.info(f"Using COLMAP binary: {self.colmap.colmap_bin}")
            
            result = self.colmap.run_sfm(
                image_dir=str(image_dir),
                output_dir=str(workspace_dir),
                camera_model="SIMPLE_RADIAL",
                single_camera=False,
                gpu_index=0
            )
            
            sparse_dir = workspace_dir / "0"
            
            return {
                'num_cameras': result.num_cameras,
                'num_images': result.num_images,
                'num_points': result.num_points,
                'mean_error': result.mean_reprojection_error,
                'sparse_dir': str(sparse_dir),
                'workspace_dir': str(workspace_dir)
            }
            
        except Exception as e:
            logger.error(f"COLMAP failed: {e}")
            logger.error(traceback.format_exc())
            # Return placeholder results
            return {
                'num_cameras': 0,
                'num_images': preprocess_result['num_images'],
                'num_points': 0,
                'sparse_dir': None,
                'workspace_dir': str(workspace_dir),
                'error': str(e)
            }
    
    async def _stage_ai_analysis(self, job: Dict, preprocess_result: Dict) -> Dict:
        """AI scene understanding stage."""
        import cv2
        import numpy as np
        
        # Initialize AI services (lazy-loaded)
        self._init_ai_services()
        
        # Check if AI services are available
        if self.detector is None:
            logger.warning("AI services not available, skipping AI analysis")
            return {
                'skipped': True,
                'reason': 'AI services not available (CUDA/GPU required)',
                'num_detections': 0,
                'detections': [],
                'scene_classification': {},
                'num_masks': 0,
                'num_tracks': 0
            }
        
        image_paths = preprocess_result['image_paths']
        
        # Load first few images for analysis
        sample_images = []
        for path in image_paths[:5]:  # Analyze first 5 images
            img = cv2.imread(path)
            if img is not None:
                sample_images.append(img)
        
        if not sample_images:
            return {'error': 'No images to analyze'}
        
        # Object detection
        all_detections = []
        for img in sample_images:
            detections = self.detector.detect(img)
            all_detections.extend(detections)
        
        # Scene classification
        scene_results = self.classifier.classify_batch(sample_images)
        
        # Segmentation on first image
        if sample_images:
            masks = self.segmenter.segment(sample_images[0])
        else:
            masks = []
        
        # Object tracking (if multiple images)
        tracks = []
        if len(sample_images) > 1:
            for img in sample_images:
                detections = self.detector.detect(img)
                tracks = self.tracker.update(detections, img)
        
        return {
            'num_detections': len(all_detections),
            'detections': [
                {
                    'bbox': det['bbox'],
                    'confidence': float(det['confidence']),
                    'class': det['class']
                }
                for det in all_detections[:10]  # Top 10
            ],
            'scene_classification': {
                'top_class': scene_results[0]['predictions'][0]['class'],
                'confidence': float(scene_results[0]['predictions'][0]['confidence'])
            },
            'num_masks': len(masks),
            'num_tracks': len(tracks)
        }
    
    async def _stage_gaussian_training(
        self,
        job: Dict,
        sfm_result: Dict,
        ai_result: Dict
    ) -> Dict:
        """Gaussian Splatting training stage (placeholder)."""
        # This would integrate with actual Gaussian Splatting implementation
        # For now, return placeholder
        return {
            'status': 'placeholder',
            'message': 'Gaussian Splatting training not yet implemented',
            'num_gaussians': 0
        }
    
    async def _stage_export(
        self,
        job: Dict,
        sfm_result: Dict,
        ai_result: Dict,
        gaussian_result: Dict
    ) -> Dict:
        """Export results stage."""
        job_id = job['job_id']
        user_id = job['user_id']
        
        # Create export directory in temp workspace
        job_temp_dir = Path(f"/tmp/reconstruction_jobs/{job_id}")
        export_dir = job_temp_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export SfM results (if available)
        export_files = {}
        
        if sfm_result.get('sparse_dir'):
            # Copy sparse reconstruction
            import shutil
            sparse_export = export_dir / "sparse"
            if Path(sfm_result['sparse_dir']).exists():
                shutil.copytree(sfm_result['sparse_dir'], sparse_export, dirs_exist_ok=True)
                export_files['sparse'] = str(sparse_export)
        
        # Export AI results as JSON
        import json
        ai_export = export_dir / "ai_results.json"
        with open(ai_export, 'w') as f:
            json.dump(ai_result, f, indent=2)
        export_files['ai_results'] = str(ai_export)
        
        # Upload exports to MinIO
        uploaded_files = {}
        for file_type, file_path in export_files.items():
            if Path(file_path).is_file():
                object_name = f"{user_id}/{job_id}/output/{Path(file_path).name}"
                with open(file_path, 'rb') as f:
                    self.minio.upload_data(f.read(), object_name)
                uploaded_files[file_type] = object_name
        
        # Update job with output files
        db = get_database()
        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"output_files": uploaded_files}}
        )
        
        return {
            'export_dir': str(export_dir),
            'files': uploaded_files
        }
    
    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        stage: Optional[str],
        progress: Optional[float],
        error: Optional[str] = None,
        error_details: Optional[str] = None
    ):
        """Update job status in database."""
        db = get_database()
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if stage is not None:
            update_data["stage"] = stage
        
        if progress is not None:
            update_data["progress"] = progress
        
        if error is not None:
            update_data["error"] = error
        
        if error_details is not None:
            update_data["error_details"] = error_details
        
        if status == "processing" and "started_at" not in update_data:
            job = await db.jobs.find_one({"job_id": job_id})
            if job and not job.get("started_at"):
                update_data["started_at"] = datetime.utcnow()
        
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        logger.info(f"Job {job_id}: {status} - {stage} ({progress*100 if progress else 0:.1f}%)")
    
    async def _save_results(self, job_id: str, results: Dict):
        """Save results to database."""
        db = get_database()
        
        result_doc = {
            'job_id': job_id,
            'created_at': datetime.utcnow(),
            'num_cameras': results.get('sfm', {}).get('num_cameras', 0),
            'num_images': results.get('preprocessing', {}).get('num_images', 0),
            'num_points': results.get('sfm', {}).get('num_points', 0),
            'num_gaussians': results.get('gaussian', {}).get('num_gaussians', 0),
            'detected_objects': results.get('ai', {}).get('detections', []),
            'scene_classification': results.get('ai', {}).get('scene_classification', {}),
            'files': results.get('export', {}).get('files', {})
        }
        
        # Upsert result
        await db.results.update_one(
            {"job_id": job_id},
            {"$set": result_doc},
            upsert=True
        )


# Singleton instance
_pipeline_instance = None


def get_integrated_pipeline() -> IntegratedPipeline:
    """Get singleton pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = IntegratedPipeline()
    return _pipeline_instance
