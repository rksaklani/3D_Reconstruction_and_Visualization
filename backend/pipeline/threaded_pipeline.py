"""Threading-based reconstruction pipeline."""

import logging
import threading
import traceback
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

from backend.config import get_config
from backend.database import get_sync_database
from backend.services.minio_service import get_minio_service
from backend.services.colmap_service import get_colmap_service
from backend.pipeline.process_manager import ProcessManager

logger = logging.getLogger(__name__)


class ThreadedPipeline:
    """Threading-based 3D reconstruction pipeline."""
    
    def __init__(self):
        """Initialize threaded pipeline with all services."""
        logger.info("Initializing threaded pipeline...")
        
        # Load configuration
        self.config = get_config()
        
        # Initialize storage
        self.minio = get_minio_service()
        
        # Initialize COLMAP
        self.colmap = get_colmap_service()
        
        # Initialize process manager
        self.process_manager = ProcessManager()
        
        # Track active jobs and PIDs
        self.active_jobs: Dict[str, threading.Thread] = {}
        self.job_pids: Dict[str, int] = {}
        self._lock = threading.Lock()
        
        logger.info("✓ Threaded pipeline initialized")
    
    def start_job(self, job_id: str) -> None:
        """
        Start job in background thread.
        
        Args:
            job_id: Job identifier
            
        Raises:
            ValueError: If job is already running
        """
        with self._lock:
            if job_id in self.active_jobs:
                raise ValueError(f"Job already running: {job_id}")
            
            # Create and start thread
            thread = threading.Thread(
                target=self._process_job,
                args=(job_id,),
                daemon=True,
                name=f"job-{job_id}"
            )
            self.active_jobs[job_id] = thread
            thread.start()
            
            logger.info(f"Started job thread: {job_id}")
    
    def stop_job(self, job_id: str) -> None:
        """
        Stop running job.
        
        Terminates the process group and updates job status.
        
        Args:
            job_id: Job identifier
        """
        db = get_sync_database()
        
        # Get job from database
        job = db.jobs.find_one({"job_id": job_id})
        
        if job and job.get("pid"):
            try:
                self.process_manager.terminate_process_group(job["pid"])
            except Exception as e:
                logger.error(f"Error terminating process for job {job_id}: {e}")
        
        # Update status
        db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "stopped",
                "updated_at": datetime.utcnow(),
                "error": "Stopped by user"
            }}
        )
        
        # Remove from active jobs
        with self._lock:
            self.active_jobs.pop(job_id, None)
            self.job_pids.pop(job_id, None)
        
        logger.info(f"Stopped job: {job_id}")
    
    def _process_job(self, job_id: str) -> None:
        """
        Execute job in background thread (synchronous).
        
        This method runs in a background thread and executes all pipeline
        stages sequentially. It handles exceptions and updates job status.
        
        Args:
            job_id: Job identifier
        """
        try:
            logger.info(f"Processing job: {job_id}")
            
            # Get job from database
            db = get_sync_database()
            job = db.jobs.find_one({"job_id": job_id})
            
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            # Update status to processing
            self._update_job_status(job_id, "processing", "preprocessing", 0.0)
            
            # Stage 1: Preprocessing
            logger.info(f"Job {job_id}: Stage 1 - Preprocessing")
            preprocess_result = self._stage_preprocess(job)
            self._update_job_status(job_id, "processing", "sfm", 0.15)
            
            # Stage 2: Structure from Motion
            logger.info(f"Job {job_id}: Stage 2 - Structure from Motion")
            sfm_result = self._stage_sfm(job, preprocess_result)
            self._update_job_status(job_id, "processing", "ai_analysis", 0.35)
            
            # Stage 3: AI Scene Understanding
            logger.info(f"Job {job_id}: Stage 3 - AI Scene Understanding")
            ai_result = self._stage_ai_analysis(job, preprocess_result)
            self._update_job_status(job_id, "processing", "gaussian_training", 0.50)
            
            # Stage 4: Gaussian Splatting
            logger.info(f"Job {job_id}: Stage 4 - Gaussian Splatting")
            gaussian_result = self._stage_gaussian_training(job, sfm_result, ai_result)
            self._update_job_status(job_id, "processing", "export", 0.85)
            
            # Stage 5: Export
            logger.info(f"Job {job_id}: Stage 5 - Export")
            export_result = self._stage_export(job, sfm_result, ai_result, gaussian_result)
            self._update_job_status(job_id, "completed", "complete", 1.0)
            
            # Save results
            self._save_results(job_id, {
                'job_id': job_id,
                'status': 'completed',
                'preprocessing': preprocess_result,
                'sfm': sfm_result,
                'ai': ai_result,
                'gaussian': gaussian_result,
                'export': export_result
            })
            
            logger.info(f"✓ Job completed: {job_id}")
            
        except Exception as e:
            logger.error(f"Job failed: {job_id} - {e}")
            logger.error(traceback.format_exc())
            
            self._update_job_status(
                job_id, "failed", None, None,
                error=str(e),
                error_details=traceback.format_exc()
            )
        
        finally:
            # Cleanup
            with self._lock:
                self.active_jobs.pop(job_id, None)
                self.job_pids.pop(job_id, None)
    
    def _stage_preprocess(self, job: Dict) -> Dict:
        """
        Preprocessing stage.
        
        Downloads input files from MinIO and preprocesses them.
        """
        from backend.pipeline.preprocess import (
            ImageLoader, VideoDecoder, ImagePreprocessor, PreprocessConfig
        )
        import cv2
        
        job_id = job['job_id']
        user_id = job['user_id']
        
        # Create job workspace
        job_temp_dir = Path(f"/tmp/reconstruction_jobs/{job_id}")
        local_dir = job_temp_dir / "input"
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Download input files from MinIO
        image_paths = []
        for object_name in job['input_files']:
            filename = Path(object_name).name
            local_path = local_dir / filename
            
            data = self.minio.download_data(object_name)
            local_path.write_bytes(data)
            image_paths.append(str(local_path))
        
        # Initialize preprocessing components
        image_loader = ImageLoader(min_images=3)
        video_decoder = VideoDecoder(sampling_rate=1)
        preprocessor = ImagePreprocessor(PreprocessConfig(
            resize_enabled=False,
            normalize_enabled=True,
            denoise_enabled=False,
            blur_detection_enabled=True,
            blur_threshold=100.0
        ))
        
        # Load images or extract frames
        if job['input_type'] == 'video':
            video_path = image_paths[0]
            frames = video_decoder.extract_frames(video_path)
            images = [(frame, idx) for frame, idx in frames]
        else:
            images = image_loader.load_images(image_paths)
        
        # Filter blurry images
        images = preprocessor.filter_blurry_images(images)
        
        # Save preprocessed images
        preprocessed_dir = job_temp_dir / "preprocessed"
        preprocessed_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (image, metadata) in enumerate(images):
            output_path = preprocessed_dir / f"image_{i:04d}.jpg"
            cv2.imwrite(str(output_path), image)
        
        return {
            'num_images': len(images),
            'preprocessed_dir': str(preprocessed_dir),
            'image_paths': [str(preprocessed_dir / f"image_{i:04d}.jpg") for i in range(len(images))],
            'temp_dir': str(job_temp_dir)
        }
    
    def _stage_sfm(self, job: Dict, preprocess_result: Dict) -> Dict:
        """
        Structure from Motion stage.
        
        Runs COLMAP SfM using ProcessManager for subprocess execution.
        """
        job_id = job['job_id']
        
        # Prepare COLMAP workspace
        job_temp_dir = Path(preprocess_result['temp_dir'])
        workspace_dir = job_temp_dir / "colmap"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        image_dir = Path(preprocess_result['preprocessed_dir'])
        log_path = job_temp_dir / "live.log"
        
        try:
            # Run COLMAP pipeline with GPU acceleration
            logger.info(f"Running COLMAP SfM on {image_dir}")
            
            # Use sequential matcher for videos (faster), exhaustive for image sets
            matcher = "sequential" if job['input_type'] == 'video' else "exhaustive"
            
            result = self.colmap.run_sfm(
                image_dir=str(image_dir),
                output_dir=str(workspace_dir),
                camera_model="SIMPLE_RADIAL",
                single_camera=False,
                gpu_index=0,
                matcher=matcher
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
            
            return {
                'num_cameras': 0,
                'num_images': preprocess_result['num_images'],
                'num_points': 0,
                'sparse_dir': None,
                'workspace_dir': str(workspace_dir),
                'error': str(e)
            }
    
    def _stage_ai_analysis(self, job: Dict, preprocess_result: Dict) -> Dict:
        """
        AI scene understanding stage.
        
        Performs object detection, segmentation, and scene classification.
        """
        import cv2
        
        # Lazy-load AI services
        try:
            from ai.detection.yolo import YOLODetector
            from ai.segmentation.sam import SAMSegmenter
            from ai.tracking.object_tracker import ObjectTracker
            from ai.classification.scene_classifier import SceneClassifier
            
            detector = YOLODetector()
            segmenter = SAMSegmenter()
            tracker = ObjectTracker()
            classifier = SceneClassifier()
        except Exception as e:
            logger.warning(f"AI services not available: {e}")
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
        
        # Load sample images for analysis
        sample_images = []
        for path in image_paths[:5]:
            img = cv2.imread(path)
            if img is not None:
                sample_images.append(img)
        
        if not sample_images:
            return {'error': 'No images to analyze'}
        
        # Object detection
        all_detections = []
        for img in sample_images:
            detections = detector.detect(img)
            all_detections.extend(detections)
        
        # Scene classification
        scene_results = classifier.classify_batch(sample_images)
        
        # Segmentation on first image
        masks = segmenter.segment(sample_images[0]) if sample_images else []
        
        # Object tracking
        tracks = []
        if len(sample_images) > 1:
            for img in sample_images:
                detections = detector.detect(img)
                tracks = tracker.update(detections, img)
        
        return {
            'num_detections': len(all_detections),
            'detections': [
                {
                    'bbox': det['bbox'],
                    'confidence': float(det['confidence']),
                    'class': det['class']
                }
                for det in all_detections[:10]
            ],
            'scene_classification': {
                'top_class': scene_results[0]['predictions'][0]['class'],
                'confidence': float(scene_results[0]['predictions'][0]['confidence'])
            },
            'num_masks': len(masks),
            'num_tracks': len(tracks)
        }
    
    def _stage_gaussian_training(
        self,
        job: Dict,
        sfm_result: Dict,
        ai_result: Dict
    ) -> Dict:
        """
        Gaussian Splatting training stage.
        
        Placeholder for Gaussian Splatting integration.
        """
        # This would integrate with actual Gaussian Splatting implementation
        # For now, return placeholder
        return {
            'status': 'placeholder',
            'message': 'Gaussian Splatting training not yet implemented',
            'num_gaussians': 0
        }
    
    def _stage_export(
        self,
        job: Dict,
        sfm_result: Dict,
        ai_result: Dict,
        gaussian_result: Dict
    ) -> Dict:
        """
        Export results stage.
        
        Exports results and uploads to MinIO.
        """
        import json
        import shutil
        
        job_id = job['job_id']
        user_id = job['user_id']
        
        # Create export directory
        job_temp_dir = Path(f"/tmp/reconstruction_jobs/{job_id}")
        export_dir = job_temp_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export SfM results
        export_files = {}
        
        if sfm_result.get('sparse_dir'):
            sparse_export = export_dir / "sparse"
            if Path(sfm_result['sparse_dir']).exists():
                shutil.copytree(sfm_result['sparse_dir'], sparse_export, dirs_exist_ok=True)
                export_files['sparse'] = str(sparse_export)
        
        # Export AI results as JSON
        ai_export = export_dir / "ai_results.json"
        with open(ai_export, 'w') as f:
            json.dump(ai_result, f, indent=2)
        export_files['ai_results'] = str(ai_export)
        
        # Export reconstruction summary
        summary = {
            'job_id': job_id,
            'status': 'completed',
            'reconstruction': {
                'num_cameras': sfm_result.get('num_cameras', 0),
                'num_images': sfm_result.get('num_images', 0),
                'num_points': sfm_result.get('num_points', 0),
                'mean_error': sfm_result.get('mean_error', 0.0),
                'sparse_dir': sfm_result.get('sparse_dir')
            },
            'ai_analysis': {
                'num_detections': ai_result.get('num_detections', 0),
                'skipped': ai_result.get('skipped', False)
            },
            'gaussian_splatting': gaussian_result
        }
        
        summary_export = export_dir / "reconstruction_summary.json"
        with open(summary_export, 'w') as f:
            json.dump(summary, f, indent=2)
        export_files['summary'] = str(summary_export)
        
        # Upload exports to MinIO
        uploaded_files = {}
        for file_type, file_path in export_files.items():
            file_path_obj = Path(file_path)
            
            if file_path_obj.is_file():
                # Upload single file
                object_name = f"{user_id}/{job_id}/output/{file_path_obj.name}"
                with open(file_path_obj, 'rb') as f:
                    self.minio.upload_data(f.read(), object_name)
                uploaded_files[file_type] = object_name
                
            elif file_path_obj.is_dir():
                # Upload directory contents
                uploaded_count = 0
                for file in file_path_obj.rglob('*'):
                    if file.is_file():
                        # Create relative path for MinIO
                        rel_path = file.relative_to(export_dir)
                        object_name = f"{user_id}/{job_id}/output/{rel_path}"
                        
                        with open(file, 'rb') as f:
                            self.minio.upload_data(f.read(), object_name)
                        uploaded_count += 1
                
                if uploaded_count > 0:
                    uploaded_files[file_type] = f"{user_id}/{job_id}/output/{file_path_obj.name}/ ({uploaded_count} files)"
        
        # Update job with output files
        db = get_sync_database()
        db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"output_files": uploaded_files}}
        )
        
        # Cleanup local files after successful upload to MinIO
        logger.info(f"Cleaning up local files for job {job_id}")
        try:
            # Keep only the live.log file, delete everything else
            if job_temp_dir.exists():
                # Calculate total size before cleanup
                total_size = sum(f.stat().st_size for f in job_temp_dir.rglob('*') if f.is_file())
                
                # Delete input files (already in MinIO)
                input_dir = job_temp_dir / "input"
                if input_dir.exists():
                    shutil.rmtree(input_dir)
                    logger.info(f"  Deleted input directory")
                
                # Delete preprocessed images (can be regenerated)
                preprocessed_dir = job_temp_dir / "preprocessed"
                if preprocessed_dir.exists():
                    shutil.rmtree(preprocessed_dir)
                    logger.info(f"  Deleted preprocessed directory")
                
                # Delete COLMAP database (large, already processed)
                colmap_dir = job_temp_dir / "colmap"
                if colmap_dir.exists():
                    # Keep sparse reconstruction, delete database
                    db_file = colmap_dir / "database.db"
                    if db_file.exists():
                        db_file.unlink()
                        logger.info(f"  Deleted COLMAP database ({db_file.stat().st_size / (1024**3):.2f} GB)")
                    
                    # Delete sparse reconstruction (already in MinIO)
                    sparse_dir = colmap_dir / "0"
                    if sparse_dir.exists():
                        shutil.rmtree(sparse_dir)
                        logger.info(f"  Deleted sparse reconstruction")
                
                # Delete export directory (already in MinIO)
                if export_dir.exists():
                    shutil.rmtree(export_dir)
                    logger.info(f"  Deleted export directory")
                
                # Calculate remaining size
                remaining_size = sum(f.stat().st_size for f in job_temp_dir.rglob('*') if f.is_file())
                freed_space = total_size - remaining_size
                
                logger.info(f"Cleanup complete: freed {freed_space / (1024**2):.2f} MB")
                logger.info(f"Remaining files: {remaining_size / (1024**2):.2f} MB (logs only)")
                
        except Exception as e:
            logger.warning(f"Cleanup failed (non-critical): {e}")
        
        return {
            'export_dir': str(export_dir),
            'files': uploaded_files,
            'cleanup': 'completed'
        }
    
    def _update_job_status(
        self,
        job_id: str,
        status: str,
        stage: Optional[str],
        progress: Optional[float],
        error: Optional[str] = None,
        error_details: Optional[str] = None
    ):
        """Update job status in database."""
        db = get_sync_database()
        
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
        
        # Set started_at on first processing update
        if status == "processing":
            job = db.jobs.find_one({"job_id": job_id})
            if job and not job.get("started_at"):
                update_data["started_at"] = datetime.utcnow()
        
        # Set completed_at on completion
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow()
        
        db.jobs.update_one(
            {"job_id": job_id},
            {"$set": update_data}
        )
        
        logger.info(f"Job {job_id}: {status} - {stage} ({progress*100 if progress else 0:.1f}%)")
    
    def _save_results(self, job_id: str, results: Dict):
        """Save results to database."""
        db = get_sync_database()
        
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
        db.results.update_one(
            {"job_id": job_id},
            {"$set": result_doc},
            upsert=True
        )


# Singleton instance
_pipeline_instance = None
_pipeline_lock = threading.Lock()


def get_threaded_pipeline() -> ThreadedPipeline:
    """Get singleton pipeline instance (thread-safe)."""
    global _pipeline_instance
    
    if _pipeline_instance is None:
        with _pipeline_lock:
            # Double-check locking pattern
            if _pipeline_instance is None:
                _pipeline_instance = ThreadedPipeline()
    
    return _pipeline_instance
