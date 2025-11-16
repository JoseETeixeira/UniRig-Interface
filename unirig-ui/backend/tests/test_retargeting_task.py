"""
Tests for motion retargeting Celery task.
"""

import pytest
import uuid
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.tasks.retargeting_task import (
    retarget_motion_task,
    RetargetingTaskError,
    _execute_dme_retargeting,
    _update_progress
)
from app.db.models import RetargetingJob, Job, MotionClip


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    return session


@pytest.fixture
def mock_retargeting_job():
    """Create a mock retargeting job."""
    job = Mock(spec=RetargetingJob)
    job.id = str(uuid.uuid4())
    job.job_id = str(uuid.uuid4())
    job.motion_clip_id = "motion-001"
    job.status = "queued"
    job.progress = 0
    job.result_path = None
    job.error = None
    job.skeleton_compatibility = {"compatible": True}
    job.created_at = datetime.utcnow()
    job.completed_at = None
    return job


@pytest.fixture
def mock_job():
    """Create a mock parent job."""
    job = Mock(spec=Job)
    job.job_id = str(uuid.uuid4())
    job.status = "completed"
    job.final_file = "/app/results/test-session/test-job_rigged.fbx"
    return job


@pytest.fixture
def mock_motion_clip():
    """Create a mock motion clip."""
    clip = Mock(spec=MotionClip)
    clip.id = "motion-001"
    clip.name = "Walking Forward"
    clip.file_name = "walk_forward.bvh"
    clip.duration = 2.5
    clip.skeleton_type = "humanoid"
    return clip


class TestRetargetMotionTask:
    """Test retarget_motion_task Celery task."""
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    @patch('app.tasks.retargeting_task._execute_dme_retargeting')
    def test_retarget_motion_success(
        self,
        mock_dme_execute,
        mock_session_local,
        mock_retargeting_job,
        mock_job,
        mock_motion_clip,
        mock_db_session
    ):
        """Test successful motion retargeting."""
        # Setup mocks
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_retargeting_job,  # First query: RetargetingJob
            mock_motion_clip,      # Second query: MotionClip
            mock_job               # Third query: Job
        ]
        
        # Mock DME execution
        mock_dme_execute.return_value = {"success": True}
        
        # Mock file existence
        with patch('app.tasks.retargeting_task.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.parent.mkdir = Mock()
            mock_path.return_value = mock_path_instance
            
            # Mock settings
            with patch('app.tasks.retargeting_task.settings') as mock_settings:
                mock_settings.motion_cache_dir = "/app/motion_cache"
                
                # Execute task
                result = retarget_motion_task(
                    retargeting_job_id=mock_retargeting_job.id,
                    job_id=mock_job.job_id,
                    motion_clip_id=mock_motion_clip.id
                )
        
        # Assertions
        assert result["status"] == "completed"
        assert "result_path" in result
        assert "processing_time" in result
        assert mock_retargeting_job.status == "completed"
        assert mock_retargeting_job.progress == 100
        assert mock_retargeting_job.error is None
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    def test_retarget_motion_job_not_found(self, mock_session_local, mock_db_session):
        """Test error when retargeting job not found."""
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(RetargetingTaskError, match="RetargetingJob .* not found"):
            retarget_motion_task(
                retargeting_job_id="nonexistent-job",
                job_id="some-job",
                motion_clip_id="some-motion"
            )
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    def test_retarget_motion_clip_not_found(
        self,
        mock_session_local,
        mock_retargeting_job,
        mock_db_session
    ):
        """Test error when motion clip not found."""
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_retargeting_job,  # RetargetingJob exists
            None                   # MotionClip not found
        ]
        
        with pytest.raises(RetargetingTaskError, match="Motion clip .* not found"):
            retarget_motion_task(
                retargeting_job_id=mock_retargeting_job.id,
                job_id="some-job",
                motion_clip_id="nonexistent-motion"
            )
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    def test_retarget_motion_parent_job_not_completed(
        self,
        mock_session_local,
        mock_retargeting_job,
        mock_motion_clip,
        mock_job,
        mock_db_session
    ):
        """Test error when parent job is not completed."""
        # Mark parent job as processing
        mock_job.status = "processing"
        
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_retargeting_job,  # RetargetingJob
            mock_motion_clip,      # MotionClip
            mock_job               # Job (not completed)
        ]
        
        # Mock file existence
        with patch('app.tasks.retargeting_task.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance
            
            with patch('app.tasks.retargeting_task.settings') as mock_settings:
                mock_settings.motion_cache_dir = "/app/motion_cache"
                
                with pytest.raises(RetargetingTaskError, match="not found or not completed"):
                    retarget_motion_task(
                        retargeting_job_id=mock_retargeting_job.id,
                        job_id=mock_job.job_id,
                        motion_clip_id=mock_motion_clip.id
                    )
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    @patch('app.tasks.retargeting_task._execute_dme_retargeting')
    def test_retarget_motion_dme_failure(
        self,
        mock_dme_execute,
        mock_session_local,
        mock_retargeting_job,
        mock_job,
        mock_motion_clip,
        mock_db_session
    ):
        """Test handling of DME execution failure."""
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_retargeting_job,
            mock_motion_clip,
            mock_job
        ]
        
        # Mock DME failure
        mock_dme_execute.side_effect = RetargetingTaskError("DME execution failed")
        
        # Mock file existence
        with patch('app.tasks.retargeting_task.Path') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path_instance.parent.mkdir = Mock()
            mock_path.return_value = mock_path_instance
            
            with patch('app.tasks.retargeting_task.settings') as mock_settings:
                mock_settings.motion_cache_dir = "/app/motion_cache"
                
                with pytest.raises(RetargetingTaskError, match="Motion retargeting failed"):
                    retarget_motion_task(
                        retargeting_job_id=mock_retargeting_job.id,
                        job_id=mock_job.job_id,
                        motion_clip_id=mock_motion_clip.id
                    )
    
    @patch('app.tasks.retargeting_task.SessionLocal')
    def test_retarget_motion_progress_updates(
        self,
        mock_session_local,
        mock_retargeting_job,
        mock_job,
        mock_motion_clip,
        mock_db_session
    ):
        """Test that progress updates occur at correct milestones."""
        mock_session_local.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_retargeting_job,
            mock_motion_clip,
            mock_job,
            mock_retargeting_job,  # For output verification
        ]
        
        # Track progress updates
        progress_values = []
        original_commit = mock_db_session.commit
        
        def track_progress(*args, **kwargs):
            progress_values.append(mock_retargeting_job.progress)
            return original_commit(*args, **kwargs)
        
        mock_db_session.commit = track_progress
        
        # Mock DME execution
        with patch('app.tasks.retargeting_task._execute_dme_retargeting') as mock_dme:
            mock_dme.return_value = {"success": True}
            
            # Mock file existence
            with patch('app.tasks.retargeting_task.Path') as mock_path:
                mock_path_instance = Mock()
                mock_path_instance.exists.return_value = True
                mock_path_instance.parent.mkdir = Mock()
                mock_path.return_value = mock_path_instance
                
                with patch('app.tasks.retargeting_task.settings') as mock_settings:
                    mock_settings.motion_cache_dir = "/app/motion_cache"
                    with patch('app.tasks.retargeting_task.os.path.exists', return_value=True):
                        retarget_motion_task(
                            retargeting_job_id=mock_retargeting_job.id,
                            job_id=mock_job.job_id,
                            motion_clip_id=mock_motion_clip.id
                        )
        
        # Verify progress milestones
        assert 0 in progress_values    # Initial
        assert 20 in progress_values   # Motion loaded
        assert 40 in progress_values   # Skeleton loaded
        assert 50 in progress_values   # DME started
        assert 90 in progress_values   # Output verified
        assert 100 in progress_values  # Completed


class TestDMEExecution:
    """Test DME retargeting execution function."""
    
    def test_execute_dme_placeholder(self):
        """Test placeholder DME execution."""
        result = _execute_dme_retargeting(
            source_motion="/test/motion.bvh",
            target_skeleton="/test/skeleton.fbx",
            output_file="/test/output.fbx"
        )
        
        assert result["success"] is True
        assert "bone_mapping" in result
        assert result["bone_mapping"]["matched_bones"] > 0
    
    def test_execute_dme_with_progress_callback(self):
        """Test DME execution with progress callbacks."""
        progress_values = []
        
        def progress_callback(value):
            progress_values.append(value)
        
        _execute_dme_retargeting(
            source_motion="/test/motion.bvh",
            target_skeleton="/test/skeleton.fbx",
            output_file="/test/output.fbx",
            progress_callback=progress_callback
        )
        
        # Verify progress callback was invoked
        assert len(progress_values) > 0
        assert 0.0 in progress_values
        assert 1.0 in progress_values


class TestUpdateProgress:
    """Test progress update helper function."""
    
    def test_update_progress_success(self):
        """Test successful progress update."""
        mock_db = Mock()
        mock_job = Mock(spec=RetargetingJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        _update_progress(mock_db, "test-job-id", 50)
        
        assert mock_job.progress == 50
        mock_db.commit.assert_called_once()
    
    def test_update_progress_job_not_found(self):
        """Test progress update when job not found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Should not raise exception
        _update_progress(mock_db, "nonexistent-job", 50)
    
    def test_update_progress_db_error(self):
        """Test progress update handles database errors gracefully."""
        mock_db = Mock()
        mock_db.commit.side_effect = Exception("Database error")
        mock_job = Mock(spec=RetargetingJob)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_job
        
        # Should not raise exception
        _update_progress(mock_db, "test-job-id", 50)
        mock_db.rollback.assert_called_once()
