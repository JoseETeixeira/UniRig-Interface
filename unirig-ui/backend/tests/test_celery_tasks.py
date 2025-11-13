"""
Tests for Celery background tasks with mocked subprocess calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.tasks.cleanup import cleanup_expired_sessions, check_disk_space
from app.tasks.download import download_model_checkpoint


class TestCleanupTasks:
    """Test session cleanup Celery tasks."""
    
    @patch("app.tasks.cleanup.CleanupService")
    @patch("app.tasks.cleanup.SessionService")
    def test_cleanup_expired_sessions_task(self, mock_session_service, mock_cleanup_service, db_session):
        """Test cleanup task removes expired sessions."""
        # Mock expired sessions
        expired_session = Mock()
        expired_session.id = "expired-session-123"
        mock_session_service.return_value.get_expired_sessions.return_value = [expired_session]
        
        # Run task
        result = cleanup_expired_sessions()
        
        assert result["cleaned"] > 0
        mock_cleanup_service.return_value.cleanup_session_files.assert_called()
    
    @patch("app.tasks.cleanup.DiskMonitor")
    def test_check_disk_space_task_normal(self, mock_disk_monitor):
        """Test disk space check task with normal space."""
        mock_disk_monitor.return_value.check_space.return_value = {
            "free_gb": 50.0,
            "status": "ok"
        }
        
        result = check_disk_space()
        
        assert result["status"] == "ok"
        assert result["free_gb"] == 50.0
    
    @patch("app.tasks.cleanup.DiskMonitor")
    @patch("app.tasks.cleanup.CleanupService")
    def test_check_disk_space_task_emergency_cleanup(self, mock_cleanup_service, mock_disk_monitor):
        """Test disk space check triggers emergency cleanup when low."""
        mock_disk_monitor.return_value.check_space.return_value = {
            "free_gb": 4.0,  # Below 5GB threshold
            "status": "critical"
        }
        
        result = check_disk_space()
        
        assert result["status"] == "critical"
        mock_cleanup_service.return_value.emergency_cleanup.assert_called_once()


class TestDownloadTasks:
    """Test model checkpoint download tasks."""
    
    @patch("app.tasks.download.requests.get")
    @patch("app.tasks.download.hashlib.sha256")
    def test_download_model_checkpoint_success(self, mock_sha256, mock_requests_get):
        """Test successful model checkpoint download."""
        # Mock successful download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "1000000"}
        mock_response.iter_content = lambda chunk_size: [b"data" * 1000]
        mock_requests_get.return_value = mock_response
        
        # Mock SHA256 verification
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "expected_sha256"
        mock_sha256.return_value = mock_hash
        
        result = download_model_checkpoint(
            url="https://huggingface.co/model/checkpoint.pth",
            destination="/tmp/checkpoint.pth",
            expected_sha256="expected_sha256"
        )
        
        assert result["status"] == "success"
        assert result["path"] == "/tmp/checkpoint.pth"
    
    @patch("app.tasks.download.requests.get")
    def test_download_model_checkpoint_retry_on_failure(self, mock_requests_get):
        """Test download retries on failure."""
        # Mock failed download
        mock_requests_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            download_model_checkpoint(
                url="https://huggingface.co/model/checkpoint.pth",
                destination="/tmp/checkpoint.pth"
            )
        
        # Should retry 3 times
        assert mock_requests_get.call_count == 3
    
    @patch("app.tasks.download.requests.get")
    @patch("app.tasks.download.hashlib.sha256")
    def test_download_model_checkpoint_sha256_mismatch(self, mock_sha256, mock_requests_get):
        """Test download fails with SHA256 mismatch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "1000000"}
        mock_response.iter_content = lambda chunk_size: [b"data" * 1000]
        mock_requests_get.return_value = mock_response
        
        # Mock SHA256 mismatch
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "wrong_sha256"
        mock_sha256.return_value = mock_hash
        
        with pytest.raises(ValueError, match="SHA256 mismatch"):
            download_model_checkpoint(
                url="https://huggingface.co/model/checkpoint.pth",
                destination="/tmp/checkpoint.pth",
                expected_sha256="expected_sha256"
            )


class TestSkeletonGenerationTask:
    """Test skeleton generation Celery task."""
    
    @patch("app.tasks.skeleton.subprocess.run")
    @patch("app.tasks.skeleton.JobService")
    def test_skeleton_generation_success(self, mock_job_service, mock_subprocess):
        """Test successful skeleton generation."""
        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Skeleton generated successfully"
        mock_subprocess.return_value = mock_result
        
        from app.tasks.skeleton import generate_skeleton_task
        
        result = generate_skeleton_task(
            job_id="test-job-123",
            input_file="/uploads/model.obj",
            output_dir="/outputs"
        )
        
        assert result["status"] == "completed"
        mock_job_service.return_value.update_job_status.assert_called()
    
    @patch("app.tasks.skeleton.subprocess.run")
    @patch("app.tasks.skeleton.JobService")
    def test_skeleton_generation_failure(self, mock_job_service, mock_subprocess):
        """Test skeleton generation handles errors."""
        # Mock failed subprocess execution
        mock_subprocess.side_effect = Exception("GPU out of memory")
        
        from app.tasks.skeleton import generate_skeleton_task
        
        result = generate_skeleton_task(
            job_id="test-job-123",
            input_file="/uploads/model.obj",
            output_dir="/outputs"
        )
        
        assert result["status"] == "failed"
        assert "GPU out of memory" in result["error"]


class TestSkinningTask:
    """Test skinning generation Celery task."""
    
    @patch("app.tasks.skinning.subprocess.run")
    @patch("app.tasks.skinning.JobService")
    def test_skinning_generation_success(self, mock_job_service, mock_subprocess):
        """Test successful skinning generation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Skinning completed"
        mock_subprocess.return_value = mock_result
        
        from app.tasks.skinning import generate_skinning_task
        
        result = generate_skinning_task(
            job_id="test-job-456",
            input_file="/uploads/model_skeleton.obj",
            output_dir="/outputs"
        )
        
        assert result["status"] == "completed"
    
    @patch("app.tasks.skinning.subprocess.run")
    def test_skinning_progress_updates(self, mock_subprocess):
        """Test skinning task updates progress during execution."""
        # This test would require capturing progress callback
        # Implementation depends on actual progress tracking mechanism
        pass
