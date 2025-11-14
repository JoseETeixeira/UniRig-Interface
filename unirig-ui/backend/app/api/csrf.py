"""
CSRF token endpoint
Provides CSRF tokens to authenticated clients
"""
from fastapi import APIRouter, Request, Response
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/csrf-token")
async def get_csrf_token(request: Request, response: Response):
    """
    Get or generate a CSRF token
    Returns the current token from cookie or generates a new one
    """
    # Check if token already exists in cookie
    csrf_token = request.cookies.get("csrf_token")
    
    # Generate new token if not present
    if not csrf_token:
        csrf_token = secrets.token_urlsafe(32)
        logger.info(f"Generated new CSRF token for client {request.client.host}")
    
    # Always set cookie to refresh expiry
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=3600  # 1 hour
    )
    
    # Return token in response body for frontend to use in X-CSRF-Token header
    return {
        "csrf_token": csrf_token
    }
