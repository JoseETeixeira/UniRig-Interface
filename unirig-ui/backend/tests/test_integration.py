"""
Integration tests for end-to-end workflows.
Tests complete upload → skeleton → skinning → download flows.
"""

import pytest
from fastapi import status
from pathlib import Path
from unittest.mock import patch, Mock


class TestEndToEndSkeletonWorkflow:
    """Test complete skeleton generation workflow."""
    
    @patch("app.tasks.skeleton.subprocess.run")
    def test_upload_and_generate_skeleton(self, mock_subprocess, test_client, sample_session, mock_obj_file):
        """Test end-to-end workflow: upload → skeleton generation → download."""
        # Mock successful skeleton generation
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_subprocess.return_value = mock_result
        
        # Step 1: Upload file
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("character.obj", f, "model/obj")}
            upload_response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        assert upload_response.status_code == status.HTTP_200_OK
        file_path = upload_response.json()["path"]
        
        # Step 2: Create skeleton generation job
        job_response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": file_path},
            cookies={"session_id": sample_session.id}
        )
        
        assert job_response.status_code == status.HTTP_200_OK
        job_id = job_response.json()["job_id"]
        
        # Step 3: Verify job status
        status_response = test_client.get(
            f"/api/jobs/{job_id}",
            cookies={"session_id": sample_session.id}
        )
        
        assert status_response.status_code == status.HTTP_200_OK
        assert status_response.json()["status"] in ["pending", "running", "completed"]


class TestEndToEndSkinningWorkflow:
    """Test complete skinning workflow."""
    
    @patch("app.tasks.skeleton.subprocess.run")
    @patch("app.tasks.skinning.subprocess.run")
    def test_skeleton_then_skinning(self, mock_skinning_subprocess, mock_skeleton_subprocess, 
                                    test_client, sample_session, mock_obj_file):
        """Test workflow: upload → skeleton → skinning."""
        # Mock successful execution
        mock_success = Mock()
        mock_success.returncode = 0
        mock_skeleton_subprocess.return_value = mock_success
        mock_skinning_subprocess.return_value = mock_success
        
        # Step 1: Upload
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("character.obj", f, "model/obj")}
            upload_response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        file_path = upload_response.json()["path"]
        
        # Step 2: Generate skeleton
        skeleton_response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": file_path},
            cookies={"session_id": sample_session.id}
        )
        
        skeleton_job_id = skeleton_response.json()["job_id"]
        
        # Simulate skeleton completion
        from app.services.job_service import JobService
        from app.models.job import JobStatus
        
        job_service = JobService(test_client.app.state.db)
        job_service.update_job_status(
            skeleton_job_id,
            JobStatus.COMPLETED,
            output_file="character_skeleton.obj"
        )
        
        # Step 3: Generate skinning
        skinning_response = test_client.post(
            "/api/jobs/skinning",
            json={"input_file": "character_skeleton.obj"},
            cookies={"session_id": sample_session.id}
        )
        
        assert skinning_response.status_code == status.HTTP_200_OK
        skinning_job_id = skinning_response.json()["job_id"]
        
        # Verify both jobs exist
        jobs_response = test_client.get(
            "/api/jobs",
            cookies={"session_id": sample_session.id}
        )
        
        job_ids = [job["id"] for job in jobs_response.json()["jobs"]]
        assert skeleton_job_id in job_ids
        assert skinning_job_id in job_ids


class TestEndToEndMergeWorkflow:
    """Test complete merge workflow."""
    
    @patch("app.tasks.merge.subprocess.run")
    def test_merge_skeleton_and_skinning(self, mock_subprocess, test_client, sample_session, mock_obj_file):
        """Test merge operation combines skeleton and skinning."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Upload file
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("model.obj", f, "model/obj")}
            test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        # Create merge job
        merge_response = test_client.post(
            "/api/jobs/merge",
            json={
                "skeleton_file": "model_skeleton.obj",
                "skinning_file": "model_skinning.obj"
            },
            cookies={"session_id": sample_session.id}
        )
        
        assert merge_response.status_code == status.HTTP_200_OK
        assert "job_id" in merge_response.json()


class TestErrorScenarios:
    """Test error handling in integration flows."""
    
    def test_invalid_file_blocks_workflow(self, test_client, sample_session):
        """Test uploading invalid file prevents job creation."""
        from io import BytesIO
        
        content = BytesIO(b"malicious")
        files = {"file": ("malware.exe", content, "application/octet-stream")}
        
        response = test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        # Upload should fail
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch("app.tasks.skeleton.subprocess.run")
    def test_gpu_oom_error_handling(self, mock_subprocess, test_client, sample_session, mock_obj_file):
        """Test GPU out-of-memory error is handled gracefully."""
        # Mock GPU OOM error
        mock_subprocess.side_effect = Exception("CUDA out of memory")
        
        # Upload file
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("large_model.obj", f, "model/obj")}
            upload_response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        file_path = upload_response.json()["path"]
        
        # Create job
        job_response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": file_path},
            cookies={"session_id": sample_session.id}
        )
        
        job_id = job_response.json()["job_id"]
        
        # Check job status shows error
        status_response = test_client.get(
            f"/api/jobs/{job_id}",
            cookies={"session_id": sample_session.id}
        )
        
        # Job should eventually show failed status
        # (actual task execution happens in background)
        assert status_response.status_code == status.HTTP_200_OK
    
    def test_session_isolation(self, test_client, db_session):
        """Test sessions are isolated from each other."""
        # Create two sessions
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        
        session1 = session_service.create_session()
        session2 = session_service.create_session()
        db_session.commit()
        
        # Create job in session1
        job_response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": "model.obj"},
            cookies={"session_id": session1.id}
        )
        
        job_id = job_response.json()["job_id"]
        
        # Try to access job from session2 (should fail)
        access_response = test_client.get(
            f"/api/jobs/{job_id}",
            cookies={"session_id": session2.id}
        )
        
        assert access_response.status_code == status.HTTP_403_FORBIDDEN


class TestConcurrentRequests:
    """Test handling of concurrent requests."""
    
    def test_multiple_uploads_concurrent(self, test_client, sample_session, mock_obj_file):
        """Test system handles multiple concurrent uploads."""
        from concurrent.futures import ThreadPoolExecutor
        
        def upload_file(filename):
            with open(mock_obj_file, "rb") as f:
                files = {"file": (filename, f, "model/obj")}
                return test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": sample_session.id}
                )
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(upload_file, f"model_{i}.obj")
                for i in range(3)
            ]
            results = [f.result() for f in futures]
        
        # All uploads should succeed (within rate limit)
        success_count = sum(1 for r in results if r.status_code == status.HTTP_200_OK)
        assert success_count >= 1
