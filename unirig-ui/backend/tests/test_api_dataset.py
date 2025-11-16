"""
Tests for motion dataset management API endpoints.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_service import dataset_service, DatasetDownloadError

client = TestClient(app)


@pytest.fixture
def mock_dataset_service():
    """Create a mock dataset service."""
    with patch('app.api.dataset.dataset_service') as mock:
        yield mock


class TestGetDatasetStatus:
    """Test GET /api/motion-dataset/status endpoint."""
    
    def test_get_status_dataset_exists_and_valid(self, mock_dataset_service):
        """Test getting status when dataset exists and is valid."""
        mock_dataset_service.check_dataset_exists.return_value = True
        mock_dataset_service.get_download_status.return_value = {
            "status": "completed",
            "progress": 100,
            "message": "Dataset ready"
        }
        mock_dataset_service.verify_integrity.return_value = {
            "valid": True,
            "clip_count": 150,
            "verified_at": "2025-11-15T10:00:00Z"
        }
        mock_dataset_service.get_dataset_index.return_value = {
            "clips": [{"id": f"clip-{i}"} for i in range(150)]
        }
        
        response = client.get(
            "/api/motion-dataset/status",
            cookies={"session_id": "test-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["downloadStatus"] == "completed"
        assert data["progress"] == 100
        assert data["integrityValid"] is True
        assert data["clipCount"] == 150
    
    def test_get_status_dataset_not_found(self, mock_dataset_service):
        """Test getting status when dataset doesn't exist."""
        mock_dataset_service.check_dataset_exists.return_value = False
        mock_dataset_service.get_download_status.return_value = {
            "status": "not_started",
            "progress": 0,
            "message": "Dataset not downloaded"
        }
        
        response = client.get(
            "/api/motion-dataset/status",
            cookies={"session_id": "test-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["downloadStatus"] == "not_started"
        assert data["progress"] == 0
        assert data["integrityValid"] is False
        assert data["clipCount"] == 0
    
    def test_get_status_unauthorized(self, mock_dataset_service):
        """Test error when no session cookie provided."""
        response = client.get("/api/motion-dataset/status")
        
        assert response.status_code == 401
    
    def test_get_status_service_error(self, mock_dataset_service):
        """Test handling of service errors."""
        mock_dataset_service.check_dataset_exists.side_effect = Exception("Service error")
        
        response = client.get(
            "/api/motion-dataset/status",
            cookies={"session_id": "test-session"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "DATASET_STATUS_ERROR"


class TestRefreshDataset:
    """Test POST /api/admin/motion-dataset/refresh endpoint."""
    
    def test_refresh_dataset_success(self, mock_dataset_service):
        """Test successful dataset refresh."""
        mock_dataset_service.download_dataset.return_value = {
            "status": "completed",
            "message": "Dataset downloaded successfully",
            "clip_count": 150
        }
        mock_dataset_service.index_motion_clips_to_database.return_value = None
        
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": False},
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["clipCount"] == 150
        assert "successfully" in data["message"]
    
    def test_refresh_dataset_force(self, mock_dataset_service):
        """Test forced dataset refresh."""
        mock_dataset_service.download_dataset.return_value = {
            "status": "completed",
            "message": "Dataset re-downloaded",
            "clip_count": 150
        }
        mock_dataset_service.index_motion_clips_to_database.return_value = None
        
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": True},
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200
        mock_dataset_service.download_dataset.assert_called_once_with(force=True)
    
    def test_refresh_dataset_already_exists(self, mock_dataset_service):
        """Test refresh when dataset already exists."""
        mock_dataset_service.download_dataset.return_value = {
            "status": "exists",
            "message": "Dataset already cached",
            "clip_count": 150
        }
        mock_dataset_service.index_motion_clips_to_database.return_value = None
        
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": False},
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "exists"
    
    def test_refresh_dataset_download_error(self, mock_dataset_service):
        """Test handling of download errors."""
        mock_dataset_service.download_dataset.side_effect = DatasetDownloadError("Download failed")
        
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": False},
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "DATASET_DOWNLOAD_ERROR"
    
    def test_refresh_dataset_unauthorized(self, mock_dataset_service):
        """Test error when no session cookie provided."""
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": False}
        )
        
        assert response.status_code == 401
    
    def test_refresh_dataset_indexing_failure(self, mock_dataset_service):
        """Test that indexing failures don't fail the request."""
        mock_dataset_service.download_dataset.return_value = {
            "status": "completed",
            "message": "Dataset downloaded",
            "clip_count": 150
        }
        mock_dataset_service.index_motion_clips_to_database.side_effect = Exception("Indexing failed")
        
        # Request should still succeed even if indexing fails
        response = client.post(
            "/api/admin/motion-dataset/refresh",
            json={"force": False},
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200


class TestCheckDatasetIntegrity:
    """Test GET /api/admin/motion-dataset/integrity endpoint."""
    
    def test_check_integrity_valid(self, mock_dataset_service):
        """Test integrity check when dataset is valid."""
        mock_dataset_service.check_dataset_exists.return_value = True
        mock_dataset_service.verify_integrity.return_value = {
            "valid": True,
            "clip_count": 150,
            "verified_at": "2025-11-15T10:00:00Z"
        }
        mock_dataset_service.get_dataset_index.return_value = {
            "clips": [{"id": f"clip-{i}"} for i in range(150)]
        }
        
        response = client.get(
            "/api/admin/motion-dataset/integrity",
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["reason"] == "OK"
        assert data["clipCount"] == 150
        assert data["verifiedAt"] == "2025-11-15T10:00:00Z"
    
    def test_check_integrity_invalid(self, mock_dataset_service):
        """Test integrity check when dataset is corrupted."""
        mock_dataset_service.check_dataset_exists.return_value = True
        mock_dataset_service.verify_integrity.return_value = {
            "valid": False,
            "reason": "Checksum mismatch",
            "verified_at": "2025-11-15T10:00:00Z"
        }
        mock_dataset_service.get_dataset_index.return_value = {
            "clips": []
        }
        
        response = client.get(
            "/api/admin/motion-dataset/integrity",
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["reason"] == "Checksum mismatch"
        assert data["clipCount"] == 0
    
    def test_check_integrity_dataset_not_found(self, mock_dataset_service):
        """Test error when dataset doesn't exist."""
        mock_dataset_service.check_dataset_exists.return_value = False
        
        response = client.get(
            "/api/admin/motion-dataset/integrity",
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "DATASET_NOT_FOUND"
    
    def test_check_integrity_unauthorized(self, mock_dataset_service):
        """Test error when no session cookie provided."""
        response = client.get("/api/admin/motion-dataset/integrity")
        
        assert response.status_code == 401
    
    def test_check_integrity_service_error(self, mock_dataset_service):
        """Test handling of service errors."""
        mock_dataset_service.check_dataset_exists.return_value = True
        mock_dataset_service.verify_integrity.side_effect = Exception("Verification failed")
        
        response = client.get(
            "/api/admin/motion-dataset/integrity",
            cookies={"session_id": "admin-session"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["error"] == "INTEGRITY_CHECK_ERROR"


class TestDatasetServiceIntegration:
    """Integration tests for dataset service."""
    
    @patch('app.services.dataset_service.Path')
    def test_dataset_service_mock_generation(self, mock_path):
        """Test that dataset service can generate mock dataset."""
        # This would require more complex mocking of file I/O
        # For now, just verify the service can be instantiated
        from app.services.dataset_service import DatasetService
        
        service = DatasetService()
        assert service.cache_dir is not None
        assert service.index_file is not None
