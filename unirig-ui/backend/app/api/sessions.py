"""
Session management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import os

from app.db.database import get_db
from app.db.models import Session
from app.services.cleanup_service import CleanupService
from app.services.disk_monitor import DiskMonitor
from app.tasks.cleanup import cleanup_single_session

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionStats(BaseModel):
    session_id: str
    created_at: str
    last_accessed: str
    upload_count: int
    uploads_size_mb: float
    results_size_mb: float
    total_size_mb: float


class DiskSpaceInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float
    warning: Optional[str] = None


@router.get('/sessions/{session_id}/stats', response_model=SessionStats)
async def get_session_stats(session_id: str, db = Depends(get_db)):
    """
    Get statistics for a specific session
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionStats with file counts and sizes
    """
    try:
        # Get session from database
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate directory sizes
        uploads_size = 0
        results_size = 0
        upload_count = 0
        
        uploads_dir = f"uploads/{session_id}"
        results_dir = f"results/{session_id}"
        
        if os.path.exists(uploads_dir):
            uploads_size = DiskMonitor.get_directory_size(uploads_dir)
            # Count files in uploads
            import os
            for root, dirs, files in os.walk(uploads_dir):
                upload_count += len(files)
        
        if os.path.exists(results_dir):
            results_size = DiskMonitor.get_directory_size(results_dir)
        
        return SessionStats(
            session_id=session.session_id,
            created_at=session.created_at.isoformat(),
            last_accessed=session.last_accessed.isoformat(),
            upload_count=upload_count,
            uploads_size_mb=uploads_size * 1024,  # Convert GB to MB
            results_size_mb=results_size * 1024,
            total_size_mb=(uploads_size + results_size) * 1024
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session stats: {str(e)}")


@router.delete('/sessions/{session_id}')
async def delete_session(session_id: str, db = Depends(get_db)):
    """
    Delete a session and all associated files
    User-triggered cleanup action
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message and task ID
    """
    try:
        # Verify session exists
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Trigger cleanup task asynchronously
        task = cleanup_single_session.delay(session_id)
        
        logger.info(f"Session cleanup initiated for {session_id}, task_id: {task.id}")
        
        return {
            "success": True,
            "message": f"Session cleanup initiated",
            "session_id": session_id,
            "task_id": task.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get('/disk-space', response_model=DiskSpaceInfo)
async def get_disk_space():
    """
    Get current disk space information
    
    Returns:
        DiskSpaceInfo with usage statistics
    """
    try:
        usage = DiskMonitor.get_disk_usage()
        
        warning = None
        if DiskMonitor.is_low_disk_space():
            warning = f"CRITICAL: Only {usage['free_gb']:.1f}GB free. Emergency cleanup may trigger."
        elif DiskMonitor.needs_warning():
            warning = f"Warning: Only {usage['free_gb']:.1f}GB free."
        
        return DiskSpaceInfo(
            total_gb=usage['total_gb'],
            used_gb=usage['used_gb'],
            free_gb=usage['free_gb'],
            percent_used=usage['percent_used'],
            warning=warning
        )
        
    except Exception as e:
        logger.error(f"Failed to get disk space: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get disk space: {str(e)}")


@router.post('/sessions/cleanup-all')
async def cleanup_all_sessions(db = Depends(get_db)):
    """
    Clean up all expired sessions immediately
    Admin/maintenance action
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Manual cleanup of all expired sessions initiated")
        results = CleanupService.cleanup_expired_sessions()
        
        return {
            "success": True,
            "message": "Cleanup completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup sessions: {str(e)}")
