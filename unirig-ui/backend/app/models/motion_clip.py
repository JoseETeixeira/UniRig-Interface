"""
Motion Clip Database Model

Represents motion clips from the preprocessed dataset for motion retargeting.

Design: Data Models - MotionClip (design.md lines 272-295)
Requirements: 5.1
"""

from sqlalchemy import Column, String, Integer, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class MotionClip(Base):
    """
    Motion clip metadata stored in database for browsing and selection.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Display name of the motion
        file_name: File name in dataset
        duration: Duration in seconds
        frame_count: Number of frames
        skeleton_type: Type of skeleton (humanoid, quadruped, other)
        tags: List of tags for categorization (e.g., ['walk', 'run'])
        thumbnail_url: Optional preview image URL
        bone_count: Number of bones in skeleton
        dataset_source: Source dataset name
        created_at: Timestamp when indexed
        updated_at: Timestamp of last update
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
