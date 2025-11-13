"""
Custom exception classes for UniRig UI backend.
Provides structured error handling with detailed error messages.
"""

from typing import Optional, Dict, Any


class UniRigException(Exception):
    """
    Base exception class for all UniRig UI errors.
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        documentation: Optional[str] = None
    ):
        """
        Initialize UniRig exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "INVALID_FILE_FORMAT")
            details: Additional technical details
            suggestion: Suggested resolution for the user
            documentation: Link to relevant documentation
        """
        self.message = message
        self.error_code = error_code
        self.details = details
        self.suggestion = suggestion
        self.documentation = documentation
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "suggestion": self.suggestion,
                "documentation": self.documentation
            }
        }


class FileValidationError(UniRigException):
    """
    Raised when uploaded file fails validation.
    Examples: unsupported format, corrupted file, invalid mesh.
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            details=details,
            suggestion=suggestion or "Please verify the file is a valid 3D model in a supported format.",
            documentation="https://docs.example.com/supported-formats"
        )


class InvalidFormatError(FileValidationError):
    """
    Raised when uploaded file format is not supported.
    """
    
    def __init__(self, file_extension: str):
        super().__init__(
            message=f"Unsupported file format: {file_extension}",
            details=f"UniRig UI supports: .obj, .fbx, .glb, .vrm",
            suggestion="Please convert your file to a supported format using Blender or similar tools."
        )


class FileSizeExceededError(FileValidationError):
    """
    Raised when uploaded file exceeds size limit.
    """
    
    def __init__(self, file_size: int, max_size: int):
        file_size_mb = file_size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)
        
        super().__init__(
            message=f"File size exceeds limit: {file_size_mb:.2f}MB (max: {max_size_mb:.2f}MB)",
            details=f"Uploaded file is {file_size} bytes, maximum allowed is {max_size} bytes",
            suggestion="Try optimizing your model (reduce polygon count, remove unused materials) or upload a smaller file."
        )


class JobNotFoundError(UniRigException):
    """
    Raised when requested job ID doesn't exist.
    """
    
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job not found: {job_id}",
            error_code="JOB_NOT_FOUND",
            details=f"No job exists with ID: {job_id}",
            suggestion="Verify the job ID is correct. The job may have been deleted or expired.",
            documentation="https://docs.example.com/job-management"
        )


class SessionNotFoundError(UniRigException):
    """
    Raised when requested session ID doesn't exist.
    """
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            error_code="SESSION_NOT_FOUND",
            details=f"No session exists with ID: {session_id}",
            suggestion="Your session may have expired. Please refresh the page to create a new session.",
            documentation="https://docs.example.com/sessions"
        )


class ProcessingError(UniRigException):
    """
    Raised when model processing fails.
    Examples: skeleton generation failure, skinning failure, merge failure.
    """
    
    def __init__(
        self,
        message: str,
        stage: str,
        details: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=f"PROCESSING_ERROR_{stage.upper()}",
            details=details,
            suggestion=suggestion or "Try processing the model again. If the issue persists, check the model topology.",
            documentation="https://docs.example.com/troubleshooting"
        )


class SkeletonGenerationError(ProcessingError):
    """
    Raised when skeleton generation fails.
    """
    
    def __init__(self, details: Optional[str] = None):
        super().__init__(
            message="Skeleton generation failed",
            stage="skeleton",
            details=details,
            suggestion="Try using a different random seed, or verify the model has valid geometry."
        )


class SkinningGenerationError(ProcessingError):
    """
    Raised when skinning weight prediction fails.
    """
    
    def __init__(self, details: Optional[str] = None):
        super().__init__(
            message="Skinning generation failed",
            stage="skinning",
            details=details,
            suggestion="Ensure the skeleton was generated successfully before attempting skinning."
        )


class MergeError(ProcessingError):
    """
    Raised when merging skeleton and skin fails.
    """
    
    def __init__(self, details: Optional[str] = None):
        super().__init__(
            message="Failed to merge skeleton and skinning",
            stage="merge",
            details=details,
            suggestion="Verify both skeleton and skinning files exist and are valid."
        )


class GPUOutOfMemoryError(ProcessingError):
    """
    Raised when GPU runs out of memory during processing.
    """
    
    def __init__(self):
        super().__init__(
            message="GPU out of memory",
            stage="gpu",
            details="The model is too complex for available GPU memory",
            suggestion="Try processing a smaller model, or reduce the polygon count of your current model."
        )


class SecurityError(UniRigException):
    """
    Raised when a security validation fails.
    """
    
    def __init__(self, details: str):
        super().__init__(
            message="Security validation failed",
            error_code="SECURITY_ERROR",
            details=details,
            suggestion="Ensure your file is a valid 3D model without embedded scripts or malicious content.",
            documentation="https://github.com/VAST-AI-Research/UniRig#supported-formats"
        )
