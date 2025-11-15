"""
Integration tests for real-time job progress tracking (Task 3).
Tests progress updates through the full pipeline and polling capability.
"""

import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile

from app.main import app
from app.db.database import Base, get_db
from app.models.job import JobStatus, JobStage


# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_progress.db"
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


class TestJobProgressTracking:
    """Test suite for Task 3: Real-time job progress tracking"""
    
    def test_job_starts_with_zero_progress(self, setup_database):
        """
        Test that newly created jobs start with 0% progress.
        Requirement 1.1: Display progress percentage
        """
        # Create session
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        # Create a job
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test model data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        
        assert upload_response.status_code == 200
        job_data = upload_response.json()
        
        # Verify initial progress is 0
        assert job_data["progress"] == 0.0
        assert job_data["status"] == "uploaded"
        
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_polling_endpoint_returns_current_progress(self, setup_database):
        """
        Test that GET /api/jobs/{jobId} returns current progress.
        Requirement 1.6: Polling endpoint for live updates
        """
        # Create session and job
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Poll the job status
        poll_response = client.get(f"/api/jobs/{job_id}")
        
        assert poll_response.status_code == 200
        poll_data = poll_response.json()
        
        # Verify progress and status fields exist
        assert "progress" in poll_data
        assert "status" in poll_data
        assert "stage" in poll_data
        assert isinstance(poll_data["progress"], (int, float))
        assert 0 <= poll_data["progress"] <= 1.0
        
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_progress_updates_through_pipeline_phases(self, setup_database):
        """
        Test that progress updates correctly through pipeline phases.
        Requirement 1.4: Display current phase (skeleton, skinning, merge)
        """
        # Create session and job
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Manually simulate progress through phases
        from app.db.database import SessionLocal
        from app.db.models import Job as JobModel
        from app.services.job_service import JobService
        
        db = SessionLocal()
        job_service = JobService(db)
        
        # Simulate skeleton phase (30-60%)
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.SKELETON,
            progress=0.3
        )
        
        poll1 = client.get(f"/api/jobs/{job_id}")
        assert poll1.json()["progress"] == 0.3
        assert poll1.json()["stage"] == "skeleton_generation"
        assert poll1.json()["status"] == "processing"
        
        # Simulate skinning phase (60-80%)
        job_service.update_job(
            job_id=job_id,
            stage=JobStage.SKINNING,
            progress=0.8
        )
        
        poll2 = client.get(f"/api/jobs/{job_id}")
        assert poll2.json()["progress"] == 0.8
        assert poll2.json()["stage"] == "skinning_generation"
        
        # Simulate merge phase (80-95%)
        job_service.update_job(
            job_id=job_id,
            stage=JobStage.MERGE,
            progress=0.95
        )
        
        poll3 = client.get(f"/api/jobs/{job_id}")
        assert poll3.json()["progress"] == 0.95
        assert poll3.json()["stage"] == "merge"
        
        # Simulate completion (100%)
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=1.0
        )
        
        poll4 = client.get(f"/api/jobs/{job_id}")
        assert poll4.json()["progress"] == 1.0
        assert poll4.json()["status"] == "completed"
        
        db.close()
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_progress_milestones_match_specification(self, setup_database):
        """
        Test that progress milestones match the task specification:
        - Extract: 30%
        - Skeleton: 60%
        - Skinning: 80%
        - Merge: 95%
        - Complete: 100%
        """
        # Create session and job
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        from app.db.database import SessionLocal
        from app.services.job_service import JobService
        
        db = SessionLocal()
        job_service = JobService(db)
        
        # Test extract milestone (30%)
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.SKELETON,
            progress=0.3
        )
        assert client.get(f"/api/jobs/{job_id}").json()["progress"] == 0.3
        
        # Test skeleton milestone (60%)
        job_service.update_job(job_id=job_id, progress=0.6, stage=JobStage.SKELETON)
        assert client.get(f"/api/jobs/{job_id}").json()["progress"] == 0.6
        
        # Test skinning milestone (80%)
        job_service.update_job(job_id=job_id, progress=0.8, stage=JobStage.SKINNING)
        assert client.get(f"/api/jobs/{job_id}").json()["progress"] == 0.8
        
        # Test merge milestone (95%)
        job_service.update_job(job_id=job_id, progress=0.95, stage=JobStage.MERGE)
        assert client.get(f"/api/jobs/{job_id}").json()["progress"] == 0.95
        
        # Test complete milestone (100%)
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=1.0
        )
        assert client.get(f"/api/jobs/{job_id}").json()["progress"] == 1.0
        
        db.close()
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_polling_supports_5_second_interval(self, setup_database):
        """
        Test that polling endpoint can be called every 5 seconds.
        Requirement 1.6: Update progress indicator at least every 5 seconds
        """
        # Create session and job
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Simulate 3 polling requests at 5 second intervals
        # (In real test we don't actually wait, just verify it works)
        for i in range(3):
            poll_response = client.get(f"/api/jobs/{job_id}")
            assert poll_response.status_code == 200
            assert "progress" in poll_response.json()
        
        Path(tmp_path).unlink(missing_ok=True)
    
    def test_database_status_index_exists(self, setup_database):
        """
        Test that status column has database index for efficient querying.
        Task requirement: Add database index on status column
        """
        from app.db.models import Job
        
        # Check if index exists on status column
        # In SQLAlchemy, indexes are defined on Column with index=True
        status_column = Job.__table__.columns['status']
        
        # Verify index=True is set (this is already in the model)
        assert status_column.index is True
    
    def test_failed_job_reports_progress(self, setup_database):
        """
        Test that failed jobs still report their progress at failure point.
        Requirement 1.5: Display error details for failed jobs
        """
        # Create session and job
        session_response = client.post("/api/sessions")
        session_id = session_response.json()["session_id"]
        
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name
        
        upload_response = client.post(
            f"/api/sessions/{session_id}/upload",
            files={"file": ("model.glb", open(tmp_path, "rb"), "model/gltf-binary")}
        )
        job_id = upload_response.json()["job_id"]
        
        # Simulate job failing at 45% progress
        from app.db.database import SessionLocal
        from app.services.job_service import JobService
        
        db = SessionLocal()
        job_service = JobService(db)
        
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.SKELETON,
            progress=0.45
        )
        
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message="Simulated failure"
        )
        
        # Poll failed job
        poll_response = client.get(f"/api/jobs/{job_id}")
        poll_data = poll_response.json()
        
        assert poll_data["status"] == "failed"
        assert poll_data["progress"] == 0.45  # Progress preserved at failure point
        assert "error_message" in poll_data
        
        db.close()
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
