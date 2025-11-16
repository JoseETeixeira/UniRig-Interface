"""
Motion clips API endpoints.
Provides access to indexed motion clips from the preprocessed dataset for browsing and selection.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import MotionClip


router = APIRouter()


class MotionClipResponse(BaseModel):
    """Response model for a single motion clip."""
    id: str
    name: str
    fileName: str
    duration: float
    frameCount: int
    skeletonType: str
    tags: List[str]
    thumbnailUrl: Optional[str]
    boneCount: int
    datasetSource: str
    createdAt: Optional[str]
    updatedAt: Optional[str]

    class Config:
        from_attributes = True


class MotionClipsListResponse(BaseModel):
    """Response model for paginated motion clips list."""
    clips: List[MotionClipResponse]
    total: int
    limit: int
    offset: int


@router.get("/motion-clips", response_model=MotionClipsListResponse)
async def list_motion_clips(
    skeleton_type: Optional[str] = Query(None, description="Filter by skeleton type (humanoid, quadruped, other)"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(50, ge=1, le=100, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    List available motion clips from the preprocessed dataset.
    
    Supports filtering by skeleton type and tags, with pagination.
    Returns 503 if motion dataset has not been indexed yet.
    
    Args:
        skeleton_type: Optional filter for skeleton type (humanoid, quadruped, other)
        tags: Optional comma-separated list of tags to filter by
        limit: Maximum number of clips to return (1-100, default 50)
        offset: Number of clips to skip for pagination (default 0)
        db: Database session dependency
    
    Returns:
        MotionClipsListResponse with clips array, total count, and pagination info
    
    Raises:
        HTTPException 503: If motion dataset is not indexed yet
    """
    # Check if dataset is indexed (any clips exist)
    total_clips = db.query(func.count(MotionClip.id)).scalar()
    if total_clips == 0:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DATASET_NOT_READY",
                "message": "Motion dataset is not yet indexed. Please wait for dataset download and indexing to complete.",
                "suggestions": [
                    "Check application logs for dataset download progress",
                    "Verify MOTION_DATASET_URL environment variable is configured",
                    "Retry in a few minutes"
                ]
            }
        )
    
    # Build query with filters
    query = db.query(MotionClip)
    
    # Filter by skeleton type if provided
    if skeleton_type:
        skeleton_type_lower = skeleton_type.lower()
        if skeleton_type_lower not in ['humanoid', 'quadruped', 'other']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_SKELETON_TYPE",
                    "message": f"Invalid skeleton type: {skeleton_type}. Must be one of: humanoid, quadruped, other"
                }
            )
        query = query.filter(MotionClip.skeleton_type == skeleton_type_lower)
    
    # Filter by tags if provided
    if tags:
        tag_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]
        if tag_list:
            # Filter clips that have ANY of the requested tags (OR logic)
            # SQLite JSON query: check if any tag in the tags array matches
            for tag in tag_list:
                query = query.filter(MotionClip.tags.contains([tag]))
    
    # Get total count with filters applied
    total_filtered = query.count()
    
    # Apply pagination
    clips = query.order_by(MotionClip.name).offset(offset).limit(limit).all()
    
    # Convert to response format using to_dict() method
    clips_data = [MotionClipResponse(**clip.to_dict()) for clip in clips]
    
    return MotionClipsListResponse(
        clips=clips_data,
        total=total_filtered,
        limit=limit,
        offset=offset
    )


@router.get("/motion-clips/{clip_id}", response_model=MotionClipResponse)
async def get_motion_clip(
    clip_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed metadata for a specific motion clip.
    
    Args:
        clip_id: Motion clip ID (UUID)
        db: Database session dependency
    
    Returns:
        MotionClipResponse with full clip metadata
    
    Raises:
        HTTPException 404: If clip ID does not exist
    """
    clip = db.query(MotionClip).filter(MotionClip.id == clip_id).first()
    
    if not clip:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOTION_CLIP_NOT_FOUND",
                "message": f"Motion clip with ID {clip_id} does not exist in the dataset"
            }
        )
    
    return MotionClipResponse(**clip.to_dict())
