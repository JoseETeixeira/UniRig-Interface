"""
FastAPI dependencies for authentication and authorization.
"""

from fastapi import Cookie, HTTPException
from typing import Optional


async def get_current_session_id(session_id: Optional[str] = Cookie(None, alias="session_id")) -> str:
    """
    Extract and validate session ID from cookie.
    
    Args:
        session_id: Session ID from cookie
    
    Returns:
        Valid session ID
    
    Raises:
        HTTPException: If session ID is missing or invalid
    """
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Session ID required."
        )
    
    return session_id


async def get_session_from_cookie(cookie_session_id: Optional[str] = Cookie(None, alias="session_id")) -> str:
    """
    Extract and validate session ID from cookie.
    Use this when there's a path parameter also named session_id to avoid conflicts.
    
    Args:
        cookie_session_id: Session ID from cookie
    
    Returns:
        Valid session ID
    
    Raises:
        HTTPException: If session ID is missing or invalid
    """
    if not cookie_session_id:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Session ID required."
        )
    
    return cookie_session_id
