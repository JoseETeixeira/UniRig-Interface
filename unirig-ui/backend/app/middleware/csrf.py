"""
CSRF protection middleware for FastAPI
Implements CSRF token generation and validation
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import secrets
import logging

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware
    Generates and validates CSRF tokens for state-changing requests
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            
            # Add CSRF token to response cookie for future requests
            if "csrf_token" not in request.cookies:
                csrf_token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key="csrf_token",
                    value=csrf_token,
                    httponly=True,
                    secure=False,  # Set to True in production with HTTPS
                    samesite="lax"
                )
            
            return response
        
        # For state-changing requests (POST, PUT, DELETE), validate CSRF token
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")
        
        if not csrf_cookie or not csrf_header:
            logger.warning(f"CSRF token missing for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "CSRF_TOKEN_MISSING",
                        "message": "CSRF token required",
                        "details": "Cross-site request forgery protection requires a valid token",
                        "suggestion": "Ensure your client sends the X-CSRF-Token header"
                    }
                }
            )
        
        if csrf_cookie != csrf_header:
            logger.warning(f"CSRF token mismatch for {request.method} {request.url.path}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "CSRF_TOKEN_INVALID",
                        "message": "Invalid CSRF token",
                        "details": "The provided CSRF token does not match",
                        "suggestion": "Refresh the page and try again"
                    }
                }
            )
        
        # CSRF check passed, proceed with request
        response = await call_next(request)
        return response
