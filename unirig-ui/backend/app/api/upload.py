"""
File upload endpoint.
Handles 3D model uploads with validation and session management.
"""

import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.file_service import FileService
from app.services.job_service import JobService
from app.services.session_service import SessionService
from app.models.job import Job
from app.utils.errors import FileValidationError, FileSizeExceededError
from app.tasks.skeleton_task import generate_skeleton


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=Job)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a 3D model file for rigging.
    
    Validates file format (.obj, .fbx, .glb, .vrm) and size (max 100MB).
    Creates a job entry and stores the file in a session-specific directory.
    
    Args:
        file: Uploaded 3D model file
        session_id: Optional session ID (generated if not provided)
        db: Database session (injected)
        
    Returns:
        Job: Created job with upload details
        
    Raises:
        HTTPException: If file validation fails
        
    Example:
        POST /api/upload
        Content-Type: multipart/form-data
        
        Response:
        {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "filename": "character.glb",
            "file_size": 2458624,
            "status": "uploaded",
            ...
        }
    """
    try:
        # Validate file format
        FileService.validate_file(file)
        
        # Create or retrieve session
        session_service = SessionService(db)
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Create session if it doesn't exist
        try:
            session_service.get_session(session_id)
            # Update last accessed time
            session_service.update_last_accessed(session_id)
        except:
            # Create new session
            session_service.create_session(session_id)
        
        # Save uploaded file
        file_path, original_filename, file_size = await FileService.save_upload(file, session_id)
        
        # Create job entry
        job_service = JobService(db)
        job = job_service.create_job(
            session_id=session_id,
            filename=original_filename,
            file_size=file_size,
            file_path=file_path
        )
        
        # Trigger skeleton generation task
        logger.info(f"Triggering skeleton generation for job {job.job_id}")
        generate_skeleton.delay(job_id=job.job_id, input_file=file_path)
        
        return job
        
    except FileValidationError as e:
        logger.error(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    except FileSizeExceededError as e:
        logger.error(f"File size exceeded: {e}")
        raise HTTPException(status_code=413, detail=e.to_dict())
    except Exception as e:
        logger.exception(f"Upload failed with error: {e}")
        raise HTTPException(status_code=500, detail={
            "error": {
                "code": "UPLOAD_FAILED",
                "message": str(e),
                "type": type(e).__name__
            }
        })
