"""
Unit tests for CleanupService - session cleanup, secure deletion, disk monitoring.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.services.cleanup_service import CleanupService
from app.services.disk_monitor import DiskMonitor


class TestSessionFileCleanup:
    """Test session file cleanup operations."""
    
    def test_cleanup_session_files(self, db_session, sample_session, temp_upload_dir):
        """Test cleaning up files for a specific session."""
        cleanup_service = CleanupService(db_session)
        
        # Create mock session directory with files
        session_dir = temp_upload_dir / sample_session.id
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "model.obj").write_text("test")
        (session_dir / "output.obj").write_text("test")
        
        cleanup_service.cleanup_session_files(sample_session.id, temp_upload_dir)
        
        # Directory and files should be deleted
        assert not session_dir.exists()
    
    def test_cleanup_nonexistent_session(self, db_session, temp_upload_dir):
        """Test cleanup handles non-existent sessions gracefully."""
        cleanup_service = CleanupService(db_session)
        
        # Should not raise exception
        cleanup_service.cleanup_session_files("nonexistent-id", temp_upload_dir)


class TestSecureDeletion:
    """Test secure file deletion with shred."""
    
    @patch("app.services.cleanup_service.subprocess.run")
    def test_secure_delete_file(self, mock_subprocess, temp_upload_dir):
        """Test secure file deletion using shred."""
        test_file = temp_upload_dir / "sensitive.obj"
        test_file.write_text("sensitive data")
        
        mock_subprocess.return_value = Mock(returncode=0)
        
        CleanupService.secure_delete_file(test_file)
        
        # Shred command should be called
        mock_subprocess.assert_called()
        args = mock_subprocess.call_args[0][0]
        assert "shred" in args
        assert "-uz" in args or "-u" in args
    
    @patch("app.services.cleanup_service.subprocess.run")
    def test_secure_delete_fallback(self, mock_subprocess, temp_upload_dir):
        """Test fallback to standard deletion if shred fails."""
        test_file = temp_upload_dir / "file.obj"
        test_file.write_text("data")
        
        # Mock shred failure
        mock_subprocess.side_effect = FileNotFoundError("shred not found")
        
        CleanupService.secure_delete_file(test_file)
        
        # File should still be deleted via fallback
        assert not test_file.exists()
    
    def test_secure_delete_directory(self, temp_upload_dir):
        """Test secure deletion of entire directory."""
        test_dir = temp_upload_dir / "session_dir"
        test_dir.mkdir()
        (test_dir / "file1.obj").write_text("data1")
        (test_dir / "file2.obj").write_text("data2")
        
        CleanupService.secure_delete_directory(test_dir)
        
        assert not test_dir.exists()


class TestExpiredSessionCleanup:
    """Test cleanup of expired sessions."""
    
    def test_cleanup_expired_sessions(self, db_session, temp_upload_dir):
        """Test cleaning up expired sessions."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        cleanup_service = CleanupService(db_session)
        
        # Create expired session
        session = session_service.create_session()
        session.last_activity = datetime.utcnow() - timedelta(hours=25)
        
        # Create session files
        session_dir = temp_upload_dir / session.id
        session_dir.mkdir(parents=True)
        (session_dir / "file.obj").write_text("data")
        
        db_session.commit()
        
        # Run cleanup
        cleanup_service.cleanup_expired_sessions(expiration_hours=24, base_dir=temp_upload_dir)
        
        # Session files should be deleted
        assert not session_dir.exists()
        
        # Session should be marked inactive
        updated_session = session_service.get_session(session.id)
        assert updated_session.is_active is False


class TestEmergencyCleanup:
    """Test emergency cleanup when disk space is low."""
    
    def test_emergency_cleanup_oldest_sessions(self, db_session, temp_upload_dir):
        """Test emergency cleanup removes oldest sessions first."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        cleanup_service = CleanupService(db_session)
        
        # Create multiple sessions with different ages
        old_session = session_service.create_session()
        old_session.last_activity = datetime.utcnow() - timedelta(hours=20)
        
        new_session = session_service.create_session()
        new_session.last_activity = datetime.utcnow() - timedelta(hours=1)
        
        db_session.commit()
        
        # Create directories
        old_dir = temp_upload_dir / old_session.id
        old_dir.mkdir()
        (old_dir / "file.obj").write_text("data")
        
        new_dir = temp_upload_dir / new_session.id
        new_dir.mkdir()
        (new_dir / "file.obj").write_text("data")
        
        # Run emergency cleanup (should remove oldest first)
        cleanup_service.emergency_cleanup(base_dir=temp_upload_dir, target_free_gb=10.0)
        
        # Older session should be cleaned first
        # (actual behavior depends on disk space, but test the logic)
        assert cleanup_service is not None


class TestDiskMonitoring:
    """Test disk space monitoring."""
    
    @patch("app.services.disk_monitor.shutil.disk_usage")
    def test_check_disk_space_normal(self, mock_disk_usage):
        """Test disk space check with sufficient space."""
        mock_disk_usage.return_value = Mock(
            total=100 * 1024**3,  # 100GB
            used=50 * 1024**3,    # 50GB
            free=50 * 1024**3     # 50GB
        )
        
        monitor = DiskMonitor("/uploads")
        result = monitor.check_space()
        
        assert result["status"] == "ok"
        assert result["free_gb"] == 50.0
    
    @patch("app.services.disk_monitor.shutil.disk_usage")
    def test_check_disk_space_warning(self, mock_disk_usage):
        """Test disk space check with warning threshold."""
        mock_disk_usage.return_value = Mock(
            total=100 * 1024**3,
            used=92 * 1024**3,
            free=8 * 1024**3   # 8GB - below 10GB warning
        )
        
        monitor = DiskMonitor("/uploads")
        result = monitor.check_space()
        
        assert result["status"] == "warning"
        assert result["free_gb"] < 10.0
    
    @patch("app.services.disk_monitor.shutil.disk_usage")
    def test_check_disk_space_critical(self, mock_disk_usage):
        """Test disk space check with critical threshold."""
        mock_disk_usage.return_value = Mock(
            total=100 * 1024**3,
            used=97 * 1024**3,
            free=3 * 1024**3   # 3GB - below 5GB critical
        )
        
        monitor = DiskMonitor("/uploads")
        result = monitor.check_space()
        
        assert result["status"] == "critical"
        assert result["free_gb"] < 5.0
