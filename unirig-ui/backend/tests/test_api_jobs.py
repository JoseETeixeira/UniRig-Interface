"""
API endpoint tests for job management routes.
"""

import pytest
from fastapi import status


class TestJobCreation:
    """Test job creation endpoints."""
    
    def test_create_skeleton_job(self, test_client, sample_session, mock_obj_file):
        """Test creating a skeleton generation job."""
        # First upload a file
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            upload_response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        file_path = upload_response.json()["path"]
        
        # Create skeleton job
        response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": file_path},
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "pending"
    
    def test_create_skinning_job(self, test_client, sample_session):
        """Test creating a skinning job."""
        response = test_client.post(
            "/api/jobs/skinning",
            json={"input_file": "model_with_skeleton.obj"},
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"
    
    def test_create_merge_job(self, test_client, sample_session):
        """Test creating a merge job."""
        response = test_client.post(
            "/api/jobs/merge",
            json={"input_file": "model.obj"},
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "pending"


class TestJobRetrieval:
    """Test job retrieval endpoints."""
    
    def test_get_job_by_id(self, test_client, sample_session, sample_job):
        """Test retrieving a specific job."""
        response = test_client.get(
            f"/api/jobs/{sample_job.id}",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_job.id
        assert data["status"] == sample_job.status.value
    
    def test_get_nonexistent_job(self, test_client, sample_session):
        """Test retrieving non-existent job returns 404."""
        response = test_client.get(
            "/api/jobs/nonexistent-id",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_list_session_jobs(self, test_client, sample_session):
        """Test listing all jobs for a session."""
        # Create multiple jobs
        for i in range(3):
            test_client.post(
                "/api/jobs/skeleton",
                json={"input_file": f"model_{i}.obj"},
                cookies={"session_id": sample_session.id}
            )
        
        response = test_client.get(
            "/api/jobs",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["jobs"]) >= 3


class TestJobCancellation:
    """Test job cancellation."""
    
    def test_cancel_pending_job(self, test_client, sample_session, sample_job):
        """Test cancelling a pending job."""
        response = test_client.post(
            f"/api/jobs/{sample_job.id}/cancel",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"
    
    def test_cancel_completed_job_fails(self, test_client, sample_session, sample_job):
        """Test cancelling completed job returns error."""
        # First complete the job
        from app.services.job_service import JobService
        from app.models.job import JobStatus
        
        job_service = JobService(test_client.app.state.db)
        job_service.update_job_status(sample_job.id, JobStatus.COMPLETED)
        
        response = test_client.post(
            f"/api/jobs/{sample_job.id}/cancel",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestConcurrentJobLimits:
    """Test concurrent job limits."""
    
    def test_concurrent_job_limit_enforced(self, test_client, sample_session):
        """Test only one active job allowed per session."""
        # Create first job
        response1 = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": "model1.obj"},
            cookies={"session_id": sample_session.id}
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to create second job (should fail)
        response2 = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": "model2.obj"},
            cookies={"session_id": sample_session.id}
        )
        
        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "concurrent job limit" in response2.json()["detail"].lower()


class TestJobDeletion:
    """Test job deletion."""
    
    def test_delete_job(self, test_client, sample_session, sample_job):
        """Test deleting a job."""
        response = test_client.delete(
            f"/api/jobs/{sample_job.id}",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify job is deleted
        get_response = test_client.get(
            f"/api/jobs/{sample_job.id}",
            cookies={"session_id": sample_session.id}
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
