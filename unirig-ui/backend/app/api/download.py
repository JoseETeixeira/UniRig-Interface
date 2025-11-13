"""
File download endpoint.
Handles downloading generated rigging results (skeleton, skin, final).
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enum import Enum

from app.db.database import get_db
from app.services.job_service import JobService
from app.utils.errors import JobNotFoundError


router = APIRouter()


class DownloadType(str, Enum):
    """Download type enumeration."""
    SKELETON = "skeleton"
    SKIN = "skin"
    FINAL = "final"


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    type: DownloadType = Query(..., description="Type of file to download (skeleton/skin/final)"),
    db: Session = Depends(get_db)
):
    """
    Download generated rigging result files.
    
    Args:
        job_id: Job identifier
        type: Type of result file (skeleton, skin, or final)
        db: Database session (injected)
        
    Returns:
        FileResponse: File download with Content-Disposition header
        
    Raises:
        HTTPException: If job not found or file not available
        
    Example:
        GET /api/download/550e8400?type=final
        
        Response: File download with filename "{original}_rigged.glb"
    """
    try:
        job_service = JobService(db)
        job = job_service.get_job(job_id)
        
        # Determine which file to download
        file_path = None
        file_extension = None
        
        if type == DownloadType.SKELETON:
            file_path = job.results.skeleton_file
            file_extension = "fbx"
        elif type == DownloadType.SKIN:
            file_path = job.results.skin_file
            file_extension = "fbx"
        elif type == DownloadType.FINAL:
            file_path = job.results.final_file
            file_extension = "glb"
        
        # Validate file exists
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail=f"File not available. {type.value} has not been generated yet."
            )
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found on server: {file_path}"
            )
        
        # Generate download filename
        base_name = os.path.splitext(job.filename)[0]
        download_filename = f"{base_name}_{type.value}.{file_extension}"
        
        # Return file with proper headers
        return FileResponse(
            path=file_path,
            filename=download_filename,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )
        
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
