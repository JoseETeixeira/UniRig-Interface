"""
SQLAlchemy database models for UniRig UI.
Defines Session, Job, and MotionClip tables with relationships and indexes.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, JSON
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
    
    # Model metadata
    vertex_count = Column(Integer, nullable=True)
    bone_count = Column(Integer, nullable=True)
    file_format = Column(String, nullable=True)
    
    # Relationship to session
    session = relationship("Session", back_populates="jobs")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_jobs_session_status', 'session_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Job(job_id={self.job_id}, status={self.status}, filename={self.filename})>"


class MotionClip(Base):
    """
    Motion clip metadata from preprocessed dataset for motion retargeting.
    Indexed from cached motion files (BVH/FBX) for browsing and selection.
    """
    __tablename__ = "motion_clips"
    
    # Primary identifier
    id = Column(String(255), primary_key=True, index=True)
    
    # Motion metadata
    name = Column(String(255), nullable=False, index=True)
    file_name = Column(String(500), nullable=False, unique=True)
    duration = Column(Float, nullable=False)
    frame_count = Column(Integer, nullable=False)
    skeleton_type = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, nullable=False, default=list)  # List of strings
    thumbnail_url = Column(String(500), nullable=True)
    bone_count = Column(Integer, nullable=False)
    dataset_source = Column(String(255), nullable=False, default="default")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    
    # Relationship to retargeting jobs
    retargeting_jobs = relationship("RetargetingJob", back_populates="motion_clip")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_motion_clips_skeleton_type', 'skeleton_type'),
        Index('idx_motion_clips_name', 'name'),
    )
    
    def __repr__(self):
        return f"<MotionClip(id={self.id}, name={self.name}, skeleton_type={self.skeleton_type})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "fileName": self.file_name,
            "duration": self.duration,
            "frameCount": self.frame_count,
            "skeletonType": self.skeleton_type,
            "tags": self.tags if self.tags else [],
            "thumbnailUrl": self.thumbnail_url,
            "boneCount": self.bone_count,
            "datasetSource": self.dataset_source,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }


class RetargetingJob(Base):
    """
    Retargeting job model for tracking motion retargeting operations.
    Each retargeting job represents transferring a motion clip from the dataset
    to a rigged model using the Deep Motion Editing framework.
    """
    __tablename__ = "retargeting_jobs"
    
    # Primary key and foreign keys
    id = Column(String(255), primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    motion_clip_id = Column(String(255), ForeignKey("motion_clips.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Job status and progress
    status = Column(
        String(50),
        nullable=False,
        default="queued",
        index=True
    )
    # Status values: 'queued', 'processing', 'completed', 'failed'
    
    progress = Column(Integer, default=0)  # 0-100
    
    # Result information
    result_path = Column(String(500), nullable=True)  # Path to retargeted animation file
    error = Column(String, nullable=True)  # Error message if failed
    
    # Skeleton compatibility information (JSON object)
    skeleton_compatibility = Column(JSON, nullable=True)
    # Format: {"compatible": bool, "missingBones": [str], "extraBones": [str]}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    job = relationship("Job", backref="retargeting_jobs")
    motion_clip = relationship("MotionClip", back_populates="retargeting_jobs")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_retargeting_job_id', 'job_id'),
        Index('idx_retargeting_status', 'status'),
        Index('idx_retargeting_job_status', 'job_id', 'status'),
    )
    
    def __repr__(self):
        return f"<RetargetingJob(id={self.id}, job_id={self.job_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "jobId": self.job_id,
            "motionClipId": self.motion_clip_id,
            "status": self.status,
            "progress": self.progress,
            "resultPath": self.result_path,
            "error": self.error,
            "skeletonCompatibility": self.skeleton_compatibility,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "completedAt": self.completed_at.isoformat() if self.completed_at else None
        }
