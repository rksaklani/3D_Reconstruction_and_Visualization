"""
Error handling and recovery service for the 3D reconstruction pipeline.
Provides centralized error handling, recovery strategies, and user-friendly error messages.
"""

import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum
import traceback

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur in the pipeline."""
    INPUT_VALIDATION = "input_validation"
    FEATURE_MATCHING = "feature_matching"
    BUNDLE_ADJUSTMENT = "bundle_adjustment"
    AI_MODEL_LOADING = "ai_model_loading"
    GAUSSIAN_TRAINING = "gaussian_training"
    MESH_EXTRACTION = "mesh_extraction"
    GPU_MEMORY = "gpu_memory"
    FILE_IO = "file_io"
    SHADER_COMPILATION = "shader_compilation"
    NETWORK = "network"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.ABORT,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.recovery_strategy = recovery_strategy
        self.details = details or {}


class ErrorHandler:
    """Centralized error handler for the pipeline."""
    
    def __init__(self):
        self.error_handlers: Dict[ErrorType, Callable] = {
            ErrorType.INPUT_VALIDATION: self._handle_input_validation_error,
            ErrorType.FEATURE_MATCHING: self._handle_feature_matching_error,
            ErrorType.BUNDLE_ADJUSTMENT: self._handle_bundle_adjustment_error,
            ErrorType.AI_MODEL_LOADING: self._handle_ai_model_loading_error,
            ErrorType.GAUSSIAN_TRAINING: self._handle_gaussian_training_error,
            ErrorType.MESH_EXTRACTION: self._handle_mesh_extraction_error,
            ErrorType.GPU_MEMORY: self._handle_gpu_memory_error,
            ErrorType.FILE_IO: self._handle_file_io_error,
            ErrorType.SHADER_COMPILATION: self._handle_shader_compilation_error,
        }
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return recovery information.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Dictionary with error information and recovery strategy
        """
        context = context or {}
        
        # Log the error with full context
        logger.error(
            f"Pipeline error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "context": context,
                "traceback": traceback.format_exc()
            }
        )
        
        # Handle PipelineError with specific recovery strategy
        if isinstance(error, PipelineError):
            handler = self.error_handlers.get(error.error_type)
            if handler:
                return handler(error, context)
        
        # Default error handling
        return {
            "success": False,
            "error_type": ErrorType.UNKNOWN.value,
            "message": str(error),
            "user_message": "An unexpected error occurred. Please try again.",
            "recovery_strategy": RecoveryStrategy.ABORT.value,
            "details": context
        }
    
    def _handle_input_validation_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle input validation errors (Requirement 17.1)."""
        image_count = context.get("image_count", 0)
        
        if image_count < 3:
            return {
                "success": False,
                "error_type": ErrorType.INPUT_VALIDATION.value,
                "message": error.message,
                "user_message": f"Insufficient images provided. At least 3 images are required, but only {image_count} were provided.",
                "recovery_strategy": RecoveryStrategy.ABORT.value,
                "suggestions": [
                    "Upload at least 3 images",
                    "Ensure images have sufficient overlap",
                    "Use high-quality, non-blurry images"
                ]
            }
        
        return {
            "success": False,
            "error_type": ErrorType.INPUT_VALIDATION.value,
            "message": error.message,
            "user_message": "Input validation failed. Please check your files.",
            "recovery_strategy": RecoveryStrategy.ABORT.value
        }
    
    def _handle_feature_matching_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle feature matching errors (Requirement 17.2)."""
        disconnected_components = context.get("disconnected_components", [])
        
        return {
            "success": False,
            "error_type": ErrorType.FEATURE_MATCHING.value,
            "message": error.message,
            "user_message": "Feature matching failed. The match graph is disconnected.",
            "recovery_strategy": RecoveryStrategy.ABORT.value,
            "details": {
                "disconnected_components": disconnected_components
            },
            "suggestions": [
                "Add bridging images between disconnected groups",
                "Ensure images have sufficient overlap (>30%)",
                "Check that images are from the same scene"
            ]
        }
    
    def _handle_bundle_adjustment_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle bundle adjustment errors (Requirement 17.3, 17.4)."""
        attempt = context.get("attempt", 1)
        max_attempts = context.get("max_attempts", 3)
        
        if attempt < max_attempts:
            return {
                "success": False,
                "error_type": ErrorType.BUNDLE_ADJUSTMENT.value,
                "message": error.message,
                "user_message": f"Bundle adjustment failed (attempt {attempt}/{max_attempts}). Retrying with conservative parameters...",
                "recovery_strategy": RecoveryStrategy.RETRY.value,
                "retry_params": {
                    "max_iterations": 50,  # Reduced from default
                    "function_tolerance": 1e-4,  # More lenient
                    "use_robust_loss": True
                }
            }
        else:
            return {
                "success": False,
                "error_type": ErrorType.BUNDLE_ADJUSTMENT.value,
                "message": error.message,
                "user_message": "Bundle adjustment failed after multiple attempts. Using initial SfM result.",
                "recovery_strategy": RecoveryStrategy.FALLBACK.value,
                "fallback_action": "use_initial_sfm"
            }
    
    def _handle_ai_model_loading_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle AI model loading errors (Requirement 17.8)."""
        model_name = context.get("model_name", "unknown")
        attempt = context.get("attempt", 1)
        
        if attempt == 1:
            return {
                "success": False,
                "error_type": ErrorType.AI_MODEL_LOADING.value,
                "message": error.message,
                "user_message": f"Failed to load {model_name}. Attempting automatic download...",
                "recovery_strategy": RecoveryStrategy.RETRY.value,
                "retry_action": "download_model"
            }
        elif attempt == 2:
            return {
                "success": False,
                "error_type": ErrorType.AI_MODEL_LOADING.value,
                "message": error.message,
                "user_message": f"Failed to load {model_name}. Trying smaller model or CPU inference...",
                "recovery_strategy": RecoveryStrategy.FALLBACK.value,
                "fallback_action": "use_smaller_model_or_cpu"
            }
        else:
            return {
                "success": False,
                "error_type": ErrorType.AI_MODEL_LOADING.value,
                "message": error.message,
                "user_message": "AI model loading failed. Proceeding without AI scene understanding.",
                "recovery_strategy": RecoveryStrategy.SKIP.value,
                "skip_stage": "ai_understanding"
            }
    
    def _handle_gaussian_training_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle Gaussian training errors (Requirement 17.5)."""
        checkpoint_available = context.get("checkpoint_available", False)
        
        if checkpoint_available:
            return {
                "success": False,
                "error_type": ErrorType.GAUSSIAN_TRAINING.value,
                "message": error.message,
                "user_message": "Gaussian training became unstable. Restoring from checkpoint and reducing learning rate...",
                "recovery_strategy": RecoveryStrategy.RETRY.value,
                "retry_params": {
                    "restore_checkpoint": True,
                    "learning_rate_scale": 0.5,
                    "enable_gradient_clipping": True
                }
            }
        else:
            return {
                "success": False,
                "error_type": ErrorType.GAUSSIAN_TRAINING.value,
                "message": error.message,
                "user_message": "Gaussian training failed. This may affect rendering quality.",
                "recovery_strategy": RecoveryStrategy.ABORT.value
            }
    
    def _handle_mesh_extraction_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle mesh extraction errors (Requirement 17.11)."""
        object_id = context.get("object_id", "unknown")
        
        return {
            "success": False,
            "error_type": ErrorType.MESH_EXTRACTION.value,
            "message": error.message,
            "user_message": f"Mesh extraction failed for object {object_id}. Using pure Gaussian representation.",
            "recovery_strategy": RecoveryStrategy.FALLBACK.value,
            "fallback_action": "use_gaussian_only",
            "details": {
                "object_id": object_id,
                "editable": False
            }
        }
    
    def _handle_gpu_memory_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle GPU memory exhaustion (Requirement 17.7, 17.12)."""
        return {
            "success": False,
            "error_type": ErrorType.GPU_MEMORY.value,
            "message": error.message,
            "user_message": "GPU memory exhausted. Reducing rendering resolution and enabling LOD culling...",
            "recovery_strategy": RecoveryStrategy.RETRY.value,
            "retry_params": {
                "reduce_resolution": True,
                "enable_lod": True,
                "reduce_gaussian_count": True
            },
            "suggestions": [
                "Reduce rendering quality",
                "Enable LOD culling",
                "Use fewer Gaussians",
                "Close other GPU-intensive applications"
            ]
        }
    
    def _handle_file_io_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle file I/O errors (Requirement 17.6)."""
        file_path = context.get("file_path", "unknown")
        operation = context.get("operation", "unknown")
        
        return {
            "success": False,
            "error_type": ErrorType.FILE_IO.value,
            "message": error.message,
            "user_message": f"File {operation} failed for {file_path}.",
            "recovery_strategy": RecoveryStrategy.ABORT.value,
            "suggestions": [
                "Check file permissions",
                "Ensure sufficient disk space",
                "Verify the file path is correct",
                "Try an alternative output location"
            ]
        }
    
    def _handle_shader_compilation_error(
        self,
        error: PipelineError,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle shader compilation errors (Requirement 17.12)."""
        shader_name = context.get("shader_name", "unknown")
        
        return {
            "success": False,
            "error_type": ErrorType.SHADER_COMPILATION.value,
            "message": error.message,
            "user_message": f"Shader compilation failed for {shader_name}. Falling back to simplified shaders.",
            "recovery_strategy": RecoveryStrategy.FALLBACK.value,
            "fallback_action": "use_simplified_shaders",
            "suggestions": [
                "Update graphics drivers",
                "Check GPU compatibility",
                "Try a different browser (for WebGL shaders)"
            ]
        }


# Global error handler instance
error_handler = ErrorHandler()
