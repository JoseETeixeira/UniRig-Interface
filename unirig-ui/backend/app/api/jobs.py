"""
Job management endpoints.
Handles job status queries, processing triggers, and job lifecycle operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.services.job_service import JobService
from app.services.file_service import FileService
from app.models.job import Job, JobStatus
from app.utils.errors import JobNotFoundError


router = APIRouter()


class SkeletonRequest(BaseModel):
    """Request model for skeleton generation."""
    seed: Optional[int] = 42


class SkinningRequest(BaseModel):
    """Request model for skinning generation."""
    pass


class TaskResponse(BaseModel):
    """Response model for background task trigger."""
    task_id: str
    status: str
    message: str


class JobListResponse(BaseModel):
    """Response model for job list."""
    jobs: List[Job]
    total: int


class DeleteResponse(BaseModel):
    """Response model for job deletion."""
    message: str
    job_id: str


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get job status and details by ID.
    Used for polling job progress during processing.
    
    Args:
        job_id: Job identifier
        db: Database session (injected)
        
    Returns:
        Job: Complete job information with status and results
        
    Raises:
        HTTPException: If job not found
        
    Example:
        GET /api/jobs/550e8400-e29b-41d4-a716-446655440000
        
        Response:
        {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "processing",
            "progress": 0.65,
            "stage": "skinning_generation",
            ...
        }
    """
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        return job
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.get("/sessions/{session_id}/jobs", response_model=JobListResponse)
async def list_session_jobs(
    session_id: str,
    status: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of jobs"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_db)
):
    """
    List all jobs for a session with optional filtering.
    
    Args:
        session_id: Session identifier
        status: Optional status filter (uploaded/queued/processing/completed/failed)
        limit: Maximum jobs to return (1-1000)
        offset: Pagination offset
        db: Database session (injected)
        
    Returns:
        JobListResponse: List of jobs with total count
        
    Example:
        GET /api/sessions/7c9e6679/jobs?status=completed&limit=10
        
        Response:
        {
            "jobs": [...],
            "total": 3
        }
    """
    job_service = JobService(db)
    
    # Convert status string to enum if provided
    status_filter = None
    if status:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: uploaded, queued, processing, completed, failed"
            )
    
    jobs = job_service.list_jobs(
        session_id=session_id,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    
    return JobListResponse(jobs=jobs, total=len(jobs))


@router.post("/jobs/{job_id}/skeleton", response_model=TaskResponse)
async def trigger_skeleton_generation(
    job_id: str,
    request: SkeletonRequest = SkeletonRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger skeleton generation for a job.
    Queues a Celery task to generate the skeleton structure.
    
    Args:
        job_id: Job identifier
        request: Skeleton generation parameters (seed)
        db: Database session (injected)
        
    Returns:
        TaskResponse: Task ID and status
        
    Raises:
        HTTPException: If job not found or concurrent job limit exceeded
        
    Example:
        POST /api/jobs/550e8400/skeleton
        Body: {"seed": 42}
        
        Response:
        {
            "task_id": "celery_task_uuid",
            "status": "queued",
            "message": "Skeleton generation queued"
        }
    """
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        # Check for concurrent job limit (max 1 processing job per session)
        session_id = job.session_id
        active_jobs = job_service.get_active_jobs_for_session(session_id)
        
        if len(active_jobs) > 0:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "CONCURRENT_JOB_LIMIT",
                        "message": "A job is already processing for this session",
                        "details": f"Found {len(active_jobs)} active job(s)",
                        "suggestion": "Wait for the current job to complete before starting a new one"
                    }
                }
            )
        
        # Update job status to queued
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress=0.0
        )
        
        # Trigger Celery task for skeleton generation
        from app.tasks.skeleton_task import generate_skeleton
        task = generate_skeleton.delay(
            job_id=job_id,
            input_file=job.file_path,
            seed=request.seed
        )
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="Skeleton generation queued successfully"
        )
        
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.post("/jobs/{job_id}/skinning", response_model=TaskResponse)
async def trigger_skinning_generation(
    job_id: str,
    request: SkinningRequest = SkinningRequest(),
    db: Session = Depends(get_db)
):
    """
    Trigger skinning weight generation for a job.
    Requires skeleton to be generated first.
    Queues a Celery task to generate skinning weights.
    
    Args:
        job_id: Job identifier
        request: Skinning generation parameters
        db: Database session (injected)
        
    Returns:
        TaskResponse: Task ID and status
        
    Raises:
        HTTPException: If job not found or skeleton not available
        
    Example:
        POST /api/jobs/550e8400/skinning
        
        Response:
        {
            "task_id": "celery_task_uuid",
            "status": "queued",
            "message": "Skinning generation queued"
        }
    """
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        # Validate skeleton exists
        if not job.results.skeleton_file:
            raise HTTPException(
                status_code=400,
                detail="Skeleton must be generated before skinning. Call /skeleton endpoint first."
            )
        
        # Check for concurrent job limit (max 1 processing job per session)
        session_id = job.session_id
        active_jobs = job_service.get_active_jobs_for_session(session_id)
        
        if len(active_jobs) > 0:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "CONCURRENT_JOB_LIMIT",
                        "message": "A job is already processing for this session",
                        "details": f"Found {len(active_jobs)} active job(s)",
                        "suggestion": "Wait for the current job to complete before starting a new one"
                    }
                }
            )
        
        # Update job status to queued
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.QUEUED,
            progress=0.0
        )
        
        # Trigger Celery task for skinning generation
        from app.tasks.skinning_task import generate_skinning
        task = generate_skinning.delay(
            job_id=job_id,
            skeleton_file=job.results.skeleton_file
        )
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="Skinning generation queued successfully"
        )
        
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())


@router.delete("/jobs/{job_id}", response_model=DeleteResponse)
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a job and its associated files.
    
    Args:
        job_id: Job identifier
        db: Database session (injected)
        
    Returns:
        DeleteResponse: Confirmation message
        
    Raises:
        HTTPException: If job not found
        
    Example:
        DELETE /api/jobs/550e8400
        
        Response:
        {
            "message": "Job deleted successfully",
            "job_id": "550e8400"
        }
    """
    try:
        job_service = JobService(db)
        
        # Get job to retrieve file paths
        job = job_service.get_job(job_id)
        
        # Delete job from database
        job_service.delete_job(job_id)
        
        # Note: Files are cleaned up by session cleanup process
        # Individual file deletion could be added here if needed
        
        return DeleteResponse(
            message="Job deleted successfully",
            job_id=job_id
        )
        
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
