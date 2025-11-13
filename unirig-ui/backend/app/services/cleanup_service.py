"""
Cleanup service for managing session expiration and file deletion
"""
import os
import shutil
import subprocess
import platform
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from pathlib import Path
import logging

from app.db.database import get_db
from app.db.models import Session
from app.services.disk_monitor import DiskMonitor

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up expired sessions and managing disk space"""
    
    SESSION_EXPIRY_HOURS = 24
    
    @staticmethod
    def get_expired_sessions() -> List[Session]:
        """
        Find all sessions that have been idle for more than 24 hours
        
        Returns:
            List of expired Session objects
        """
        db = next(get_db())
        try:
            expiry_time = datetime.utcnow() - timedelta(hours=CleanupService.SESSION_EXPIRY_HOURS)
            expired = db.query(Session).filter(
                Session.last_accessed < expiry_time
            ).all()
            return expired
        finally:
            db.close()
    
    @staticmethod
    def get_oldest_sessions(limit: int = 10) -> List[Session]:
        """
        Get the oldest sessions by last_accessed time
        Used for emergency cleanup
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of Session objects
        """
        db = next(get_db())
        try:
            sessions = db.query(Session).order_by(
                Session.last_accessed.asc()
            ).limit(limit).all()
            return sessions
        finally:
            db.close()
    
    @staticmethod
    def secure_delete_file(file_path: str) -> bool:
        """
        Securely delete a file using shred on Linux, otherwise normal delete
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successful
        """
        try:
            if platform.system() == 'Linux':
                # Use shred for secure deletion on Linux
                subprocess.run(['shred', '-u', '-z', '-n', '3', file_path], 
                             check=False, capture_output=True)
            else:
                # Fallback to normal deletion on other platforms
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Failed to securely delete {file_path}: {e}")
            # Try regular delete as fallback
            try:
                os.remove(file_path)
                return True
            except:
                return False
    
    @staticmethod
    def secure_delete_directory(dir_path: str) -> bool:
        """
        Securely delete all files in a directory, then remove the directory
        
        Args:
            dir_path: Path to directory
            
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(dir_path):
                return True
            
            # Securely delete all files first
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    CleanupService.secure_delete_file(file_path)
            
            # Remove empty directory structure
            shutil.rmtree(dir_path, ignore_errors=True)
            return True
        except Exception as e:
            logger.error(f"Failed to securely delete directory {dir_path}: {e}")
            return False
    
    @staticmethod
    def delete_session_files(session_id: str) -> Tuple[bool, str]:
        """
        Delete all files associated with a session using secure deletion
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (success, message)
        """
        try:
            uploads_dir = f"uploads/{session_id}"
            results_dir = f"results/{session_id}"
            
            deleted_count = 0
            
            # Securely delete uploads directory
            if os.path.exists(uploads_dir):
                CleanupService.secure_delete_directory(uploads_dir)
                deleted_count += 1
                logger.info(f"Securely deleted uploads directory: {uploads_dir}")
            
            # Securely delete results directory
            if os.path.exists(results_dir):
                CleanupService.secure_delete_directory(results_dir)
                deleted_count += 1
                logger.info(f"Securely deleted results directory: {results_dir}")
            
            if deleted_count == 0:
                return True, "No files to delete"
            
            return True, f"Securely deleted {deleted_count} directories"
            
        except Exception as e:
            error_msg = f"Failed to delete files for session {session_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def delete_session_from_db(session_id: str) -> Tuple[bool, str]:
        """
        Delete session record from database
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (success, message)
        """
        db = next(get_db())
        try:
            session = db.query(Session).filter(Session.session_id == session_id).first()
            if not session:
                return False, "Session not found"
            
            db.delete(session)
            db.commit()
            logger.info(f"Deleted session from database: {session_id}")
            return True, "Session deleted from database"
            
        except Exception as e:
            db.rollback()
            error_msg = f"Failed to delete session {session_id} from database: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        finally:
            db.close()
    
    @classmethod
    def cleanup_session(cls, session_id: str) -> Tuple[bool, str]:
        """
        Complete cleanup of a session (files + database)
        
        Args:
            session_id: Session identifier
            
        Returns:
            Tuple of (success, message)
        """
        # Delete files first
        files_success, files_msg = cls.delete_session_files(session_id)
        
        # Then delete from database
        db_success, db_msg = cls.delete_session_from_db(session_id)
        
        if files_success and db_success:
            return True, f"Session {session_id} fully cleaned up"
        elif db_success:
            return True, f"Session deleted but file cleanup had issues: {files_msg}"
        else:
            return False, f"Cleanup failed - Files: {files_msg}, DB: {db_msg}"
    
    @classmethod
    def cleanup_expired_sessions(cls) -> Dict[str, any]:
        """
        Clean up all expired sessions
        
        Returns:
            Dictionary with cleanup results
        """
        expired_sessions = cls.get_expired_sessions()
        
        results = {
            "total_expired": len(expired_sessions),
            "cleaned": 0,
            "failed": 0,
            "errors": []
        }
        
        for session in expired_sessions:
            success, msg = cls.cleanup_session(session.session_id)
            if success:
                results["cleaned"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "session_id": session.session_id,
                    "error": msg
                })
        
        logger.info(f"Cleanup completed: {results['cleaned']} cleaned, {results['failed']} failed")
        return results
    
    @classmethod
    def emergency_cleanup(cls, target_free_gb: float = 10) -> Dict[str, any]:
        """
        Emergency cleanup when disk space is critically low
        Deletes oldest sessions until target free space is achieved
        
        Args:
            target_free_gb: Target free space in GB
            
        Returns:
            Dictionary with cleanup results
        """
        logger.warning("Emergency cleanup triggered due to low disk space")
        
        results = {
            "initial_free_gb": 0,
            "final_free_gb": 0,
            "sessions_cleaned": 0,
            "errors": []
        }
        
        # Get initial disk usage
        initial_usage = DiskMonitor.get_disk_usage()
        results["initial_free_gb"] = initial_usage["free_gb"]
        
        # Clean oldest sessions until we reach target
        while True:
            current_usage = DiskMonitor.get_disk_usage()
            if current_usage["free_gb"] >= target_free_gb:
                break
            
            # Get batch of oldest sessions
            old_sessions = cls.get_oldest_sessions(limit=5)
            if not old_sessions:
                logger.warning("No more sessions to clean, but target not reached")
                break
            
            for session in old_sessions:
                success, msg = cls.cleanup_session(session.session_id)
                if success:
                    results["sessions_cleaned"] += 1
                else:
                    results["errors"].append({
                        "session_id": session.session_id,
                        "error": msg
                    })
        
        # Get final disk usage
        final_usage = DiskMonitor.get_disk_usage()
        results["final_free_gb"] = final_usage["free_gb"]
        
        logger.info(f"Emergency cleanup completed: {results}")
        return results
