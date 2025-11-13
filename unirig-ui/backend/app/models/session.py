"""
Pydantic models for session-related API requests and responses.
Handles user session management and tracking.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SessionModel(BaseModel):
    """
    Session data model for API responses.
    Represents a user session with activity tracking.
    """
    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_accessed: datetime = Field(..., description="Last activity timestamp")
    expired: bool = Field(False, description="Whether session has expired")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "created_at": "2025-11-13T09:00:00Z",
                "last_accessed": "2025-11-13T10:30:00Z",
                "expired": False
            }
        }


class SessionCreate(BaseModel):
    """Request model for creating a new session."""
    session_id: Optional[str] = Field(None, description="Optional session ID (generated if not provided)")


class SessionUpdate(BaseModel):
    """Request model for updating session activity."""
    last_accessed: Optional[datetime] = None
    expired: Optional[bool] = None
