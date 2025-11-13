"""
Unit tests for JobService - job CRUD operations, status management.
"""

import pytest
from datetime import datetime

from app.services.job_service import JobService
from app.models.job import Job, JobStatus, JobType


class TestJobCreation:
    """Test job creation logic."""
    
    def test_create_skeleton_job(self, db_session, sample_session):
        """Test creating a skeleton generation job."""
        job_service = JobService(db_session)
        
        job = job_service.create_job(
            session_id=sample_session.id,
            job_type="skeleton",
            input_file="model.obj"
        )
        
        assert job.id is not None
        assert job.session_id == sample_session.id
        assert job.type == JobType.SKELETON
        assert job.status == JobStatus.PENDING
        assert job.input_file == "model.obj"
        assert job.created_at is not None
    
    def test_create_skinning_job(self, db_session, sample_session):
        """Test creating a skinning job."""
        job_service = JobService(db_session)
        
        job = job_service.create_job(
            session_id=sample_session.id,
            job_type="skinning",
            input_file="model_with_skeleton.obj"
        )
        
        assert job.type == JobType.SKINNING
        assert job.status == JobStatus.PENDING
    
    def test_create_merge_job(self, db_session, sample_session):
        """Test creating a merge job."""
        job_service = JobService(db_session)
        
        job = job_service.create_job(
            session_id=sample_session.id,
            job_type="merge",
            input_file="model.obj"
        )
        
        assert job.type == JobType.MERGE
        assert job.status == JobStatus.PENDING


class TestJobRetrieval:
    """Test job retrieval operations."""
    
    def test_get_job_by_id(self, db_session, sample_job):
        """Test retrieving job by ID."""
        job_service = JobService(db_session)
        
        retrieved_job = job_service.get_job(sample_job.id)
        
        assert retrieved_job is not None
        assert retrieved_job.id == sample_job.id
        assert retrieved_job.input_file == sample_job.input_file
    
    def test_get_nonexistent_job(self, db_session):
        """Test retrieving non-existent job returns None."""
        job_service = JobService(db_session)
        
        job = job_service.get_job("nonexistent-id")
        
        assert job is None
    
    def test_get_jobs_for_session(self, db_session, sample_session):
        """Test retrieving all jobs for a session."""
        job_service = JobService(db_session)
        
        # Create multiple jobs
        job1 = job_service.create_job(sample_session.id, "skeleton", "model1.obj")
        job2 = job_service.create_job(sample_session.id, "skinning", "model2.obj")
        db_session.commit()
        
        jobs = job_service.get_jobs_for_session(sample_session.id)
        
        assert len(jobs) >= 2
        job_ids = [j.id for j in jobs]
        assert job1.id in job_ids
        assert job2.id in job_ids


class TestJobStatusUpdates:
    """Test job status management."""
    
    def test_update_job_status_to_running(self, db_session, sample_job):
        """Test updating job status to RUNNING."""
        job_service = JobService(db_session)
        
        job_service.update_job_status(sample_job.id, JobStatus.RUNNING)
        db_session.commit()
        
        updated_job = job_service.get_job(sample_job.id)
        assert updated_job.status == JobStatus.RUNNING
        assert updated_job.started_at is not None
    
    def test_update_job_status_to_completed(self, db_session, sample_job):
        """Test updating job status to COMPLETED."""
        job_service = JobService(db_session)
        
        # First set to RUNNING
        job_service.update_job_status(sample_job.id, JobStatus.RUNNING)
        db_session.commit()
        
        # Then set to COMPLETED
        job_service.update_job_status(
            sample_job.id,
            JobStatus.COMPLETED,
            output_file="output.obj"
        )
        db_session.commit()
        
        updated_job = job_service.get_job(sample_job.id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.completed_at is not None
        assert updated_job.output_file == "output.obj"
    
    def test_update_job_status_to_failed(self, db_session, sample_job):
        """Test updating job status to FAILED with error message."""
        job_service = JobService(db_session)
        
        error_message = "GPU out of memory"
        job_service.update_job_status(
            sample_job.id,
            JobStatus.FAILED,
            error=error_message
        )
        db_session.commit()
        
        updated_job = job_service.get_job(sample_job.id)
        assert updated_job.status == JobStatus.FAILED
        assert updated_job.error == error_message
        assert updated_job.completed_at is not None


class TestJobProgress:
    """Test job progress tracking."""
    
    def test_update_job_progress(self, db_session, sample_job):
        """Test updating job progress percentage."""
        job_service = JobService(db_session)
        
        job_service.update_job_progress(sample_job.id, 45)
        db_session.commit()
        
        updated_job = job_service.get_job(sample_job.id)
        assert updated_job.progress == 45
    
    def test_update_job_progress_bounds(self, db_session, sample_job):
        """Test progress is clamped to 0-100."""
        job_service = JobService(db_session)
        
        # Test negative value
        job_service.update_job_progress(sample_job.id, -10)
        db_session.commit()
        assert job_service.get_job(sample_job.id).progress == 0
        
        # Test over 100
        job_service.update_job_progress(sample_job.id, 150)
        db_session.commit()
        assert job_service.get_job(sample_job.id).progress == 100


class TestActiveJobs:
    """Test active job retrieval."""
    
    def test_get_active_jobs_for_session(self, db_session, sample_session):
        """Test retrieving only active jobs for a session."""
        job_service = JobService(db_session)
        
        # Create jobs with different statuses
        job1 = job_service.create_job(sample_session.id, "skeleton", "model1.obj")
        job2 = job_service.create_job(sample_session.id, "skinning", "model2.obj")
        job3 = job_service.create_job(sample_session.id, "merge", "model3.obj")
        
        job_service.update_job_status(job1.id, JobStatus.RUNNING)
        job_service.update_job_status(job2.id, JobStatus.COMPLETED)
        db_session.commit()
        
        active_jobs = job_service.get_active_jobs_for_session(sample_session.id)
        
        # Should return PENDING and RUNNING jobs only
        assert len(active_jobs) == 2
        statuses = [j.status for j in active_jobs]
        assert JobStatus.RUNNING in statuses
        assert JobStatus.PENDING in statuses
        assert JobStatus.COMPLETED not in statuses


class TestJobDeletion:
    """Test job deletion."""
    
    def test_delete_job(self, db_session, sample_job):
        """Test deleting a job."""
        job_service = JobService(db_session)
        
        job_id = sample_job.id
        job_service.delete_job(job_id)
        db_session.commit()
        
        deleted_job = job_service.get_job(job_id)
        assert deleted_job is None
