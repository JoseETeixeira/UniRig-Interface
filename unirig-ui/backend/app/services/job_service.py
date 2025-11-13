"""
Job service for managing rigging job operations.
Handles CRUD operations for jobs using SQLAlchemy ORM.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.models import Job as JobModel
from app.models.job import Job, JobCreate, JobUpdate, JobStatus, JobStage, JobResults
from app.utils.errors import JobNotFoundError


class JobService:
    """
    Service class for job management.
    Provides CRUD operations and business logic for rigging jobs.
    """
    
    def __init__(self, db: Session):
        """
        Initialize JobService with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def create_job(
        self,
        session_id: str,
        filename: str,
        file_size: int,
        file_path: str
    ) -> Job:
        """
        Create a new job entry in the database.
        
        Args:
            session_id: Session ID this job belongs to
            filename: Original uploaded filename
            file_size: File size in bytes
            file_path: Server path to uploaded file
            
        Returns:
            Created Job object
        """
        job_id = str(uuid.uuid4())
        
        db_job = JobModel(
            job_id=job_id,
            session_id=session_id,
            filename=filename,
            file_size=file_size,
            file_path=file_path,
            status=JobStatus.UPLOADED.value,
            progress=0.0,
            stage=None
        )
        
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        
        return self._model_to_pydantic(db_job)
    
    def get_job(self, job_id: str) -> Job:
        """
        Retrieve a job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job object
            
        Raises:
            JobNotFoundError: If job doesn't exist
        """
        db_job = self.db.query(JobModel).filter(JobModel.job_id == job_id).first()
        
        if not db_job:
            raise JobNotFoundError(job_id)
        
        return self._model_to_pydantic(db_job)
    
    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        stage: Optional[JobStage] = None,
        error_message: Optional[str] = None,
        skeleton_file: Optional[str] = None,
        skin_file: Optional[str] = None,
        final_file: Optional[str] = None
    ) -> Job:
        """
        Update job fields.
        Automatically updates the updated_at timestamp.
        
        Args:
            job_id: Job identifier
            status: New job status
            progress: Progress value (0.0 to 1.0)
            stage: Current processing stage
            error_message: Error message if job failed
            skeleton_file: Path to generated skeleton file
            skin_file: Path to generated skin file
            final_file: Path to final merged file
            
        Returns:
            Updated Job object
            
        Raises:
            JobNotFoundError: If job doesn't exist
        """
        db_job = self.db.query(JobModel).filter(JobModel.job_id == job_id).first()
        
        if not db_job:
            raise JobNotFoundError(job_id)
        
        # Update fields if provided
        if status is not None:
            db_job.status = status.value if isinstance(status, JobStatus) else status
        if progress is not None:
            db_job.progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
        if stage is not None:
            db_job.stage = stage.value if isinstance(stage, JobStage) else stage
        if error_message is not None:
            db_job.error_message = error_message
        if skeleton_file is not None:
            db_job.skeleton_file = skeleton_file
        if skin_file is not None:
            db_job.skin_file = skin_file
        if final_file is not None:
            db_job.final_file = final_file
        
        # Update timestamp
        db_job.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_job)
        
        return self._model_to_pydantic(db_job)
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job from the database.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was deleted
            
        Raises:
            JobNotFoundError: If job doesn't exist
        """
        db_job = self.db.query(JobModel).filter(JobModel.job_id == job_id).first()
        
        if not db_job:
            raise JobNotFoundError(job_id)
        
        self.db.delete(db_job)
        self.db.commit()
        
        return True
    
    def list_jobs(
        self,
        session_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Job]:
        """
        List jobs with optional filtering.
        
        Args:
            session_id: Filter by session ID
            status: Filter by job status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            List of Job objects, ordered by creation time (newest first)
        """
        query = self.db.query(JobModel)
        
        # Apply filters
        if session_id:
            query = query.filter(JobModel.session_id == session_id)
        if status:
            status_value = status.value if isinstance(status, JobStatus) else status
            query = query.filter(JobModel.status == status_value)
        
        # Order by creation time (newest first) and apply pagination
        query = query.order_by(desc(JobModel.created_at)).limit(limit).offset(offset)
        
        db_jobs = query.all()
        
        return [self._model_to_pydantic(job) for job in db_jobs]
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> Job:
        """
        Convenience method to update job status with optional error message.
        
        Args:
            job_id: Job identifier
            status: New status
            error_message: Error message if status is FAILED
            
        Returns:
            Updated Job object
        """
        return self.update_job(
            job_id=job_id,
            status=status,
            error_message=error_message
        )
    
    def get_active_jobs_for_session(self, session_id: str) -> List[Job]:
        """
        Get all active (processing or queued) jobs for a session.
        Used for enforcing concurrent job limits.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of active Job objects
        """
        active_statuses = [
            JobStatus.QUEUED.value,
            JobStatus.PROCESSING.value
        ]
        
        db_jobs = self.db.query(JobModel).filter(
            JobModel.session_id == session_id,
            JobModel.status.in_(active_statuses)
        ).all()
        
        return [self._model_to_pydantic(job) for job in db_jobs]
    
    def _model_to_pydantic(self, db_job: JobModel) -> Job:
        """
        Convert SQLAlchemy model to Pydantic model.
        
        Args:
            db_job: SQLAlchemy Job model
            
        Returns:
            Pydantic Job model
        """
        return Job(
            job_id=db_job.job_id,
            session_id=db_job.session_id,
            filename=db_job.filename,
            file_size=db_job.file_size,
            file_path=db_job.file_path,
            status=JobStatus(db_job.status),
            progress=db_job.progress,
            stage=JobStage(db_job.stage) if db_job.stage else None,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
            error_message=db_job.error_message,
            results=JobResults(
                skeleton_file=db_job.skeleton_file,
                skin_file=db_job.skin_file,
                final_file=db_job.final_file
            )
        )
