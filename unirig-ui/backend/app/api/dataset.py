"""
Motion dataset management API endpoints.
Provides admin endpoints for dataset refresh, integrity checks, and status monitoring.
"""

import logging
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.services.dataset_service import dataset_service, DatasetDownloadError
from app.api.deps import get_current_session_id

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models

class DatasetStatusResponse(BaseModel):
    """Response model for dataset status."""
    exists: bool = Field(..., description="Whether dataset exists in cache")
    downloadStatus: str = Field(..., description="Download status: not_started, downloading, completed, failed")
    progress: int = Field(..., ge=0, le=100, description="Download progress percentage")
    message: str = Field(..., description="Status message")
    integrityValid: bool = Field(..., description="Whether dataset integrity is valid")
    clipCount: int = Field(..., ge=0, description="Number of motion clips in dataset")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exists": True,
                "downloadStatus": "completed",
                "progress": 100,
                "message": "Dataset ready",
                "integrityValid": True,
                "clipCount": 150
            }
        }


class RefreshDatasetRequest(BaseModel):
    """Request model for dataset refresh."""
    force: bool = Field(False, description="Force re-download even if dataset exists")
    
    class Config:
        json_schema_extra = {
            "example": {
                "force": True
            }
        }


class RefreshDatasetResponse(BaseModel):
    """Response model for dataset refresh."""
    status: str = Field(..., description="Refresh status: started, completed, exists")
    message: str = Field(..., description="Status message")
    clipCount: int = Field(..., ge=0, description="Number of clips downloaded")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "message": "Dataset downloaded successfully",
                "clipCount": 150
            }
        }


class IntegrityCheckResponse(BaseModel):
    """Response model for integrity check."""
    valid: bool = Field(..., description="Whether dataset integrity is valid")
    reason: str = Field(..., description="Reason if invalid, or 'OK' if valid")
    clipCount: int = Field(..., ge=0, description="Number of clips verified")
    verifiedAt: str = Field(..., description="Timestamp of verification")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "reason": "OK",
                "clipCount": 150,
                "verifiedAt": "2025-11-15T10:30:00Z"
            }
        }


# Endpoints

@router.get("/motion-dataset/status", response_model=DatasetStatusResponse)
async def get_dataset_status():
    """
    Get motion dataset download and integrity status.
    
    **Authentication**: None required (public endpoint)
    
    **Returns**:
    - Dataset existence status
    - Download progress and status
    - Integrity validation result
    - Number of available motion clips
    
    **Status Codes**:
    - 200: Success
    - 500: Server error
    """
    try:
        # Check if dataset exists
        exists = dataset_service.check_dataset_exists()
        
        # Get download status
        download_status = dataset_service.get_download_status()
        
        # Check integrity if dataset exists
        integrity_result = {"valid": False}
        clip_count = 0
        
        if exists:
            integrity_result = dataset_service.verify_integrity()
            index_data = dataset_service.get_dataset_index()
            clip_count = len(index_data.get("clips", []))
        
        return DatasetStatusResponse(
            exists=exists,
            downloadStatus=download_status.get("status", "unknown"),
            progress=download_status.get("progress", 0),
            message=download_status.get("message", ""),
            integrityValid=integrity_result.get("valid", False),
            clipCount=clip_count
        )
    
    except Exception as e:
        logger.error(f"Error getting dataset status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATASET_STATUS_ERROR",
                "message": "Failed to retrieve dataset status",
                "details": str(e)
            }
        )


@router.post("/admin/motion-dataset/refresh", response_model=RefreshDatasetResponse)
async def refresh_dataset(
    request: RefreshDatasetRequest,
    session_id: str = Depends(get_current_session_id)
):
    """
    Trigger motion dataset download or refresh.
    
    **Admin Endpoint**: Restricted to administrators
    
    **Authentication**: Session cookie required
    
    **Request Body**:
    - `force`: Force re-download even if dataset exists
    
    **Returns**:
    - Refresh status (started, completed, exists)
    - Status message
    - Number of clips downloaded
    
    **Status Codes**:
    - 200: Success
    - 401: Unauthorized (no session)
    - 403: Forbidden (not admin)
    - 500: Download error
    
    **Note**: This endpoint is synchronous for simplicity.
    In production, consider making it async with a background task.
    """
    try:
        logger.info(f"Dataset refresh requested by session {session_id}, force={request.force}")
        
        # TODO: Add admin authorization check
        # For now, allow any authenticated user (should restrict to admins in production)
        # if not is_admin(session_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Attempt to download dataset
        result = dataset_service.download_dataset(force=request.force)
        
        # Index motion clips to database
        if result["status"] in ["completed", "exists"]:
            try:
                dataset_service.index_motion_clips_to_database()
            except Exception as e:
                logger.error(f"Error indexing motion clips: {e}")
                # Don't fail the request if indexing fails
        
        return RefreshDatasetResponse(
            status=result["status"],
            message=result["message"],
            clipCount=result.get("clip_count", 0)
        )
    
    except DatasetDownloadError as e:
        logger.error(f"Dataset download failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATASET_DOWNLOAD_ERROR",
                "message": "Failed to download motion dataset",
                "details": str(e)
            }
        )
    
    except Exception as e:
        logger.error(f"Error refreshing dataset: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATASET_REFRESH_ERROR",
                "message": "Failed to refresh motion dataset",
                "details": str(e)
            }
        )


@router.get("/admin/motion-dataset/integrity", response_model=IntegrityCheckResponse)
async def check_dataset_integrity(
    session_id: str = Depends(get_current_session_id)
):
    """
    Check motion dataset integrity.
    
    **Admin Endpoint**: Restricted to administrators
    
    **Authentication**: Session cookie required
    
    **Returns**:
    - Integrity validation result
    - Reason if invalid
    - Number of clips verified
    - Verification timestamp
    
    **Status Codes**:
    - 200: Success (check result in response)
    - 401: Unauthorized (no session)
    - 403: Forbidden (not admin)
    - 404: Dataset not found
    - 500: Server error
    """
    try:
        logger.info(f"Dataset integrity check requested by session {session_id}")
        
        # TODO: Add admin authorization check
        # if not is_admin(session_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Check if dataset exists
        if not dataset_service.check_dataset_exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "DATASET_NOT_FOUND",
                    "message": "Motion dataset not found. Please download it first.",
                    "suggestions": ["Use POST /api/admin/motion-dataset/refresh to download"]
                }
            )
        
        # Verify integrity
        result = dataset_service.verify_integrity()
        
        # Get clip count
        index_data = dataset_service.get_dataset_index()
        clip_count = len(index_data.get("clips", []))
        
        return IntegrityCheckResponse(
            valid=result.get("valid", False),
            reason=result.get("reason", "Unknown") if not result.get("valid") else "OK",
            clipCount=clip_count if result.get("valid") else 0,
            verifiedAt=result.get("verified_at", "")
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error checking dataset integrity: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTEGRITY_CHECK_ERROR",
                "message": "Failed to check dataset integrity",
                "details": str(e)
            }
        )
