"""
Session service for managing user sessions and cleanup operations.
Handles session creation, validation, expiration, and automatic cleanup.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Session as SessionModel
from app.models.session import SessionModel as SessionPydantic, SessionCreate, SessionUpdate
from app.utils.errors import SessionNotFoundError


# Session expiration time (24 hours)
SESSION_TTL_HOURS = 24


class SessionService:
    """
    Service class for session management.
    Handles session lifecycle, activity tracking, and expiration.
    """
    
    def __init__(self, db: Session):
        """
        Initialize SessionService with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_session(self, session_id: Optional[str] = None) -> SessionPydantic:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Created SessionPydantic object
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Check if session already exists
        existing = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if existing:
            # Update last_accessed for existing session
            return self.update_last_accessed(session_id)
        
        # Create new session
        db_session = SessionModel(
            session_id=session_id,
            expired=False
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return self._model_to_pydantic(db_session)
    
    def get_session(self, session_id: str) -> SessionPydantic:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionPydantic object
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        db_session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if not db_session:
            raise SessionNotFoundError(session_id)
        
        return self._model_to_pydantic(db_session)
    
    def update_last_accessed(self, session_id: str) -> SessionPydantic:
        """
        Update the last_accessed timestamp for a session.
        This extends the session expiration time.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated SessionPydantic object
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        db_session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if not db_session:
            raise SessionNotFoundError(session_id)
        
        db_session.last_accessed = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_session)
        
        return self._model_to_pydantic(db_session)
    
    def expire_session(self, session_id: str) -> SessionPydantic:
        """
        Mark a session as expired.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated SessionPydantic object
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        db_session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if not db_session:
            raise SessionNotFoundError(session_id)
        
        db_session.expired = True
        
        self.db.commit()
        self.db.refresh(db_session)
        
        return self._model_to_pydantic(db_session)
    
    def is_session_expired(self, session_id: str) -> bool:
        """
        Check if a session has expired based on 24-hour inactivity.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session is expired
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        db_session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if not db_session:
            raise SessionNotFoundError(session_id)
        
        # Check if manually marked as expired
        if db_session.expired:
            return True
        
        # Check if inactive for more than 24 hours
        expiration_time = db_session.last_accessed + timedelta(hours=SESSION_TTL_HOURS)
        return datetime.utcnow() > expiration_time
    
    def get_expired_sessions(self) -> List[SessionPydantic]:
        """
        Get all sessions that have expired (24+ hours of inactivity).
        
        Returns:
            List of expired SessionPydantic objects
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
        
        # Find sessions that are either:
        # 1. Manually marked as expired
        # 2. Inactive for 24+ hours
        db_sessions = self.db.query(SessionModel).filter(
            (SessionModel.expired == True) |
            (SessionModel.last_accessed < cutoff_time)
        ).all()
        
        return [self._model_to_pydantic(session) for session in db_sessions]
    
    def cleanup_expired_sessions(self) -> int:
        """
        Mark all inactive sessions as expired.
        Does NOT delete files or database records - just marks them.
        Use with FileService.delete_session_files() to remove files.
        
        Returns:
            Number of sessions marked as expired
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=SESSION_TTL_HOURS)
        
        # Update all sessions that are inactive for 24+ hours
        count = self.db.query(SessionModel).filter(
            SessionModel.expired == False,
            SessionModel.last_accessed < cutoff_time
        ).update({"expired": True})
        
        self.db.commit()
        
        return count
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the database.
        This will cascade delete all associated jobs.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        db_session = self.db.query(SessionModel).filter(
            SessionModel.session_id == session_id
        ).first()
        
        if not db_session:
            raise SessionNotFoundError(session_id)
        
        self.db.delete(db_session)
        self.db.commit()
        
        return True
    
    def _model_to_pydantic(self, db_session: SessionModel) -> SessionPydantic:
        """
        Convert SQLAlchemy model to Pydantic model.
        
        Args:
            db_session: SQLAlchemy Session model
            
        Returns:
            Pydantic SessionPydantic model
        """
        return SessionPydantic(
            session_id=db_session.session_id,
            created_at=db_session.created_at,
            last_accessed=db_session.last_accessed,
            expired=db_session.expired
        )
