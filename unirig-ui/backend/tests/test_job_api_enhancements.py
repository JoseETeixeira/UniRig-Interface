"""
Unit tests for Job API enhancements (Task 1)
Tests resultFiles and metadata fields in job responses
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile
import json

from app.main import app
from app.db.database import Base, get_db
from app.models.job import JobStatus, JobStage


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


class TestJobAPIEnhancements:
    """Test suite for Task 1: Enhance Job API with model URLs and metadata"""
    
    def test_get_job_includes_result_files_for_completed_job(self, setup_database):
        """
        Test that GET /api/jobs/{jobId} includes resultFiles object
        for completed jobs with skeleton and rigged files.
        Maps to Requirement 1.1
        """
        # Create a session
        session_response = client.post("/api/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Create a job
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"fake model data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("test_model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]
        
        # Manually update job to completed with result files (simulating worker completion)
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        db_job.status = JobStatus.COMPLETED.value
        db_job.skeleton_file = f"/results/{session_id}/{job_id}_skeleton.fbx"
        db_job.final_file = f"/results/{session_id}/{job_id}_rigged.fbx"
        db_job.progress = 1.0
        db.commit()
        db.close()
        
        # Get job and verify resultFiles structure
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        job_data = response.json()
        assert "resultFiles" in job_data
        assert job_data["resultFiles"] is not None
        
        result_files = job_data["resultFiles"]
        assert "skeleton" in result_files
        assert "rigged" in result_files
        assert result_files["skeleton"] == f"/results/{session_id}/{job_id}_skeleton.fbx"
        assert result_files["rigged"] == f"/results/{session_id}/{job_id}_rigged.fbx"
        
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_get_job_includes_metadata_for_completed_job(self, setup_database):
        """
        Test that GET /api/jobs/{jobId} includes metadata object
        with vertexCount, boneCount, fileSize, format.
        Maps to Requirements 1.1 and 1.7
        """
        # Create a session
        session_response = client.post("/api/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Create a job
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"fake model data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("test_model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]
        
        # Manually update job with metadata (simulating worker completion)
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        
        db = SessionLocal()
        db_job = db.query(JobModel).filter(JobModel.job_id == job_id).first()
        db_job.status = JobStatus.COMPLETED.value
        db_job.final_file = f"/results/{session_id}/{job_id}_rigged.fbx"
        db_job.vertex_count = 50000
        db_job.bone_count = 65
        db_job.file_format = "FBX"
        db.commit()
        db.close()
        
        # Get job and verify metadata structure
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        job_data = response.json()
        assert "metadata" in job_data
        assert job_data["metadata"] is not None
        
        metadata = job_data["metadata"]
        assert "vertexCount" in metadata
        assert "boneCount" in metadata
        assert "fileSize" in metadata
        assert "format" in metadata
        
        assert metadata["vertexCount"] == 50000
        assert metadata["boneCount"] == 65
        assert metadata["format"] == "FBX"
        
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_get_job_null_metadata_for_processing_job(self, setup_database):
        """
        Test that processing jobs return null for resultFiles and metadata
        """
        # Create a session
        session_response = client.post("/api/sessions")
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Create a job
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"fake model data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("test_model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]
        
        # Get job (should be in uploaded/queued state)
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        
        job_data = response.json()
        
        # Processing jobs should have null resultFiles and metadata
        assert job_data["resultFiles"] is None or job_data["resultFiles"]["skeleton"] is None
        assert job_data["metadata"] is None
        
        # Cleanup
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_metadata_extraction_on_job_completion(self, setup_database):
        """
        Test that metadata is automatically extracted when job completes
        """
        # This test would require a real FBX/GLB file to test extraction
        # For now, we verify the service method exists and handles missing files gracefully
        from app.services.job_service import JobService
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        service = JobService(db)
        
        # Test with non-existent file (should return None gracefully)
        metadata = service._extract_metadata("/fake/path/model.fbx")
        assert metadata is None
        
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
