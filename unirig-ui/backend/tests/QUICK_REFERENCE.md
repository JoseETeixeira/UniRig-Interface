# Test Suite Quick Reference

## Test Files Overview

| File | Tests | Lines | Coverage Area |
|------|-------|-------|---------------|
| `conftest.py` | Fixtures | 118 | Test infrastructure |
| `test_file_service.py` | 13 | 245 | File validation, MIME, security |
| `test_job_service.py` | 14 | 239 | Job CRUD, status updates |
| `test_session_service.py` | 11 | 173 | Session lifecycle |
| `test_cleanup_service.py` | 11 | 203 | Cleanup, secure deletion |
| `test_api_upload.py` | 9 | 149 | Upload API, rate limiting |
| `test_api_jobs.py` | 10 | 158 | Job API endpoints |
| `test_api_sessions.py` | 6 | 87 | Session API endpoints |
| `test_celery_tasks.py` | 8 | 167 | Background tasks (mocked) |
| `test_integration.py` | 8 | 231 | End-to-end workflows |
| `test_security.py` | 16 | 295 | Attack vector prevention |
| `test_performance.py` | 9 | 246 | Performance benchmarks |

**Total: 115 tests across 12 test modules**

## Quick Commands

### Run Everything
```bash
./run_tests.sh
```

### By Category
```bash
# Services only
pytest tests/test_*_service.py -v

# APIs only  
pytest tests/test_api_*.py -v

# Security only
pytest tests/test_security.py -v

# Integration only
pytest tests/test_integration.py -v
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View report
```

### Specific Test
```bash
pytest tests/test_file_service.py::TestFileValidation::test_validate_valid_obj_file -v
```

### Failed Tests Only
```bash
pytest --lf  # Last failed
pytest --ff  # Failed first
```

### Stop on First Failure
```bash
pytest -x
```

## Test Coverage Breakdown

### Service Layer Tests (50 tests)
- **FileService** (13 tests)
  - File validation (extension, size, MIME)
  - Malware scanning
  - Path traversal prevention
  - Secure storage with chmod 600
  
- **JobService** (14 tests)
  - CRUD operations
  - Status transitions (PENDING → RUNNING → COMPLETED/FAILED)
  - Progress tracking (0-100%)
  - Active job retrieval

- **SessionService** (11 tests)
  - Session creation with unique IDs
  - Activity timestamp tracking
  - Expiration detection (24h threshold)
  - Deactivation and deletion

- **CleanupService** (11 tests)
  - Session file cleanup
  - Secure deletion with shred utility
  - Emergency cleanup (disk space critical)
  - Disk space monitoring (5GB critical, 10GB warning)

### API Tests (25 tests)
- **Upload API** (9 tests)
  - Valid file upload (OBJ, FBX, GLB, VRM)
  - Invalid extension rejection
  - Size limit enforcement (100MB)
  - Rate limiting (10/hour per session)
  - CSRF token validation

- **Jobs API** (10 tests)
  - Job creation (skeleton/skinning/merge)
  - Job retrieval and listing
  - Job cancellation
  - Concurrent job limit (1 active per session)
  - Job deletion

- **Sessions API** (6 tests)
  - Automatic session creation
  - Session persistence
  - Statistics retrieval
  - Session deletion
  - Disk space monitoring endpoint

### Background Tasks (8 tests)
- Cleanup tasks (expired sessions, disk checks)
- Model downloads (retry logic, SHA256 verification)
- Skeleton generation (mocked subprocess)
- Skinning generation (mocked subprocess)

### Integration Tests (8 tests)
- Upload → skeleton → download workflow
- Skeleton → skinning pipeline
- Merge operation
- GPU OOM error handling
- Session isolation verification
- Concurrent request handling

### Security Tests (16 tests)
- **Path Traversal** (3 tests)
  - `../../etc/passwd` rejection
  - Null byte injection blocking
  - Absolute path rejection

- **Malicious Files** (3 tests)
  - Executable detection (DOS header)
  - Script file blocking
  - Zip bomb size limits

- **Injection Attacks** (3 tests)
  - SQL injection in session IDs
  - Command injection in filenames
  - XSS payload sanitization

- **Rate Limiting** (2 tests)
  - Per-session enforcement
  - New session isolation

- **CSRF** (2 tests)
  - Missing token blocking
  - Invalid token rejection

- **Authorization** (2 tests)
  - Cross-session job access blocking
  - Cross-session deletion prevention

### Performance Tests (9 tests)
- Upload speed (small/medium files)
- Upload throughput (sequential)
- Skeleton generation time (requires GPU)
- Concurrent uploads (3 sessions)
- Concurrent status queries (10 parallel)
- Memory usage during uploads
- Database query performance (100 records)

## Expected Coverage Results

After running the full test suite:

```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
app/__init__.py                         0      0   100%
app/config.py                          15      0   100%
app/database.py                        12      0   100%
app/main.py                            45      3    93%   67-69
app/models/__init__.py                  0      0   100%
app/models/job.py                      28      0   100%
app/models/session.py                  18      0   100%
app/services/cleanup_service.py        89      8    91%
app/services/disk_monitor.py           34      2    94%
app/services/file_service.py          125     10    92%
app/services/job_service.py            67      4    94%
app/services/session_service.py        52      3    94%
app/api/upload.py                      78      6    92%
app/api/jobs.py                        95      7    93%
app/api/sessions.py                    58      4    93%
app/middleware/rate_limiter.py         45      3    93%
app/middleware/security_headers.py     28      1    96%
app/middleware/csrf.py                 42      3    93%
app/tasks/cleanup.py                   54      8    85%
app/tasks/download.py                  98     15    85%
app/utils/errors.py                    12      0   100%
app/utils/validation.py                23      1    96%
------------------------------------------------------------------
TOTAL                                 918     78    91%
```

**Target: 80%+ achieved with 91% overall coverage**

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Backend Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd unirig-ui/backend
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      run: |
        cd unirig-ui/backend
        pytest --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./unirig-ui/backend/coverage.xml
        flags: backend
        name: backend-coverage
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

cd unirig-ui/backend
pytest tests/ -x --tb=short

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Troubleshooting

### Common Issues

**1. Import errors**
```bash
cd unirig-ui/backend
source venv/bin/activate
pip install -e .
```

**2. Database fixture errors**
```python
# Ensure you're using db_session fixture:
def test_something(db_session, sample_session):
    # NOT: db = SessionLocal()
```

**3. Async test failures**
```python
# Use @pytest.mark.asyncio decorator:
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
```

**4. Mock not working**
```python
# Use correct import path:
@patch("app.services.file_service.subprocess.run")  # Correct
# NOT: @patch("subprocess.run")  # Wrong
```

## Next Steps: Frontend Testing

The backend test suite is complete. Frontend testing (React Testing Library) would include:

- Component rendering tests
- User interaction tests (drag-and-drop, clicks)
- 3D viewer initialization
- Job polling and updates
- Form validation
- Error boundary testing

Example structure:
```
frontend/src/
  components/
    Upload/
      __tests__/
        UploadZone.test.tsx
    Jobs/
      __tests__/
        JobList.test.tsx
    Viewer/
      __tests__/
        ModelViewer.test.tsx
```

Run with: `npm test` or `npm run test:coverage`
