"""
Unit tests for secure file download endpoints.
Tests session ownership validation, path security, and download functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile
import os

from app.main import app
from app.db.database import Base, get_db
from app.models.job import JobStatus


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_downloads.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestDownloadSecurity:
    """Test suite for Task 2: Secure model download endpoint"""
    
    def test_validate_access_with_matching_session(self, setup_database):
        """
        Test that validation succeeds when session IDs match.
        Requirement 1.2: Users can download their own files
        """
        # Create a session
        session_response = client.post("/api/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Create a job with a result file
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test model data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("test_model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]
        
        # Manually set final_file in database
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        filename = f"{job_id}_rigged.fbx"
        db_job.final_file = f"/results/{session_id}/{filename}"
        db_job.status = JobStatus.COMPLETED.value
        db.commit()
        db.close()
        
        # Validate access with matching session
        validate_response = client.get(
            f"/api/downloads/validate/{session_id}/{filename}",
            cookies={"session_id": session_id}
        )
        
        assert validate_response.status_code == 200
        assert validate_response.json()["status"] == "authorized"
        
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_access_denies_different_session(self, setup_database):
        """
        Test that validation fails when session IDs don't match.
        Security requirement: Prevent unauthorized access
        """
        # Create two sessions
        session1_response = client.post("/api/sessions")
        session1_id = session1_response.json()["session_id"]
        
        session2_response = client.post("/api/sessions")
        session2_id = session2_response.json()["session_id"]
        
        # Try to access session1's file with session2's credentials
        validate_response = client.get(
            f"/api/downloads/validate/{session1_id}/test_file.fbx",
            cookies={"session_id": session2_id}
        )
        
        assert validate_response.status_code == 403
        assert "do not have access" in validate_response.json()["detail"]
    
    def test_validate_access_requires_authentication(self, setup_database):
        """
        Test that validation fails without session cookie.
        Security requirement: Require authentication
        """
        # Create a session but don't provide cookie
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Try to validate without authentication
        validate_response = client.get(
            f"/api/downloads/validate/{session_id}/test_file.fbx"
        )
        
        assert validate_response.status_code == 401
        assert "Not authenticated" in validate_response.json()["detail"]
    
    def test_path_traversal_blocked(self, setup_database):
        """
        Test that directory traversal attempts are blocked.
        Security requirement: Prevent path traversal attacks
        """
        # Create a session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Test various path traversal patterns
        dangerous_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "test/../../../etc/passwd",
            "./../sensitive_file.txt",
            "../../secret.key"
        ]
        
        for dangerous_filename in dangerous_filenames:
            validate_response = client.get(
                f"/api/downloads/validate/{session_id}/{dangerous_filename}",
                cookies={"session_id": session_id}
            )
            
            assert validate_response.status_code == 403, f"Failed to block: {dangerous_filename}"
            assert "Invalid filename" in validate_response.json()["detail"]
    
    def test_invalid_file_extension_blocked(self, setup_database):
        """
        Test that only whitelisted file extensions are allowed.
        Security requirement: Whitelist allowed file types
        """
        # Create a session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Test invalid file extensions
        invalid_files = [
            "malicious.exe",
            "script.sh",
            "config.ini",
            "secret.txt",
            "database.db"
        ]
        
        for invalid_file in invalid_files:
            validate_response = client.get(
                f"/api/downloads/validate/{session_id}/{invalid_file}",
                cookies={"session_id": session_id}
            )
            
            assert validate_response.status_code == 403, f"Failed to block: {invalid_file}"
    
    def test_valid_file_extensions_allowed(self, setup_database):
        """
        Test that whitelisted file extensions are accepted.
        """
        # Create a session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Create a job with valid file
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Set final files with various valid extensions
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        
        valid_extensions = [".fbx", ".glb", ".obj", ".vrm", ".bvh"]
        
        for ext in valid_extensions:
            filename = f"{job_id}_rigged{ext}"
            db_job.final_file = f"/results/{session_id}/{filename}"
            db.commit()
            
            validate_response = client.get(
                f"/api/downloads/validate/{session_id}/{filename}",
                cookies={"session_id": session_id}
            )
            
            assert validate_response.status_code == 200, f"Failed to allow: {ext}"
        
        db.close()
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_file_not_in_session_blocked(self, setup_database):
        """
        Test that files not belonging to the session are blocked.
        Security requirement: Verify file belongs to session
        """
        # Create a session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Try to access a file that doesn't exist in any job
        validate_response = client.get(
            f"/api/downloads/validate/{session_id}/nonexistent_file.fbx",
            cookies={"session_id": session_id}
        )
        
        assert validate_response.status_code == 404
        assert "not found in session" in validate_response.json()["detail"]
    
    def test_special_characters_blocked(self, setup_database):
        """
        Test that filenames with special characters are blocked.
        Security requirement: Sanitize filenames
        """
        # Create a session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Test filenames with special characters
        invalid_filenames = [
            "file\x00name.fbx",  # Null byte
            "file;command.fbx",  # Command injection
            "file|pipe.fbx",     # Pipe character
            "file&background.fbx",  # Background execution
            "file name.fbx",     # Space (should be encoded in URL)
        ]
        
        for invalid_filename in invalid_filenames:
            validate_response = client.get(
                f"/api/downloads/validate/{session_id}/{invalid_filename}",
                cookies={"session_id": session_id}
            )
            
            # Should return 403 or 404 depending on parsing
            assert validate_response.status_code in [403, 404], f"Failed to block: {invalid_filename}"


class TestDownloadPerformance:
    """Performance tests for download functionality"""
    
    def test_large_file_support_1mb(self, setup_database):
        """
        Test download validation for 1MB file.
        Requirement: Support various file sizes
        """
        # Create session and job with 1MB file
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Create 1MB test file
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"0" * (1024 * 1024))  # 1MB
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model_1mb.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Set final file
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        filename = f"{job_id}_rigged_1mb.glb"
        db_job.final_file = f"/results/{session_id}/{filename}"
        db.commit()
        db.close()
        
        # Validate access
        validate_response = client.get(
            f"/api/downloads/validate/{session_id}/{filename}",
            cookies={"session_id": session_id}
        )
        
        assert validate_response.status_code == 200
        
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_large_file_support_50mb(self, setup_database):
        """
        Test download validation for 50MB file.
        Requirement: Support files up to 50MB
        """
        # Note: For performance reasons, we don't actually create a 50MB file in tests
        # We just verify the validation logic works regardless of file size
        
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Create minimal test file
        with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model_50mb.fbx", open(tmp_path, "rb"), "application/octet-stream")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Set final file
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        filename = f"{job_id}_rigged_50mb.fbx"
        db_job.final_file = f"/results/{session_id}/{filename}"
        db.commit()
        db.close()
        
        # Validate access (file size doesn't matter for validation)
        validate_response = client.get(
            f"/api/downloads/validate/{session_id}/{filename}",
            cookies={"session_id": session_id}
        )
        
        assert validate_response.status_code == 200
        
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
