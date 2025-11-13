"""
Pydantic models for job-related API requests and responses.
Defines job status enums, stages, and data structures.
"""

from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class JobStatus(str, Enum):
    """
    Job status enumeration.
    Tracks the lifecycle of a rigging job.
    """
    UPLOADED = "uploaded"      # File uploaded, not yet queued
    QUEUED = "queued"          # Job queued for processing
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"    # Successfully completed
    FAILED = "failed"          # Failed with error


class JobStage(str, Enum):
    """
    Job processing stage enumeration.
    Indicates which step of the pipeline is currently executing.
    """
    UPLOAD = "upload"
    SKELETON = "skeleton_generation"
    SKINNING = "skinning_generation"
    MERGE = "merge"


class JobResults(BaseModel):
    """
    Job results containing file paths to generated assets.
    All paths are relative to the results directory.
    """
    skeleton_file: Optional[str] = Field(None, description="Path to generated skeleton FBX file")
    skin_file: Optional[str] = Field(None, description="Path to generated skinning FBX file")
    final_file: Optional[str] = Field(None, description="Path to final merged rigged model")


class Job(BaseModel):
    """
    Job data model for API responses.
    Represents a complete job with all metadata and results.
    """
    job_id: str = Field(..., description="Unique job identifier")
    session_id: str = Field(..., description="Session ID this job belongs to")
    filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Server path to uploaded file")
    status: JobStatus = Field(..., description="Current job status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress percentage (0.0 to 1.0)")
    stage: Optional[JobStage] = Field(None, description="Current processing stage")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    results: JobResults = Field(default_factory=JobResults, description="Generated result files")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "filename": "character.glb",
                "file_size": 2458624,
                "file_path": "/uploads/7c9e6679/550e8400_character.glb",
                "status": "processing",
                "progress": 0.65,
                "stage": "skinning_generation",
                "created_at": "2025-11-13T10:00:00Z",
                "updated_at": "2025-11-13T10:05:30Z",
                "error_message": None,
                "results": {
                    "skeleton_file": "/results/7c9e6679/550e8400_skeleton.fbx",
                    "skin_file": None,
                    "final_file": None
                }
            }
        }


class JobCreate(BaseModel):
    """Request model for creating a new job."""
    session_id: str
    filename: str
    file_size: int
    file_path: str


class JobUpdate(BaseModel):
    """Request model for updating job status and progress."""
    status: Optional[JobStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    stage: Optional[JobStage] = None
    error_message: Optional[str] = None
    skeleton_file: Optional[str] = None
    skin_file: Optional[str] = None
    final_file: Optional[str] = None
