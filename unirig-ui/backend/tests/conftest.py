"""
Pytest configuration and shared fixtures for backend tests.
Provides database, test client, and mock fixtures.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models.session import SessionModel
from app.models.job import Job
from app.services.file_service import FileService
from app.services.job_service import JobService
from app.services.session_service import SessionService


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_client(db_session) -> Generator[TestClient, None, None]:
    """Create a TestClient with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_upload_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for file uploads."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def sample_session(db_session) -> SessionModel:
    """Create a sample session for testing."""
    session_service = SessionService(db_session)
    session = session_service.create_session()
    db_session.commit()
    return session


@pytest.fixture(scope="function")
def sample_job(db_session, sample_session) -> Job:
    """Create a sample job for testing."""
    job_service = JobService(db_session)
    job = job_service.create_job(
        session_id=sample_session.id,
        job_type="skeleton",
        input_file="test_model.obj"
    )
    db_session.commit()
    return job


@pytest.fixture
def mock_obj_file(temp_upload_dir) -> Path:
    """Create a mock OBJ file for testing."""
    obj_content = """# Sample OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
f 1 2 3
"""
    obj_path = temp_upload_dir / "test_model.obj"
    obj_path.write_text(obj_content)
    return obj_path


@pytest.fixture
def mock_large_file(temp_upload_dir) -> Path:
    """Create a mock file exceeding size limit."""
    large_file = temp_upload_dir / "large_file.obj"
    # Create a file larger than 100MB
    with open(large_file, "wb") as f:
        f.write(b"0" * (101 * 1024 * 1024))
    return large_file


@pytest.fixture
def mock_invalid_file(temp_upload_dir) -> Path:
    """Create a mock file with invalid extension."""
    invalid_file = temp_upload_dir / "malicious.exe"
    invalid_file.write_bytes(b"MZ\x90\x00")  # DOS header
    return invalid_file
