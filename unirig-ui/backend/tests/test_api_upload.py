"""
API endpoint tests for upload routes using FastAPI TestClient.
"""

import pytest
from io import BytesIO
from fastapi import status


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, test_client):
        """Test health endpoint returns 200."""
        response = test_client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "status" in response.json()
        assert response.json()["status"] == "healthy"


class TestFileUpload:
    """Test file upload endpoints."""
    
    def test_upload_valid_obj_file(self, test_client, sample_session, mock_obj_file):
        """Test uploading a valid OBJ file."""
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("test_model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "filename" in data
        assert "path" in data
        assert data["filename"] == "test_model.obj"
    
    def test_upload_without_session(self, test_client, mock_obj_file):
        """Test upload without session creates new session."""
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            response = test_client.post("/api/upload", files=files)
        
        assert response.status_code == status.HTTP_200_OK
        # Should set session cookie
        assert "session_id" in response.cookies
    
    def test_upload_invalid_extension(self, test_client, sample_session):
        """Test uploading file with invalid extension."""
        content = BytesIO(b"malicious content")
        files = {"file": ("malicious.exe", content, "application/octet-stream")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file format" in response.json()["detail"]
    
    def test_upload_exceeds_size_limit(self, test_client, sample_session, mock_large_file):
        """Test uploading file exceeding size limit."""
        with open(mock_large_file, "rb") as f:
            files = {"file": ("large_file.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "exceeds maximum allowed size" in response.json()["detail"]
    
    def test_upload_no_file(self, test_client, sample_session):
        """Test upload endpoint without file."""
        response = test_client.post(
            "/api/upload",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRateLimiting:
    """Test rate limiting on uploads."""
    
    def test_rate_limit_enforcement(self, test_client, sample_session, mock_obj_file):
        """Test rate limiting blocks excessive uploads."""
        # Make 10 uploads (the limit)
        for i in range(10):
            with open(mock_obj_file, "rb") as f:
                files = {"file": (f"model_{i}.obj", f, "model/obj")}
                response = test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": sample_session.id}
                )
                assert response.status_code == status.HTTP_200_OK
        
        # 11th upload should be rate limited
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model_11.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Rate limit exceeded" in response.json()["detail"]


class TestCSRFProtection:
    """Test CSRF protection."""
    
    def test_csrf_token_required_for_post(self, test_client, sample_session, mock_obj_file):
        """Test POST requests require CSRF token."""
        # First get CSRF token
        response = test_client.get("/api/csrf-token")
        csrf_token = response.json()["csrf_token"]
        
        # Upload with CSRF token
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                headers={"X-CSRF-Token": csrf_token},
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_csrf_token_missing_blocks_request(self, test_client, sample_session, mock_obj_file):
        """Test POST without CSRF token is blocked."""
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "CSRF" in response.json()["detail"]
