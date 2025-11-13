"""
Celery tasks for session cleanup and maintenance
"""
from celery import shared_task
from celery.utils.log import get_task_logger

from app.services.cleanup_service import CleanupService
from app.services.disk_monitor import DiskMonitor

logger = get_task_logger(__name__)


@shared_task(name="tasks.cleanup_expired_sessions")
def cleanup_expired_sessions():
    """
    Scheduled task to clean up expired sessions
    Runs every hour via Celery Beat
    """
    logger.info("Starting scheduled session cleanup")
    
    try:
        results = CleanupService.cleanup_expired_sessions()
        logger.info(f"Session cleanup completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise


@shared_task(name="tasks.check_disk_space")
def check_disk_space():
    """
    Scheduled task to monitor disk space and trigger emergency cleanup
    Runs every hour via Celery Beat
    """
    logger.info("Checking disk space")
    
    try:
        usage = DiskMonitor.get_disk_usage()
        logger.info(f"Disk usage: {usage['free_gb']:.2f}GB free ({usage['percent_used']:.1f}% used)")
        
        if DiskMonitor.is_low_disk_space():
            logger.warning(f"Low disk space detected: {usage['free_gb']:.2f}GB free")
            logger.info("Triggering emergency cleanup")
            results = CleanupService.emergency_cleanup(target_free_gb=10)
            logger.warning(f"Emergency cleanup completed: {results}")
            return {
                "status": "emergency_cleanup",
                "results": results,
                "disk_usage": usage
            }
        elif DiskMonitor.needs_warning():
            logger.warning(f"Disk space warning: {usage['free_gb']:.2f}GB free")
            return {
                "status": "warning",
                "disk_usage": usage
            }
        else:
            return {
                "status": "ok",
                "disk_usage": usage
            }
    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        raise


@shared_task(name="tasks.cleanup_single_session", bind=True, max_retries=3)
def cleanup_single_session(self, session_id: str):
    """
    Task to clean up a single session (triggered by user action)
    
    Args:
        session_id: Session identifier to clean up
    """
    logger.info(f"Cleaning up session: {session_id}")
    
    try:
        success, message = CleanupService.cleanup_session(session_id)
        if success:
            logger.info(f"Session cleanup successful: {message}")
            return {"success": True, "message": message}
        else:
            logger.error(f"Session cleanup failed: {message}")
            return {"success": False, "message": message}
    except Exception as e:
        logger.error(f"Session cleanup error: {str(e)}")
        # Retry with exponential backoff
        try:
            self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {"success": False, "message": f"Max retries exceeded: {str(e)}"}
