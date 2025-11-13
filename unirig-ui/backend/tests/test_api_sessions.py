"""
API endpoint tests for session management routes.
"""

import pytest
from fastapi import status


class TestSessionCreation:
    """Test session creation and initialization."""
    
    def test_create_session_automatically(self, test_client):
        """Test session is created automatically on first request."""
        response = test_client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        # Session cookie should be set
        assert "session_id" in response.cookies
    
    def test_session_persistence(self, test_client, sample_session):
        """Test session persists across requests."""
        # First request
        response1 = test_client.get(
            "/api/health",
            cookies={"session_id": sample_session.id}
        )
        
        # Second request with same session
        response2 = test_client.get(
            "/api/health",
            cookies={"session_id": sample_session.id}
        )
        
        assert response1.cookies.get("session_id") == response2.cookies.get("session_id")


class TestSessionStatistics:
    """Test session statistics endpoint."""
    
    def test_get_session_stats(self, test_client, sample_session):
        """Test retrieving session statistics."""
        response = test_client.get(
            f"/api/sessions/{sample_session.id}/stats",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_jobs" in data
        assert "created_at" in data
        assert "last_activity" in data
    
    def test_get_stats_for_nonexistent_session(self, test_client):
        """Test getting stats for non-existent session returns 404."""
        response = test_client.get(
            "/api/sessions/nonexistent-id/stats",
            cookies={"session_id": "nonexistent-id"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSessionDeletion:
    """Test session cleanup and deletion."""
    
    def test_delete_session(self, test_client, sample_session):
        """Test deleting a session."""
        response = test_client.delete(
            f"/api/sessions/{sample_session.id}",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted" in data["message"].lower()
    
    def test_delete_nonexistent_session(self, test_client):
        """Test deleting non-existent session returns 404."""
        response = test_client.delete(
            "/api/sessions/nonexistent-id",
            cookies={"session_id": "nonexistent-id"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDiskSpaceEndpoint:
    """Test disk space monitoring endpoint."""
    
    def test_get_disk_space(self, test_client, sample_session):
        """Test retrieving disk space information."""
        response = test_client.get(
            "/api/disk-space",
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "used" in data
        assert "free" in data
        assert "percent_used" in data
        assert 0 <= data["percent_used"] <= 100
    
    def test_disk_space_warning_threshold(self, test_client, sample_session):
        """Test disk space includes warning flag when low."""
        response = test_client.get(
            "/api/disk-space",
            cookies={"session_id": sample_session.id}
        )
        
        data = response.json()
        # Check warning flag exists
        assert "warning" in data or "status" in data
