"""
Security tests for attack vector prevention.
Tests path traversal, malicious uploads, injection attacks, rate limiting bypass attempts.
"""

import pytest
from fastapi import status
from io import BytesIO


class TestPathTraversalAttacks:
    """Test prevention of path traversal attacks."""
    
    def test_path_traversal_in_filename(self, test_client, sample_session):
        """Test path traversal attempt in filename is blocked."""
        content = BytesIO(b"malicious content")
        files = {"file": ("../../etc/passwd.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Path traversal" in response.json()["detail"]
    
    def test_null_byte_injection(self, test_client, sample_session):
        """Test null byte injection in filename is blocked."""
        content = BytesIO(b"content")
        files = {"file": ("model.obj\x00.exe", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_absolute_path_in_filename(self, test_client, sample_session):
        """Test absolute path in filename is rejected."""
        content = BytesIO(b"content")
        files = {"file": ("/tmp/malicious.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMaliciousFileUploads:
    """Test detection and blocking of malicious files."""
    
    def test_executable_file_blocked(self, test_client, sample_session):
        """Test executable files are blocked."""
        # Windows PE header
        content = BytesIO(b"MZ\x90\x00" + b"\x00" * 100)
        files = {"file": ("malware.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "MIME" in response.json()["detail"] or "malicious" in response.json()["detail"].lower()
    
    def test_script_file_blocked(self, test_client, sample_session):
        """Test script files with wrong extension are blocked."""
        content = BytesIO(b"#!/bin/bash\nrm -rf /")
        files = {"file": ("script.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_zip_bomb_size_limit(self, test_client, sample_session, mock_large_file):
        """Test files exceeding size limit are rejected."""
        with open(mock_large_file, "rb") as f:
            files = {"file": ("huge.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


class TestInjectionAttacks:
    """Test SQL and command injection prevention."""
    
    def test_sql_injection_in_session_id(self, test_client):
        """Test SQL injection in session ID is handled safely."""
        malicious_session_id = "'; DROP TABLE sessions; --"
        
        response = test_client.get(
            f"/api/sessions/{malicious_session_id}/stats",
            cookies={"session_id": malicious_session_id}
        )
        
        # Should return 404, not cause SQL error
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_command_injection_in_filename(self, test_client, sample_session):
        """Test command injection via filename is blocked."""
        content = BytesIO(b"v 0 0 0")
        files = {"file": ("model; rm -rf /.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        # Filename sanitization should reject this
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_xss_in_error_messages(self, test_client, sample_session):
        """Test XSS payload in input doesn't appear in error messages."""
        xss_payload = "<script>alert('XSS')</script>"
        content = BytesIO(b"content")
        files = {"file": (f"{xss_payload}.obj", content, "model/obj")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        # Error message should not contain raw XSS payload
        error_detail = response.json().get("detail", "")
        assert "<script>" not in error_detail


class TestRateLimitingBypass:
    """Test attempts to bypass rate limiting."""
    
    def test_rate_limit_per_session_enforced(self, test_client, db_session, mock_obj_file):
        """Test rate limiting is enforced per session."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        session = session_service.create_session()
        db_session.commit()
        
        # Make 10 uploads (the limit)
        for i in range(10):
            with open(mock_obj_file, "rb") as f:
                files = {"file": (f"model_{i}.obj", f, "model/obj")}
                response = test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": session.id}
                )
                assert response.status_code == status.HTTP_200_OK
        
        # 11th should be blocked
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model_11.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": session.id}
            )
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_rate_limit_bypass_with_new_session(self, test_client, db_session, mock_obj_file):
        """Test creating new session doesn't bypass rate limits easily."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        
        # Session 1 - hit rate limit
        session1 = session_service.create_session()
        for i in range(10):
            with open(mock_obj_file, "rb") as f:
                files = {"file": (f"model_{i}.obj", f, "model/obj")}
                test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": session1.id}
                )
        
        # Session 2 - should have separate rate limit
        session2 = session_service.create_session()
        db_session.commit()
        
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": session2.id}
            )
        
        # New session should be allowed (but this tests separation, not full bypass prevention)
        assert response.status_code == status.HTTP_200_OK


class TestCSRFBypass:
    """Test CSRF protection bypass attempts."""
    
    def test_csrf_missing_token(self, test_client, sample_session, mock_obj_file):
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
    
    def test_csrf_invalid_token(self, test_client, sample_session, mock_obj_file):
        """Test POST with invalid CSRF token is blocked."""
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                headers={"X-CSRF-Token": "invalid-token"},
                cookies={"session_id": sample_session.id}
            )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthorizationBypass:
    """Test session authorization bypass attempts."""
    
    def test_access_other_session_job(self, test_client, db_session, sample_job):
        """Test accessing another session's job is blocked."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        
        # Create a different session
        other_session = session_service.create_session()
        db_session.commit()
        
        # Try to access job from original session
        response = test_client.get(
            f"/api/jobs/{sample_job.id}",
            cookies={"session_id": other_session.id}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_other_session_data(self, test_client, db_session):
        """Test deleting another session's data is blocked."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        
        session1 = session_service.create_session()
        session2 = session_service.create_session()
        db_session.commit()
        
        # Try to delete session1 from session2
        response = test_client.delete(
            f"/api/sessions/{session1.id}",
            cookies={"session_id": session2.id}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
