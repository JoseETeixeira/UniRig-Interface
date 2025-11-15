"""
API endpoints for secure file downloads.
Validates session ownership before allowing file access.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
import re

from app.db.database import get_db
from app.db.models import Job as JobModel, Session as SessionModel
from app.utils.errors import JobNotFoundError, SessionNotFoundError
from app.api.deps import get_session_from_cookie


router = APIRouter(prefix="/api/downloads", tags=["downloads"])


@router.get("/validate/{session_id}/{filename}")
async def validate_file_access(
    session_id: str,
    filename: str,
    current_session_id: str = Depends(get_session_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Validate that the current user has access to download a file.
    Called by nginx auth_request before serving files.
    
    Args:
        session_id: Session ID from URL path
        filename: Filename from URL path
        current_session_id: Current authenticated session ID
        db: Database session
    
    Returns:
        200 OK if access granted
        403 Forbidden if access denied
        404 Not Found if session/file doesn't exist
    """
    # Validate session ownership
    if current_session_id != session_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to files from this session"
        )
    
    # Verify session exists
    db_session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )
    
    # Validate filename format and prevent directory traversal
    if not _is_safe_filename(filename):
        raise HTTPException(
            status_code=403,
            detail="Invalid filename format"
        )
    
    # Verify file exists in database (optional but recommended)
    # Check if filename belongs to any job in this session
    job = db.query(JobModel).filter(
        JobModel.session_id == session_id
    ).filter(
        (JobModel.skeleton_file.contains(filename)) |
        (JobModel.skin_file.contains(filename)) |
        (JobModel.final_file.contains(filename))
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"File {filename} not found in session {session_id}"
        )
    
    # Access granted
    return JSONResponse(
        status_code=200,
        content={"status": "authorized", "session_id": session_id, "filename": filename}
    )


def _is_safe_filename(filename: str) -> bool:
    """
    Validate that filename is safe and doesn't contain path traversal attempts.
    
    Args:
        filename: Filename to validate
    
    Returns:
        True if filename is safe, False otherwise
    """
    # Check for directory traversal patterns
    dangerous_patterns = [
        r"\.\.",  # Parent directory reference
        r"\/",    # Forward slash (should not have path separators)
        r"\\",    # Backslash
        r"\x00",  # Null byte
        r"^\.",   # Hidden files
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            return False
    
    # Check for valid file extensions (whitelist)
    allowed_extensions = [".fbx", ".glb", ".obj", ".vrm", ".bvh"]
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        return False
    
    # Check filename length
    if len(filename) > 255:
        return False
    
    # Check for valid characters (alphanumeric, dash, underscore, dot)
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return False
    
    return True
