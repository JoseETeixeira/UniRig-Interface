"""
Unit tests for SessionService - session lifecycle management.
"""

import pytest
from datetime import datetime, timedelta

from app.services.session_service import SessionService
from app.models.session import SessionModel


class TestSessionCreation:
    """Test session creation."""
    
    def test_create_session(self, db_session):
        """Test creating a new session."""
        session_service = SessionService(db_session)
        
        session = session_service.create_session()
        
        assert session.id is not None
        assert len(session.id) > 0
        assert session.created_at is not None
        assert session.last_activity is not None
        assert session.is_active is True
    
    def test_create_multiple_sessions(self, db_session):
        """Test creating multiple sessions generates unique IDs."""
        session_service = SessionService(db_session)
        
        session1 = session_service.create_session()
        session2 = session_service.create_session()
        db_session.commit()
        
        assert session1.id != session2.id


class TestSessionRetrieval:
    """Test session retrieval operations."""
    
    def test_get_session_by_id(self, db_session, sample_session):
        """Test retrieving session by ID."""
        session_service = SessionService(db_session)
        
        retrieved = session_service.get_session(sample_session.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_session.id
    
    def test_get_nonexistent_session(self, db_session):
        """Test retrieving non-existent session returns None."""
        session_service = SessionService(db_session)
        
        session = session_service.get_session("nonexistent-id")
        
        assert session is None
    
    def test_get_all_sessions(self, db_session):
        """Test retrieving all sessions."""
        session_service = SessionService(db_session)
        
        # Create multiple sessions
        session1 = session_service.create_session()
        session2 = session_service.create_session()
        db_session.commit()
        
        all_sessions = session_service.get_all_sessions()
        
        assert len(all_sessions) >= 2
        session_ids = [s.id for s in all_sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids


class TestSessionActivity:
    """Test session activity tracking."""
    
    def test_update_last_activity(self, db_session, sample_session):
        """Test updating session last activity timestamp."""
        session_service = SessionService(db_session)
        
        original_time = sample_session.last_activity
        
        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        session_service.update_last_activity(sample_session.id)
        db_session.commit()
        
        updated_session = session_service.get_session(sample_session.id)
        assert updated_session.last_activity > original_time


class TestSessionExpiration:
    """Test session expiration logic."""
    
    def test_get_expired_sessions(self, db_session):
        """Test retrieving expired sessions."""
        session_service = SessionService(db_session)
        
        # Create a session and manually set it as expired
        session = session_service.create_session()
        session.last_activity = datetime.utcnow() - timedelta(hours=25)
        db_session.commit()
        
        expired_sessions = session_service.get_expired_sessions(
            expiration_hours=24
        )
        
        assert len(expired_sessions) > 0
        expired_ids = [s.id for s in expired_sessions]
        assert session.id in expired_ids
    
    def test_active_session_not_expired(self, db_session, sample_session):
        """Test active sessions are not marked as expired."""
        session_service = SessionService(db_session)
        
        expired_sessions = session_service.get_expired_sessions(
            expiration_hours=24
        )
        
        expired_ids = [s.id for s in expired_sessions]
        assert sample_session.id not in expired_ids


class TestSessionDeactivation:
    """Test session deactivation."""
    
    def test_deactivate_session(self, db_session, sample_session):
        """Test deactivating a session."""
        session_service = SessionService(db_session)
        
        session_service.deactivate_session(sample_session.id)
        db_session.commit()
        
        updated_session = session_service.get_session(sample_session.id)
        assert updated_session.is_active is False
    
    def test_deactivate_nonexistent_session(self, db_session):
        """Test deactivating non-existent session doesn't raise error."""
        session_service = SessionService(db_session)
        
        # Should not raise exception
        session_service.deactivate_session("nonexistent-id")
        db_session.commit()


class TestSessionDeletion:
    """Test session deletion."""
    
    def test_delete_session(self, db_session, sample_session):
        """Test deleting a session."""
        session_service = SessionService(db_session)
        
        session_id = sample_session.id
        session_service.delete_session(session_id)
        db_session.commit()
        
        deleted_session = session_service.get_session(session_id)
        assert deleted_session is None


class TestSessionStatistics:
    """Test session statistics."""
    
    def test_get_session_stats(self, db_session, sample_session):
        """Test retrieving session statistics."""
        from app.services.job_service import JobService
        
        session_service = SessionService(db_session)
        job_service = JobService(db_session)
        
        # Create some jobs for the session
        job_service.create_job(sample_session.id, "skeleton", "model1.obj")
        job_service.create_job(sample_session.id, "skinning", "model2.obj")
        db_session.commit()
        
        stats = session_service.get_session_stats(sample_session.id)
        
        assert stats is not None
        assert "total_jobs" in stats
        assert stats["total_jobs"] >= 2
        assert "created_at" in stats
        assert "last_activity" in stats
