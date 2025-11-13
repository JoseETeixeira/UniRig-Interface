"""
Performance tests for upload speed, processing time, and concurrent operations.
"""

import pytest
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestUploadPerformance:
    """Test upload operation performance."""
    
    def test_small_file_upload_speed(self, test_client, sample_session, mock_obj_file):
        """Test upload speed for small files (<1MB)."""
        start_time = time.time()
        
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("small_model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 2.0  # Should complete within 2 seconds
    
    def test_medium_file_upload_speed(self, test_client, sample_session, temp_upload_dir):
        """Test upload speed for medium files (10-50MB)."""
        # Create 10MB file
        medium_file = temp_upload_dir / "medium_model.obj"
        with open(medium_file, "wb") as f:
            f.write(b"v 0 0 0\n" * (10 * 1024 * 1024 // 10))
        
        start_time = time.time()
        
        with open(medium_file, "rb") as f:
            files = {"file": ("medium_model.obj", f, "model/obj")}
            response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 10.0  # Should complete within 10 seconds
    
    def test_upload_throughput(self, test_client, sample_session, mock_obj_file):
        """Test upload throughput with multiple sequential uploads."""
        upload_count = 5
        start_time = time.time()
        
        for i in range(upload_count):
            with open(mock_obj_file, "rb") as f:
                files = {"file": (f"model_{i}.obj", f, "model/obj")}
                test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": sample_session.id}
                )
        
        elapsed = time.time() - start_time
        avg_time = elapsed / upload_count
        
        assert avg_time < 1.0  # Average under 1 second per upload


class TestProcessingPerformance:
    """Test job processing performance."""
    
    @pytest.mark.skip(reason="Requires actual GPU and UniRig setup")
    def test_skeleton_generation_time(self, test_client, sample_session, mock_obj_file):
        """Test skeleton generation processing time."""
        # Upload file
        with open(mock_obj_file, "rb") as f:
            files = {"file": ("character.obj", f, "model/obj")}
            upload_response = test_client.post(
                "/api/upload",
                files=files,
                cookies={"session_id": sample_session.id}
            )
        
        file_path = upload_response.json()["path"]
        
        # Start job
        start_time = time.time()
        job_response = test_client.post(
            "/api/jobs/skeleton",
            json={"input_file": file_path},
            cookies={"session_id": sample_session.id}
        )
        
        job_id = job_response.json()["job_id"]
        
        # Poll until complete
        while True:
            status_response = test_client.get(
                f"/api/jobs/{job_id}",
                cookies={"session_id": sample_session.id}
            )
            status = status_response.json()["status"]
            
            if status in ["completed", "failed"]:
                break
            
            time.sleep(1)
        
        elapsed = time.time() - start_time
        
        # Performance baseline (varies by model complexity and GPU)
        assert elapsed < 300  # Should complete within 5 minutes


class TestConcurrentOperations:
    """Test concurrent request handling."""
    
    def test_concurrent_uploads(self, test_client, db_session, mock_obj_file):
        """Test handling concurrent uploads from multiple sessions."""
        from app.services.session_service import SessionService
        session_service = SessionService(db_session)
        
        # Create multiple sessions
        sessions = [session_service.create_session() for _ in range(3)]
        db_session.commit()
        
        def upload_for_session(session):
            with open(mock_obj_file, "rb") as f:
                files = {"file": ("model.obj", f, "model/obj")}
                return test_client.post(
                    "/api/upload",
                    files=files,
                    cookies={"session_id": session.id}
                )
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(upload_for_session, s) for s in sessions]
            results = [f.result() for f in as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        # Should complete reasonably fast even with concurrency
        assert elapsed < 5.0
    
    def test_concurrent_job_status_queries(self, test_client, sample_session, sample_job):
        """Test concurrent status queries for same job."""
        def query_status():
            return test_client.get(
                f"/api/jobs/{sample_job.id}",
                cookies={"session_id": sample_session.id}
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_status) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        # All should succeed
        assert all(r.status_code == 200 for r in results)
        # All should return same job data
        job_ids = [r.json()["id"] for r in results]
        assert all(jid == sample_job.id for jid in job_ids)


class TestMemoryUsage:
    """Test memory usage during operations."""
    
    @pytest.mark.skip(reason="Requires memory profiling setup")
    def test_memory_during_large_upload(self, test_client, sample_session):
        """Test memory usage doesn't spike during large uploads."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Upload large file
        large_content = BytesIO(b"v 0 0 0\n" * (50 * 1024 * 1024 // 10))
        files = {"file": ("large_model.obj", large_content, "model/obj")}
        
        test_client.post(
            "/api/upload",
            files=files,
            cookies={"session_id": sample_session.id}
        )
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory increase should be reasonable (not loading entire file to memory)
        assert memory_increase < 200  # Less than 200MB increase


class TestDatabasePerformance:
    """Test database query performance."""
    
    def test_list_jobs_query_performance(self, test_client, sample_session, db_session):
        """Test performance of listing jobs with many records."""
        from app.services.job_service import JobService
        job_service = JobService(db_session)
        
        # Create many jobs
        for i in range(100):
            job_service.create_job(
                sample_session.id,
                "skeleton",
                f"model_{i}.obj"
            )
        db_session.commit()
        
        start_time = time.time()
        
        response = test_client.get(
            "/api/jobs",
            cookies={"session_id": sample_session.id}
        )
        
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert len(response.json()["jobs"]) == 100
        assert elapsed < 1.0  # Should query 100 records in under 1 second
