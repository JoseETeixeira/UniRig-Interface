# Backend Test Suite

Comprehensive testing suite for UniRig UI backend with unit, integration, security, and performance tests.

## Test Coverage

### Unit Tests

**Service Layer (`test_*_service.py`)**
- `test_file_service.py` - File validation, MIME checking, malware scanning, path traversal prevention, secure storage
- `test_job_service.py` - Job CRUD operations, status management, progress tracking
- `test_session_service.py` - Session lifecycle, activity tracking, expiration, statistics
- `test_cleanup_service.py` - Session cleanup, secure deletion, disk monitoring

**API Endpoints (`test_api_*.py`)**
- `test_api_upload.py` - File upload, rate limiting, CSRF protection
- `test_api_jobs.py` - Job creation, retrieval, cancellation, concurrent limits
- `test_api_sessions.py` - Session management, statistics, disk space monitoring

**Background Tasks (`test_celery_tasks.py`)**
- Cleanup tasks with mocked services
- Model download tasks with retry logic
- Skeleton/skinning generation with mocked subprocess calls

### Integration Tests (`test_integration.py`)

- End-to-end upload → skeleton → skinning → download workflows
- Error scenario handling (invalid files, GPU OOM, network errors)
- Session isolation verification
- Concurrent request handling

### Security Tests (`test_security.py`)

- Path traversal attack prevention
- Malicious file upload blocking
- SQL/Command/XSS injection prevention
- Rate limiting bypass attempts
- CSRF protection enforcement
- Authorization bypass attempts

### Performance Tests (`test_performance.py`)

- Upload speed benchmarks (small/medium/large files)
- Processing time measurements
- Concurrent operation handling
- Memory usage profiling
- Database query performance

## Running Tests

### Run All Tests

```bash
./run_tests.sh
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_*_service.py -v

# Integration tests
pytest tests/test_integration.py -v

# Security tests
pytest tests/test_security.py -v

# API tests
pytest tests/test_api_*.py -v
```

### Run with Coverage Report

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

Coverage report will be generated at `htmlcov/index.html`.

### Run Specific Test

```bash
pytest tests/test_file_service.py::TestFileValidation::test_validate_valid_obj_file -v
```

## Test Configuration

### pytest Configuration (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "-v",
    "--cov=app",
    "--cov-report=html",
    "--cov-branch",
]
```

### Coverage Configuration

- **Target**: 80%+ code coverage
- **Source**: `app/` directory
- **Omit**: `tests/`, `venv/`, `__pycache__/`
- **Reports**: HTML (htmlcov/) and terminal output

## Test Fixtures (`conftest.py`)

### Database Fixtures

- `db_engine` - In-memory SQLite database
- `db_session` - Fresh database session per test
- `test_client` - FastAPI TestClient with database override

### Mock Data Fixtures

- `sample_session` - Pre-created session
- `sample_job` - Pre-created job
- `mock_obj_file` - Sample OBJ file
- `mock_large_file` - File exceeding size limit
- `mock_invalid_file` - Malicious file with DOS header
- `temp_upload_dir` - Temporary upload directory

## Writing New Tests

### Unit Test Template

```python
"""Test description."""

import pytest
from app.services.your_service import YourService


class TestFeatureName:
    """Test feature description."""
    
    def test_specific_behavior(self, db_session, sample_session):
        """Test what specific behavior does."""
        service = YourService(db_session)
        
        result = service.do_something(sample_session.id)
        
        assert result is not None
        assert result.status == "expected"
```

### API Test Template

```python
"""Test API endpoint."""

import pytest
from fastapi import status


class TestYourEndpoint:
    """Test endpoint description."""
    
    def test_endpoint_success(self, test_client, sample_session):
        """Test successful request."""
        response = test_client.post(
            "/api/your-endpoint",
            json={"key": "value"},
            cookies={"session_id": sample_session.id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "expected_field" in response.json()
```

## Continuous Integration

### Pre-commit Hooks

Run tests before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit
./run_tests.sh
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Markers

Mark tests for selective execution:

```python
@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.integration
def test_end_to_end_flow():
    pass
```

Run marked tests:

```bash
# Run only fast tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

## Mocking Guidelines

### Mock External Services

```python
@patch("app.tasks.skeleton.subprocess.run")
def test_with_mock(mock_subprocess):
    mock_subprocess.return_value = Mock(returncode=0)
    # Test implementation
```

### Mock Database for Celery Tests

```python
@patch("app.tasks.cleanup.SessionService")
def test_celery_task(mock_service):
    mock_service.return_value.get_expired_sessions.return_value = []
    # Test implementation
```

## Debugging Failed Tests

### Verbose Output

```bash
pytest -vv --tb=long
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Debug with PDB

```python
import pytest

def test_something():
    value = compute()
    pytest.set_trace()  # Drop into debugger
    assert value == expected
```

## Coverage Targets

- **Overall**: 80%+ code coverage
- **Critical Paths**: 95%+ (file validation, security, session management)
- **API Endpoints**: 90%+
- **Service Layer**: 85%+
- **Background Tasks**: 75%+ (due to subprocess mocking complexity)

## Known Limitations

- Some performance tests require actual GPU setup (marked with `@pytest.mark.skip`)
- Celery tasks use mocked subprocess calls (not testing actual UniRig execution)
- Frontend tests not included (separate React Testing Library setup needed)
- E2E tests with Playwright/Cypress planned for future

## Troubleshooting

### Import Errors

Ensure you're in the backend directory and virtual environment is activated:

```bash
cd unirig-ui/backend
source venv/bin/activate
```

### Database Errors

Tests use in-memory SQLite. If you see database errors, check:
- SQLAlchemy models are properly imported
- Database fixtures are used correctly
- Transactions are committed where needed

### Async Test Failures

Ensure async tests use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
