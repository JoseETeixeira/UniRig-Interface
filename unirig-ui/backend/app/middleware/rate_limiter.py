"""
Rate limiting middleware for FastAPI
Prevents abuse by limiting requests per session
"""
from fastapi import Request, HTTPException
from typing import Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter for tracking upload requests per session
    """
    
    def __init__(self, max_uploads_per_hour: int = 10):
        """
        Initialize rate limiter
        
        Args:
            max_uploads_per_hour: Maximum number of uploads allowed per session per hour
        """
        self.max_uploads = max_uploads_per_hour
        self.upload_history: Dict[str, list] = {}  # session_id -> list of timestamps
    
    def check_upload_rate(self, session_id: str) -> bool:
        """
        Check if session has exceeded upload rate limit
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if upload is allowed
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Get upload history for this session
        if session_id not in self.upload_history:
            self.upload_history[session_id] = []
        
        # Filter out uploads older than 1 hour
        self.upload_history[session_id] = [
            ts for ts in self.upload_history[session_id] 
            if ts > hour_ago
        ]
        
        # Check if limit exceeded
        if len(self.upload_history[session_id]) >= self.max_uploads:
            logger.warning(f"Rate limit exceeded for session {session_id}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many uploads",
                        "details": f"Maximum {self.max_uploads} uploads per hour allowed",
                        "suggestion": "Please wait before uploading more files"
                    }
                }
            )
        
        # Record this upload
        self.upload_history[session_id].append(now)
        return True
    
    def cleanup_old_entries(self):
        """Remove old entries to prevent memory growth"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        for session_id in list(self.upload_history.keys()):
            self.upload_history[session_id] = [
                ts for ts in self.upload_history[session_id]
                if ts > hour_ago
            ]
            
            # Remove empty entries
            if not self.upload_history[session_id]:
                del self.upload_history[session_id]


# Global rate limiter instance
rate_limiter = RateLimiter(max_uploads_per_hour=10)


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to check rate limits for upload endpoints
    """
    # Only apply to upload endpoints
    if request.url.path.startswith("/api/upload") and request.method == "POST":
        # Get session ID from cookie
        session_id = request.cookies.get("session_id")
        
        if session_id:
            try:
                rate_limiter.check_upload_rate(session_id)
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content=e.detail
                )
    
    response = await call_next(request)
    return response


# Import JSONResponse at the end to avoid circular import
from fastapi.responses import JSONResponse
