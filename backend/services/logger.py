"""
Logging and monitoring service for the 3D reconstruction pipeline.
Provides structured logging, performance metrics, and health monitoring.
"""

import logging
import logging.handlers
import time
import psutil
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class PipelineLogger:
    """Centralized logger for the pipeline with structured logging."""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup root logger
        self.logger = logging.getLogger("pipeline")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # File handler with rotation (Requirement 22.8)
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "pipeline.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter with timestamps (Requirement 22.1)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_stage_transition(
        self,
        job_id: str,
        from_stage: str,
        to_stage: str
    ) -> None:
        """Log pipeline stage transitions (Requirement 22.1)."""
        self.logger.info(
            f"Job {job_id}: Stage transition {from_stage} -> {to_stage}",
            extra={
                "job_id": job_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_error(
        self,
        job_id: str,
        stage: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log errors with full context (Requirement 22.2)."""
        import traceback
        
        self.logger.error(
            f"Job {job_id}: Error in stage {stage}: {str(error)}",
            extra={
                "job_id": job_id,
                "stage": stage,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_performance(
        self,
        job_id: str,
        stage: str,
        duration: float,
        memory_mb: Optional[float] = None,
        gpu_memory_mb: Optional[float] = None
    ) -> None:
        """Log performance metrics (Requirement 22.3)."""
        metrics = {
            "job_id": job_id,
            "stage": stage,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        if memory_mb is not None:
            metrics["memory_mb"] = memory_mb
        
        if gpu_memory_mb is not None:
            metrics["gpu_memory_mb"] = gpu_memory_mb
        
        self.logger.info(
            f"Job {job_id}: Stage {stage} completed in {duration:.2f}s",
            extra=metrics
        )
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log user actions (Requirement 22.4)."""
        self.logger.info(
            f"User {user_id}: {action}",
            extra={
                "user_id": user_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        )


class PerformanceMonitor:
    """Monitor system performance and resource usage."""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        return self.process.cpu_percent(interval=0.1)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        return {
            "memory_mb": self.get_memory_usage(),
            "cpu_percent": self.get_cpu_percent(),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }


class HealthMonitor:
    """Health check endpoint for monitoring (Requirement 22.5)."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for monitoring systems."""
        uptime = time.time() - self.start_time
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format (Requirement 22.6)."""
        monitor = PerformanceMonitor()
        metrics = monitor.get_system_metrics()
        
        prometheus_format = f"""
# HELP pipeline_memory_usage_mb Memory usage in megabytes
# TYPE pipeline_memory_usage_mb gauge
pipeline_memory_usage_mb {metrics['memory_mb']}

# HELP pipeline_cpu_percent CPU usage percentage
# TYPE pipeline_cpu_percent gauge
pipeline_cpu_percent {metrics['cpu_percent']}

# HELP pipeline_disk_usage_percent Disk usage percentage
# TYPE pipeline_disk_usage_percent gauge
pipeline_disk_usage_percent {metrics['disk_usage_percent']}

# HELP pipeline_uptime_seconds Uptime in seconds
# TYPE pipeline_uptime_seconds counter
pipeline_uptime_seconds {time.time() - self.start_time}
"""
        return prometheus_format.strip()


# Global instances
pipeline_logger = PipelineLogger()
health_monitor = HealthMonitor()
