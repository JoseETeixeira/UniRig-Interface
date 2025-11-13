"""
SQLAlchemy database models for UniRig UI.
Defines Session and Job tables with relationships and indexes.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Session(Base):
    """
    User session model for tracking user activity and file isolation.
    Each session has a unique ID stored in the browser cookie.
    Sessions expire after 24 hours of inactivity.
    """
    __tablename__ = "sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expired = Column(Boolean, default=False, index=True)
    
    # Relationship to jobs
    jobs = relationship("Job", back_populates="session", cascade="all, delete-orphan")
    
    # Index for efficient cleanup queries
    __table_args__ = (
        Index('idx_sessions_expired_accessed', 'expired', 'last_accessed'),
    )
    
    def __repr__(self):
        return f"<Session(session_id={self.session_id}, expired={self.expired})>"


class Job(Base):
    """
    Job model for tracking rigging operations on uploaded 3D models.
    Each job represents one model going through the pipeline:
    upload → skeleton generation → skinning generation → merge → export
    """
    __tablename__ = "jobs"
    
    # Primary key and foreign keys
    job_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    
    # Job status and progress
    status = Column(
        String,
        nullable=False,
        default="uploaded",
        index=True
    )
    # Status values: 'uploaded', 'queued', 'processing', 'completed', 'failed'
    
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    stage = Column(String, nullable=True)  # 'upload', 'skeleton_generation', 'skinning_generation', 'merge'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Error tracking
    error_message = Column(String, nullable=True)
    
    # Result file paths
    skeleton_file = Column(String, nullable=True)
    skin_file = Column(String, nullable=True)
    final_file = Column(String, nullable=True)
    
    # Relationship to session
    session = relationship("Session", back_populates="jobs")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_jobs_session_status', 'session_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Job(job_id={self.job_id}, status={self.status}, filename={self.filename})>"
