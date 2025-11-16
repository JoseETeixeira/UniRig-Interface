"""
Motion retargeting API endpoints.
Handles motion retargeting requests, validation, compatibility checking, and Celery task queuing.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

from app.db.database import get_db
from app.db.models import Job, MotionClip, RetargetingJob
from app.utils.skeleton_extractor import SkeletonExtractor
from app.utils.skeleton_compatibility import check_skeleton_compatibility
from app.api.deps import get_current_session_id
from app.tasks.retargeting_task import retarget_motion_task

logger = logging.getLogger(__name__)

router = APIRouter()


class RetargetMotionRequest(BaseModel):
    """Request model for motion retargeting."""
    jobId: str = Field(..., description="Job ID of the completed rigging job")
    motionClipId: str = Field(..., description="Motion clip ID from the motion dataset")

    class Config:
        json_schema_extra = {
            "example": {
                "jobId": "550e8400-e29b-41d4-a716-446655440000",
                "motionClipId": "motion-001"
            }
        }


class SkeletonCompatibilityDetails(BaseModel):
    """Skeleton compatibility details for error responses."""
    compatible: bool
    compatibilityScore: float = Field(..., alias="compatibility_score")
    missingBones: List[str] = Field(..., alias="missing_bones")
    extraBones: List[str] = Field(..., alias="extra_bones")
    matchedBones: List[str] = Field(..., alias="matched_bones")
    skeletonTypeMatch: bool = Field(..., alias="skeleton_type_match")
    sourceType: str = Field(..., alias="source_type")
    targetType: str = Field(..., alias="target_type")
    details: str

    class Config:
        populate_by_name = True


class RetargetMotionResponse(BaseModel):
    """Response model for successful retargeting request."""
    retargetingJobId: str
    status: str
    estimatedTime: int = Field(..., description="Estimated processing time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "retargetingJobId": "660e8400-e29b-41d4-a716-446655440001",
                "status": "queued",
                "estimatedTime": 45
            }
        }


class RetargetingJobStatusResponse(BaseModel):
    """Response model for retargeting job status."""
    id: str
    jobId: str
    motionClipId: str
    status: str
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    resultPath: Optional[str] = None
    error: Optional[str] = None
    skeletonCompatibility: Optional[Dict] = None
    processingTime: Optional[int] = Field(None, description="Actual processing time in seconds")
    createdAt: str
    completedAt: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "jobId": "550e8400-e29b-41d4-a716-446655440000",
                "motionClipId": "motion-001",
                "status": "completed",
                "progress": 100,
                "resultPath": "/results/session-id/job-id_retargeted_motion-001.fbx",
                "error": None,
                "skeletonCompatibility": {
                    "compatible": True,
                    "compatibilityScore": 0.95,
                    "missingBones": [],
                    "extraBones": [],
                    "matchedBones": ["hips", "spine", "chest"]
                },
                "processingTime": 42,
                "createdAt": "2025-11-14T20:10:00Z",
                "completedAt": "2025-11-14T20:10:42Z"
            }
        }


class RetargetingErrorResponse(BaseModel):
    """Error response model for retargeting failures."""
    error: str
    message: str
    details: Optional[Dict] = None
    suggestions: Optional[List[str]] = None


@router.post("/retarget-motion", response_model=RetargetMotionResponse, status_code=status.HTTP_202_ACCEPTED)
async def retarget_motion(
    request: RetargetMotionRequest,
    db: Session = Depends(get_db)
):
    """
    Request motion retargeting for a completed rigging job.
    
    Validates the job and motion clip, extracts skeletons, checks compatibility,
    creates a retargeting job record, and queues a Celery task for processing.
    
    Args:
        request: Retargeting request with jobId and motionClipId
        db: Database session dependency
    
    Returns:
        RetargetMotionResponse with retargeting job ID, status, and estimated time
    
    Raises:
        HTTPException 400: Invalid jobId or motionClipId format
        HTTPException 404: Job or motion clip not found
        HTTPException 409: Job is not in completed status
        HTTPException 422: Skeleton incompatibility detected
        HTTPException 500: Internal server error during processing
    """
    logger.info(f"Retargeting request received: jobId={request.jobId}, motionClipId={request.motionClipId}")
    
    # Step 1: Validate job exists and is completed
    job = db.query(Job).filter(Job.job_id == request.jobId).first()
    
    if not job:
        logger.warning(f"Job not found: {request.jobId}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "JOB_NOT_FOUND",
                "message": f"Job with ID {request.jobId} not found",
                "suggestions": [
                    "Verify the job ID is correct",
                    "Check that the job belongs to your session"
                ]
            }
        )
    
    if job.status != "completed":
        logger.warning(f"Job not completed: {request.jobId}, status={job.status}")
        raise HTTPException(
            status_code=409,
            detail={
                "error": "JOB_NOT_COMPLETED",
                "message": f"Job is in '{job.status}' status. Motion retargeting is only available for completed jobs.",
                "currentStatus": job.status,
                "suggestions": [
                    "Wait for job to complete before requesting retargeting",
                    "Check job status via GET /api/jobs/{jobId}"
                ]
            }
        )
    
    # Verify job has a final rigged model file
    if not job.final_file:
        logger.error(f"Job completed but no final file: {request.jobId}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MISSING_RIGGED_MODEL",
                "message": "Job completed but rigged model file is missing",
                "suggestions": ["Contact support with job ID"]
            }
        )
    
    # Step 2: Validate motion clip exists
    motion_clip = db.query(MotionClip).filter(MotionClip.id == request.motionClipId).first()
    
    if not motion_clip:
        logger.warning(f"Motion clip not found: {request.motionClipId}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOTION_CLIP_NOT_FOUND",
                "message": f"Motion clip with ID {request.motionClipId} not found",
                "suggestions": [
                    "Verify the motion clip ID is correct",
                    "Browse available motion clips via GET /api/motion-clips"
                ]
            }
        )
    
    # Step 3: Extract skeleton from rigged model
    logger.info(f"Extracting skeleton from rigged model: {job.final_file}")
    skeleton_extractor = SkeletonExtractor()
    
    try:
        target_skeleton = skeleton_extractor.extract_skeleton(job.final_file, use_cache=True)
    except FileNotFoundError:
        logger.error(f"Rigged model file not found: {job.final_file}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "RIGGED_MODEL_NOT_FOUND",
                "message": "Rigged model file does not exist on disk",
                "suggestions": ["Contact support with job ID"]
            }
        )
    except Exception as e:
        logger.error(f"Skeleton extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SKELETON_EXTRACTION_FAILED",
                "message": f"Failed to extract skeleton from rigged model: {str(e)}",
                "suggestions": ["Retry the request", "Contact support if issue persists"]
            }
        )
    
    # Step 4: Load source skeleton from motion clip
    # Note: For now, we'll use the motion clip's metadata
    # In a full implementation, this would parse the BVH/FBX file
    source_skeleton = {
        "bones": [],  # Would be populated from motion clip file
        "skeleton_type": motion_clip.skeleton_type,
        "bone_count": motion_clip.bone_count
    }
    
    # For compatibility checking, we need at least skeleton type matching
    # In production, we would parse the motion clip file to get bone names
    logger.info(f"Source skeleton type: {motion_clip.skeleton_type}, Target skeleton type: {target_skeleton.get('skeleton_type')}")
    
    # Step 5: Check skeleton compatibility
    try:
        compatibility_result = check_skeleton_compatibility(
            source_skeleton=source_skeleton,
            target_skeleton=target_skeleton,
            fuzzy_matching=True,
            compatibility_threshold=0.7
        )
    except Exception as e:
        logger.error(f"Compatibility check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "COMPATIBILITY_CHECK_FAILED",
                "message": f"Failed to check skeleton compatibility: {str(e)}",
                "suggestions": ["Retry the request", "Contact support if issue persists"]
            }
        )
    
    logger.info(f"Compatibility check result: compatible={compatibility_result['compatible']}, score={compatibility_result['compatibility_score']}")
    
    # Step 6: Return error if skeletons are incompatible
    if not compatibility_result["compatible"]:
        logger.warning(f"Skeleton incompatibility detected for job {request.jobId} and motion {request.motionClipId}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "SKELETON_INCOMPATIBLE",
                "message": compatibility_result["details"],
                "compatibility": {
                    "compatible": compatibility_result["compatible"],
                    "compatibilityScore": compatibility_result["compatibility_score"],
                    "missingBones": compatibility_result["missing_bones"],
                    "extraBones": compatibility_result["extra_bones"],
                    "matchedBones": compatibility_result["matched_bones"],
                    "skeletonTypeMatch": compatibility_result["skeleton_type_match"],
                    "sourceType": compatibility_result["source_type"],
                    "targetType": compatibility_result["target_type"]
                },
                "suggestions": [
                    f"Try a motion clip with '{target_skeleton.get('skeleton_type')}' skeleton type",
                    "Choose a motion with fewer required bones",
                    "Re-rig the model if skeleton structure is incorrect"
                ]
            }
        )
    
    # Step 7: Create retargeting job record
    retargeting_job_id = str(uuid.uuid4())
    retargeting_job = RetargetingJob(
        id=retargeting_job_id,
        job_id=request.jobId,
        motion_clip_id=request.motionClipId,
        status="queued",
        progress=0,
        skeleton_compatibility=compatibility_result
    )
    
    try:
        db.add(retargeting_job)
        db.commit()
        db.refresh(retargeting_job)
        logger.info(f"Created retargeting job: {retargeting_job_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create retargeting job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Failed to create retargeting job record",
                "suggestions": ["Retry the request", "Contact support if issue persists"]
            }
        )
    
    # Step 8: Queue Celery task for retargeting
    try:
        # Queue the retargeting task in the dme-retargeting queue
        task = retarget_motion_task.apply_async(
            kwargs={
                "retargeting_job_id": retargeting_job_id,
                "job_id": request.jobId,
                "motion_clip_id": request.motionClipId
            },
            queue="dme-retargeting"
        )
        
        logger.info(f"Retargeting job queued: {retargeting_job_id}, celery_task_id={task.id}")
    
    except Exception as e:
        # If task queuing fails, mark job as failed
        logger.error(f"Failed to queue retargeting task: {e}")
        retargeting_job.status = "failed"
        retargeting_job.error = f"Failed to queue retargeting task: {str(e)}"
        db.commit()
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TASK_QUEUE_ERROR",
                "message": "Failed to queue motion retargeting task",
                "suggestions": ["Check that Celery workers are running", "Retry the request"]
            }
        )
    
    # Estimate processing time based on skeleton complexity
    estimated_time = 45  # Default 45 seconds
    if target_skeleton.get("bone_count", 0) > 100:
        estimated_time = 60
    elif target_skeleton.get("bone_count", 0) < 50:
        estimated_time = 30
    
    # Step 9: Return success response
    return RetargetMotionResponse(
        retargetingJobId=retargeting_job_id,
        status="queued",
        estimatedTime=estimated_time
    )


@router.get("/retarget-motion/{retargeting_job_id}", response_model=RetargetingJobStatusResponse)
async def get_retargeting_job_status(
    retargeting_job_id: str,
    db: Session = Depends(get_db),
    session_id: str = Depends(get_current_session_id)
):
    """
    Get the status of a retargeting job.
    
    Validates that the requesting user owns the parent job before returning status.
    Includes detailed status, progress, skeleton compatibility, and timing information.
    
    Args:
        retargeting_job_id: Retargeting job UUID
        db: Database session dependency
        session_id: Current user's session ID from cookie
    
    Returns:
        RetargetingJobStatusResponse with complete job details
    
    Raises:
        HTTPException 401: Not authenticated (missing session)
        HTTPException 403: Forbidden (user doesn't own parent job)
        HTTPException 404: Retargeting job not found
    """
    logger.info(f"Fetching retargeting job status: {retargeting_job_id}, session={session_id}")
    
    # Fetch retargeting job with joined parent job for authorization check
    retargeting_job = db.query(RetargetingJob).filter(
        RetargetingJob.id == retargeting_job_id
    ).first()
    
    if not retargeting_job:
        logger.warning(f"Retargeting job not found: {retargeting_job_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "RETARGETING_JOB_NOT_FOUND",
                "message": f"Retargeting job with ID {retargeting_job_id} not found",
                "suggestions": ["Verify the retargeting job ID is correct"]
            }
        )
    
    # Fetch parent job to check session ownership
    parent_job = db.query(Job).filter(Job.job_id == retargeting_job.job_id).first()
    
    if not parent_job:
        logger.error(f"Parent job not found for retargeting job: {retargeting_job_id}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PARENT_JOB_NOT_FOUND",
                "message": "Parent rigging job not found",
                "suggestions": ["Contact support with retargeting job ID"]
            }
        )
    
    # Authorization: Verify user owns the parent job
    if parent_job.session_id != session_id:
        logger.warning(f"Unauthorized access attempt to retargeting job {retargeting_job_id} by session {session_id}")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "FORBIDDEN",
                "message": "You do not have permission to access this retargeting job",
                "suggestions": [
                    "Verify you are accessing a retargeting job from your own session",
                    "Check that you are logged in with the correct account"
                ]
            }
        )
    
    # Calculate processing time if job is completed
    processing_time = None
    if retargeting_job.status == "completed" and retargeting_job.completed_at and retargeting_job.created_at:
        time_delta = retargeting_job.completed_at - retargeting_job.created_at
        processing_time = int(time_delta.total_seconds())
    
    # Build comprehensive response
    response_data = {
        "id": retargeting_job.id,
        "jobId": retargeting_job.job_id,
        "motionClipId": retargeting_job.motion_clip_id,
        "status": retargeting_job.status,
        "progress": retargeting_job.progress if retargeting_job.progress is not None else 0,
        "resultPath": retargeting_job.result_path,
        "error": retargeting_job.error,
        "skeletonCompatibility": retargeting_job.skeleton_compatibility,
        "processingTime": processing_time,
        "createdAt": retargeting_job.created_at.isoformat() if retargeting_job.created_at else None,
        "completedAt": retargeting_job.completed_at.isoformat() if retargeting_job.completed_at else None
    }
    
    logger.info(f"Returning retargeting job status: {retargeting_job_id}, status={retargeting_job.status}")
    
    return response_data
