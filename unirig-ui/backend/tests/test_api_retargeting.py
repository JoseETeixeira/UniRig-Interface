"""
Tests for motion retargeting API endpoints.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models import Job, MotionClip, RetargetingJob
from app.db.database import get_db


client = TestClient(app)


# Test fixtures
@pytest.fixture
def db_session():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def completed_job():
    """Mock completed job."""
    job = Mock(spec=Job)
    job.job_id = str(uuid.uuid4())
    job.session_id = str(uuid.uuid4())
    job.filename = "test_model.fbx"
    job.status = "completed"
    job.final_file = "/app/results/test_session/test_job_rigged.fbx"
    job.bone_count = 65
    return job


@pytest.fixture
def processing_job():
    """Mock processing job."""
    job = Mock(spec=Job)
    job.job_id = str(uuid.uuid4())
    job.status = "processing"
    job.final_file = None
    return job


@pytest.fixture
def humanoid_motion_clip():
    """Mock humanoid motion clip."""
    clip = Mock(spec=MotionClip)
    clip.id = "motion-humanoid-walk"
    clip.name = "Walking Forward"
    clip.skeleton_type = "humanoid"
    clip.bone_count = 65
    clip.duration = 2.5
    clip.frame_count = 75
    return clip


@pytest.fixture
def quadruped_motion_clip():
    """Mock quadruped motion clip."""
    clip = Mock(spec=MotionClip)
    clip.id = "motion-quadruped-run"
    clip.name = "Quadruped Running"
    clip.skeleton_type = "quadruped"
    clip.bone_count = 45
    clip.duration = 1.8
    clip.frame_count = 54
    return clip


class TestRetargetMotionEndpoint:
    """Test POST /api/retarget-motion endpoint."""
    
    @patch('app.api.retargeting.SkeletonExtractor')
    @patch('app.api.retargeting.check_skeleton_compatibility')
    def test_successful_retargeting_request(self, mock_compatibility, mock_extractor_class, db_session, completed_job, humanoid_motion_clip):
        """Test successful retargeting request."""
        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, humanoid_motion_clip]
        db_session.query.return_value = mock_query
        
        # Mock skeleton extractor
        mock_extractor = Mock()
        mock_extractor.extract_skeleton.return_value = {
            "bones": [{"name": "Hips"}, {"name": "Spine"}],
            "skeleton_type": "humanoid",
            "bone_count": 65
        }
        mock_extractor_class.return_value = mock_extractor
        
        # Mock compatibility check
        mock_compatibility.return_value = {
            "compatible": True,
            "compatibility_score": 0.95,
            "missing_bones": [],
            "extra_bones": [],
            "matched_bones": ["hips", "spine"],
            "skeleton_type_match": True,
            "source_type": "humanoid",
            "target_type": "humanoid",
            "details": "Excellent match"
        }
        
        # Override database dependency
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            # Make request
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": humanoid_motion_clip.id
                }
            )
            
            # Assertions
            assert response.status_code == 202
            data = response.json()
            assert "retargetingJobId" in data
            assert data["status"] == "queued"
            assert "estimatedTime" in data
            assert data["estimatedTime"] > 0
            
            # Verify database operations
            assert db_session.add.called
            assert db_session.commit.called
        
        finally:
            app.dependency_overrides.clear()
    
    def test_job_not_found(self, db_session):
        """Test error when job doesn't exist."""
        # Setup mock - job not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": str(uuid.uuid4()),
                    "motionClipId": "motion-001"
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "JOB_NOT_FOUND"
        
        finally:
            app.dependency_overrides.clear()
    
    def test_job_not_completed(self, db_session, processing_job):
        """Test error when job is not completed."""
        # Setup mock - job exists but not completed
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = processing_job
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": processing_job.job_id,
                    "motionClipId": "motion-001"
                }
            )
            
            assert response.status_code == 409
            data = response.json()
            assert data["detail"]["error"] == "JOB_NOT_COMPLETED"
            assert data["detail"]["currentStatus"] == "processing"
        
        finally:
            app.dependency_overrides.clear()
    
    def test_motion_clip_not_found(self, db_session, completed_job):
        """Test error when motion clip doesn't exist."""
        # Setup mock - job exists, motion clip doesn't
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, None]
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": "nonexistent-motion"
                }
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "MOTION_CLIP_NOT_FOUND"
        
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.api.retargeting.SkeletonExtractor')
    def test_skeleton_extraction_failure(self, mock_extractor_class, db_session, completed_job, humanoid_motion_clip):
        """Test error when skeleton extraction fails."""
        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, humanoid_motion_clip]
        db_session.query.return_value = mock_query
        
        # Mock skeleton extractor to raise exception
        mock_extractor = Mock()
        mock_extractor.extract_skeleton.side_effect = FileNotFoundError("Model file not found")
        mock_extractor_class.return_value = mock_extractor
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": humanoid_motion_clip.id
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"] == "RIGGED_MODEL_NOT_FOUND"
        
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.api.retargeting.SkeletonExtractor')
    @patch('app.api.retargeting.check_skeleton_compatibility')
    def test_skeleton_incompatibility(self, mock_compatibility, mock_extractor_class, db_session, completed_job, quadruped_motion_clip):
        """Test error when skeletons are incompatible."""
        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, quadruped_motion_clip]
        db_session.query.return_value = mock_query
        
        # Mock skeleton extractor
        mock_extractor = Mock()
        mock_extractor.extract_skeleton.return_value = {
            "bones": [{"name": "Hips"}, {"name": "Spine"}],
            "skeleton_type": "humanoid",
            "bone_count": 65
        }
        mock_extractor_class.return_value = mock_extractor
        
        # Mock compatibility check - incompatible
        mock_compatibility.return_value = {
            "compatible": False,
            "compatibility_score": 0.45,
            "missing_bones": ["tail", "frontleftleg", "frontrightleg"],
            "extra_bones": ["leftarm", "rightarm"],
            "matched_bones": ["hips", "spine"],
            "skeleton_type_match": False,
            "source_type": "quadruped",
            "target_type": "humanoid",
            "details": "Incompatible: Source is quadruped but target is humanoid"
        }
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": quadruped_motion_clip.id
                }
            )
            
            assert response.status_code == 422
            data = response.json()
            assert data["detail"]["error"] == "SKELETON_INCOMPATIBLE"
            assert "compatibility" in data["detail"]
            assert data["detail"]["compatibility"]["compatible"] is False
            assert data["detail"]["compatibility"]["compatibilityScore"] == 0.45
        
        finally:
            app.dependency_overrides.clear()
    
    @patch('app.api.retargeting.SkeletonExtractor')
    @patch('app.api.retargeting.check_skeleton_compatibility')
    def test_database_commit_failure(self, mock_compatibility, mock_extractor_class, db_session, completed_job, humanoid_motion_clip):
        """Test error when database commit fails."""
        # Setup mocks
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, humanoid_motion_clip]
        db_session.query.return_value = mock_query
        
        # Mock skeleton extractor
        mock_extractor = Mock()
        mock_extractor.extract_skeleton.return_value = {
            "bones": [{"name": "Hips"}],
            "skeleton_type": "humanoid",
            "bone_count": 65
        }
        mock_extractor_class.return_value = mock_extractor
        
        # Mock compatibility check
        mock_compatibility.return_value = {
            "compatible": True,
            "compatibility_score": 0.95,
            "missing_bones": [],
            "extra_bones": [],
            "matched_bones": ["hips"],
            "skeleton_type_match": True,
            "source_type": "humanoid",
            "target_type": "humanoid",
            "details": "Excellent match"
        }
        
        # Mock database commit failure
        db_session.commit.side_effect = Exception("Database error")
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": humanoid_motion_clip.id
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"] == "DATABASE_ERROR"
            assert db_session.rollback.called
        
        finally:
            app.dependency_overrides.clear()
    
    def test_invalid_request_format(self):
        """Test error with invalid request body."""
        response = client.post(
            "/api/retarget-motion",
            json={
                "invalid": "data"
            }
        )
        
        assert response.status_code == 422  # Validation error


class TestGetRetargetingJobStatus:
    """Test GET /api/retarget-motion/{retargetingJobId} endpoint."""
    
    def test_get_retargeting_job_success(self, db_session):
        """Test successfully retrieving retargeting job status."""
        # Create mock retargeting job
        mock_job = Mock(spec=RetargetingJob)
        mock_job.id = str(uuid.uuid4())
        mock_job.job_id = str(uuid.uuid4())
        mock_job.motion_clip_id = "motion-001"
        mock_job.status = "completed"
        mock_job.progress = 100
        mock_job.result_path = "/app/results/retargeted.fbx"
        mock_job.error = None
        mock_job.skeleton_compatibility = {
            "compatible": True,
            "compatibilityScore": 0.95
        }
        mock_job.created_at = Mock()
        mock_job.created_at.isoformat.return_value = "2025-11-14T20:10:00Z"
        mock_job.completed_at = Mock()
        mock_job.completed_at.isoformat.return_value = "2025-11-14T20:10:42Z"
        
        # Mock time delta calculation
        from datetime import timedelta
        time_diff = timedelta(seconds=42)
        mock_job.completed_at.__sub__ = Mock(return_value=time_diff)
        
        # Create mock parent job
        mock_parent_job = Mock(spec=Job)
        mock_parent_job.session_id = "test-session-123"
        mock_parent_job.job_id = mock_job.job_id
        
        # Setup mock query - return retargeting job first, then parent job
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_job, mock_parent_job]
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            # Make request with session cookie
            response = client.get(
                f"/api/retarget-motion/{mock_job.id}",
                cookies={"session_id": "test-session-123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == mock_job.id
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["resultPath"] == "/app/results/retargeted.fbx"
            assert data["skeletonCompatibility"]["compatible"] is True
            assert "processingTime" in data
        
        finally:
            app.dependency_overrides.clear()
    
    def test_get_retargeting_job_not_found(self, db_session):
        """Test error when retargeting job doesn't exist."""
        # Setup mock - job not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.get(
                f"/api/retarget-motion/{uuid.uuid4()}",
                cookies={"session_id": "test-session-123"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "RETARGETING_JOB_NOT_FOUND"
        
        finally:
            app.dependency_overrides.clear()
    
    def test_get_retargeting_job_unauthorized(self, db_session):
        """Test error when user doesn't own parent job."""
        # Create mock retargeting job
        mock_job = Mock(spec=RetargetingJob)
        mock_job.id = str(uuid.uuid4())
        mock_job.job_id = str(uuid.uuid4())
        
        # Create mock parent job with different session
        mock_parent_job = Mock(spec=Job)
        mock_parent_job.session_id = "different-session-456"
        mock_parent_job.job_id = mock_job.job_id
        
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_job, mock_parent_job]
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            # Request with different session ID
            response = client.get(
                f"/api/retarget-motion/{mock_job.id}",
                cookies={"session_id": "test-session-123"}
            )
            
            assert response.status_code == 403
            data = response.json()
            assert data["detail"]["error"] == "FORBIDDEN"
        
        finally:
            app.dependency_overrides.clear()
    
    def test_get_retargeting_job_no_session(self, db_session):
        """Test error when no session cookie provided."""
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            # Request without session cookie
            response = client.get(f"/api/retarget-motion/{uuid.uuid4()}")
            
            assert response.status_code == 401
        
        finally:
            app.dependency_overrides.clear()
    
    def test_get_retargeting_job_in_progress(self, db_session):
        """Test retrieving status of job in progress."""
        # Create mock retargeting job in processing state
        mock_job = Mock(spec=RetargetingJob)
        mock_job.id = str(uuid.uuid4())
        mock_job.job_id = str(uuid.uuid4())
        mock_job.motion_clip_id = "motion-001"
        mock_job.status = "processing"
        mock_job.progress = 45
        mock_job.result_path = None
        mock_job.error = None
        mock_job.skeleton_compatibility = {"compatible": True}
        mock_job.created_at = Mock()
        mock_job.created_at.isoformat.return_value = "2025-11-14T20:10:00Z"
        mock_job.completed_at = None
        
        # Create mock parent job
        mock_parent_job = Mock(spec=Job)
        mock_parent_job.session_id = "test-session-123"
        mock_parent_job.job_id = mock_job.job_id
        
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_job, mock_parent_job]
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.get(
                f"/api/retarget-motion/{mock_job.id}",
                cookies={"session_id": "test-session-123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing"
            assert data["progress"] == 45
            assert data["resultPath"] is None
            assert data["completedAt"] is None
        
        finally:
            app.dependency_overrides.clear()
    
    def test_get_retargeting_job_failed(self, db_session):
        """Test retrieving status of failed job."""
        # Create mock failed retargeting job
        mock_job = Mock(spec=RetargetingJob)
        mock_job.id = str(uuid.uuid4())
        mock_job.job_id = str(uuid.uuid4())
        mock_job.motion_clip_id = "motion-001"
        mock_job.status = "failed"
        mock_job.progress = 30
        mock_job.result_path = None
        mock_job.error = "Deep Motion Editing failed: GPU out of memory"
        mock_job.skeleton_compatibility = {"compatible": True}
        mock_job.created_at = Mock()
        mock_job.created_at.isoformat.return_value = "2025-11-14T20:10:00Z"
        mock_job.completed_at = Mock()
        mock_job.completed_at.isoformat.return_value = "2025-11-14T20:10:25Z"
        
        # Mock time delta
        from datetime import timedelta
        time_diff = timedelta(seconds=25)
        mock_job.completed_at.__sub__ = Mock(return_value=time_diff)
        
        # Create mock parent job
        mock_parent_job = Mock(spec=Job)
        mock_parent_job.session_id = "test-session-123"
        mock_parent_job.job_id = mock_job.job_id
        
        # Setup mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [mock_job, mock_parent_job]
        db_session.query.return_value = mock_query
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            response = client.get(
                f"/api/retarget-motion/{mock_job.id}",
                cookies={"session_id": "test-session-123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "failed"
            assert data["error"] == "Deep Motion Editing failed: GPU out of memory"
            assert data["processingTime"] == 25
        
        finally:
            app.dependency_overrides.clear()


class TestRetargetingIntegration:
    """Integration tests for retargeting workflow."""
    
    @patch('app.api.retargeting.SkeletonExtractor')
    @patch('app.api.retargeting.check_skeleton_compatibility')
    def test_full_retargeting_workflow(self, mock_compatibility, mock_extractor_class, db_session, completed_job, humanoid_motion_clip):
        """Test complete retargeting workflow from request to status check."""
        # Setup mocks for POST request
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [completed_job, humanoid_motion_clip]
        db_session.query.return_value = mock_query
        
        mock_extractor = Mock()
        mock_extractor.extract_skeleton.return_value = {
            "bones": [{"name": "Hips"}],
            "skeleton_type": "humanoid",
            "bone_count": 65
        }
        mock_extractor_class.return_value = mock_extractor
        
        mock_compatibility.return_value = {
            "compatible": True,
            "compatibility_score": 0.95,
            "missing_bones": [],
            "extra_bones": [],
            "matched_bones": ["hips"],
            "skeleton_type_match": True,
            "source_type": "humanoid",
            "target_type": "humanoid",
            "details": "Excellent match"
        }
        
        # Create retargeting job
        retargeting_job_id = str(uuid.uuid4())
        mock_retargeting_job = Mock(spec=RetargetingJob)
        mock_retargeting_job.id = retargeting_job_id
        db_session.refresh.side_effect = lambda obj: setattr(obj, 'id', retargeting_job_id)
        
        app.dependency_overrides[get_db] = lambda: db_session
        
        try:
            # Step 1: Create retargeting request
            create_response = client.post(
                "/api/retarget-motion",
                json={
                    "jobId": completed_job.job_id,
                    "motionClipId": humanoid_motion_clip.id
                }
            )
            
            assert create_response.status_code == 202
            create_data = create_response.json()
            job_id = create_data["retargetingJobId"]
            
            # Step 2: Check status (mock the GET request)
            mock_query_get = Mock()
            mock_retargeting_job.to_dict.return_value = {
                "id": job_id,
                "jobId": completed_job.job_id,
                "motionClipId": humanoid_motion_clip.id,
                "status": "queued",
                "progress": 0
            }
            mock_query_get.filter.return_value.first.return_value = mock_retargeting_job
            db_session.query.return_value = mock_query_get
            
            status_response = client.get(f"/api/retarget-motion/{job_id}")
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["id"] == job_id
            assert status_data["status"] == "queued"
        
        finally:
            app.dependency_overrides.clear()
