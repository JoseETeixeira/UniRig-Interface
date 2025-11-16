"""
API endpoint tests for motion clips routes.
"""

import pytest
from fastapi import status
from app.db.models import MotionClip
from datetime import datetime
import uuid


@pytest.fixture
def sample_motion_clips(db_session):
    """Create sample motion clips for testing."""
    clips = [
        MotionClip(
            id=str(uuid.uuid4()),
            name="Walking Forward",
            file_name="walk_forward.bvh",
            duration=2.5,
            frame_count=75,
            skeleton_type="humanoid",
            tags=["walk", "locomotion"],
            bone_count=65,
            dataset_source="test_dataset",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        MotionClip(
            id=str(uuid.uuid4()),
            name="Running Fast",
            file_name="run_fast.bvh",
            duration=1.8,
            frame_count=54,
            skeleton_type="humanoid",
            tags=["run", "locomotion"],
            bone_count=65,
            dataset_source="test_dataset",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        MotionClip(
            id=str(uuid.uuid4()),
            name="Dog Walk",
            file_name="dog_walk.bvh",
            duration=3.0,
            frame_count=90,
            skeleton_type="quadruped",
            tags=["walk", "locomotion", "animal"],
            bone_count=42,
            dataset_source="test_dataset",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        MotionClip(
            id=str(uuid.uuid4()),
            name="Jump High",
            file_name="jump_high.bvh",
            duration=1.2,
            frame_count=36,
            skeleton_type="humanoid",
            tags=["jump", "aerial"],
            bone_count=65,
            dataset_source="test_dataset",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
    ]
    
    for clip in clips:
        db_session.add(clip)
    db_session.commit()
    
    return clips


class TestMotionClipsList:
    """Test motion clips listing endpoint."""
    
    def test_list_all_motion_clips(self, test_client, sample_motion_clips):
        """Test listing all motion clips without filters."""
        response = test_client.get("/api/motion-clips")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "clips" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        assert data["total"] == 4
        assert len(data["clips"]) == 4
        assert data["limit"] == 50
        assert data["offset"] == 0
    
    def test_filter_by_skeleton_type_humanoid(self, test_client, sample_motion_clips):
        """Test filtering motion clips by humanoid skeleton type."""
        response = test_client.get("/api/motion-clips?skeleton_type=humanoid")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 3
        for clip in data["clips"]:
            assert clip["skeletonType"] == "humanoid"
    
    def test_filter_by_skeleton_type_quadruped(self, test_client, sample_motion_clips):
        """Test filtering motion clips by quadruped skeleton type."""
        response = test_client.get("/api/motion-clips?skeleton_type=quadruped")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 1
        assert data["clips"][0]["skeletonType"] == "quadruped"
        assert data["clips"][0]["name"] == "Dog Walk"
    
    def test_filter_by_invalid_skeleton_type(self, test_client, sample_motion_clips):
        """Test filtering with invalid skeleton type returns 400."""
        response = test_client.get("/api/motion-clips?skeleton_type=invalid")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "INVALID_SKELETON_TYPE"
    
    def test_filter_by_tags(self, test_client, sample_motion_clips):
        """Test filtering motion clips by tags."""
        response = test_client.get("/api/motion-clips?tags=locomotion")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 3
        for clip in data["clips"]:
            assert "locomotion" in clip["tags"]
    
    def test_filter_by_multiple_tags(self, test_client, sample_motion_clips):
        """Test filtering by multiple tags (comma-separated)."""
        response = test_client.get("/api/motion-clips?tags=aerial,jump")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] >= 1
        # Should include clips with either 'aerial' OR 'jump' tags
    
    def test_pagination_limit(self, test_client, sample_motion_clips):
        """Test pagination with custom limit."""
        response = test_client.get("/api/motion-clips?limit=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 4
        assert len(data["clips"]) == 2
        assert data["limit"] == 2
    
    def test_pagination_offset(self, test_client, sample_motion_clips):
        """Test pagination with offset."""
        response = test_client.get("/api/motion-clips?limit=2&offset=2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 4
        assert len(data["clips"]) == 2
        assert data["offset"] == 2
    
    def test_pagination_limits_validation(self, test_client, sample_motion_clips):
        """Test pagination limit validation (max 100)."""
        response = test_client.get("/api/motion-clips?limit=200")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_combined_filters(self, test_client, sample_motion_clips):
        """Test combining skeleton type and tag filters."""
        response = test_client.get("/api/motion-clips?skeleton_type=humanoid&tags=locomotion")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["total"] == 2
        for clip in data["clips"]:
            assert clip["skeletonType"] == "humanoid"
            assert "locomotion" in clip["tags"]
    
    def test_empty_dataset_returns_503(self, test_client, db_session):
        """Test that empty dataset returns 503 Service Unavailable."""
        # Don't add any clips to database
        response = test_client.get("/api/motion-clips")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "DATASET_NOT_READY"
    
    def test_response_structure(self, test_client, sample_motion_clips):
        """Test that response includes all required fields."""
        response = test_client.get("/api/motion-clips?limit=1")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        clip = data["clips"][0]
        required_fields = [
            "id", "name", "fileName", "duration", "frameCount",
            "skeletonType", "tags", "boneCount", "datasetSource",
            "createdAt", "updatedAt"
        ]
        
        for field in required_fields:
            assert field in clip


class TestGetMotionClip:
    """Test getting individual motion clip details."""
    
    def test_get_existing_clip(self, test_client, sample_motion_clips):
        """Test retrieving a specific motion clip by ID."""
        clip_id = sample_motion_clips[0].id
        response = test_client.get(f"/api/motion-clips/{clip_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == clip_id
        assert data["name"] == "Walking Forward"
        assert data["skeletonType"] == "humanoid"
    
    def test_get_nonexistent_clip(self, test_client, sample_motion_clips):
        """Test retrieving a non-existent motion clip returns 404."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/motion-clips/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "MOTION_CLIP_NOT_FOUND"
