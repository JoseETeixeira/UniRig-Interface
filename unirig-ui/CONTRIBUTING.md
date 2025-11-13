# Contributing to UniRig Web UI

Thank you for your interest in contributing! This guide will help you get started.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Development Workflow](#development-workflow)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Testing Requirements](#testing-requirements)
7. [Pull Request Process](#pull-request-process)
8. [Project Structure](#project-structure)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, religion, or nationality.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Trolling, insulting/derogatory comments, personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose
- Git
- NVIDIA GPU with CUDA support (for testing worker functionality)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
```bash
git clone https://github.com/YOUR_USERNAME/UniRig
cd UniRig
```

3. Add upstream remote:
```bash
git remote add upstream https://github.com/VAST-AI-Research/UniRig
```

## Development Setup

### Backend Setup

```bash
cd unirig-ui/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black flake8 mypy pytest pytest-asyncio pytest-cov

# Run backend locally
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd unirig-ui/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Docker Development

```bash
# Build and start all services
docker compose up --build

# Or build specific service
docker compose build backend
docker compose up backend

# Watch logs
docker compose logs -f backend
```

## Development Workflow

### 1. Create a Branch

Always create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### 2. Make Changes

- Write clean, readable code
- Follow the style guidelines
- Add tests for new functionality
- Update documentation as needed
- Commit early and often

### 3. Write Good Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): short description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(backend): add batch export endpoint

Implements batch export functionality allowing users to download
multiple rigged models in a single ZIP file.

Closes #42
```

```
fix(frontend): prevent duplicate job creation

Added debounce to job creation button to prevent accidental
duplicate submissions.

Fixes #56
```

### 4. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

If there are conflicts, resolve them and continue:
```bash
# After resolving conflicts
git add .
git rebase --continue
```

## Code Style Guidelines

### Python (Backend)

**Style**: Follow [PEP 8](https://pep8.org/)

**Formatter**: Black (line length: 88)
```bash
black app/
```

**Linter**: Flake8
```bash
flake8 app/ --max-line-length=88 --extend-ignore=E203
```

**Type Hints**: Use type hints for all functions
```python
from typing import Optional, List
from app.models.job import Job

def get_jobs_for_session(
    session_id: str,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Job]:
    """Get all jobs for a session."""
    # Implementation
```

**Docstrings**: Use Google-style docstrings
```python
def create_job(session_id: str, job_type: str, input_file: str) -> Job:
    """Create a new rigging job.
    
    Args:
        session_id: Unique session identifier
        job_type: Type of job (skeleton, skinning, merge)
        input_file: Path to input model file
        
    Returns:
        Job object with unique ID and pending status
        
    Raises:
        ValueError: If job_type is invalid
        FileNotFoundError: If input_file doesn't exist
    """
    pass
```

**Naming Conventions:**
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### TypeScript/React (Frontend)

**Style**: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

**Formatter**: Prettier
```bash
npm run format
```

**Linter**: ESLint
```bash
npm run lint
```

**Type Safety**: Use TypeScript strictly
```typescript
interface JobStatus {
  jobId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
}

const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get<JobStatus>(`/jobs/${jobId}`);
  return response.data;
};
```

**Component Structure:**
```typescript
import React, { useState, useEffect } from 'react';

interface Props {
  jobId: string;
  onComplete: (result: string) => void;
}

export const JobStatusCard: React.FC<Props> = ({ jobId, onComplete }) => {
  const [status, setStatus] = useState<JobStatus | null>(null);
  
  useEffect(() => {
    // Component logic
  }, [jobId]);
  
  return (
    <div className="job-status-card">
      {/* JSX */}
    </div>
  );
};
```

**Naming Conventions:**
- Components: `PascalCase`
- Files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- CSS classes: `kebab-case`

### Docker

**Dockerfile best practices:**
- Use specific base image versions
- Minimize layers with multi-line RUN commands
- Order layers from least to most frequently changing
- Use `.dockerignore` to exclude unnecessary files
- Clean up in same layer: `apt-get install && rm -rf /var/lib/apt/lists/*`

### Git

**Commit Guidelines:**
- Keep commits atomic (one logical change per commit)
- Write descriptive commit messages
- Reference issue numbers in commits
- Don't commit sensitive data (credentials, keys)
- Use `.gitignore` properly

## Testing Requirements

### Backend Tests

**Minimum Requirements:**
- All new features must have unit tests
- Bug fixes must include regression tests
- Maintain 80%+ code coverage
- All tests must pass before PR

**Running Tests:**
```bash
cd unirig-ui/backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_file_service.py

# Run specific test
pytest tests/test_file_service.py::TestFileValidation::test_validate_valid_obj_file
```

**Test Structure:**
```python
import pytest
from app.services.job_service import JobService

class TestJobCreation:
    """Test job creation functionality."""
    
    def test_create_skeleton_job(self, db_session, sample_session):
        """Test creating a skeleton generation job."""
        job_service = JobService(db_session)
        
        job = job_service.create_job(
            session_id=sample_session.id,
            job_type="skeleton",
            input_file="model.obj"
        )
        
        assert job.id is not None
        assert job.type == JobType.SKELETON
        assert job.status == JobStatus.PENDING
```

### Frontend Tests

**Requirements:**
- Component rendering tests
- User interaction tests
- Integration tests for API calls

**Running Tests:**
```bash
cd unirig-ui/frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Integration Tests

Test complete workflows end-to-end:
```python
def test_complete_rigging_workflow(test_client, mock_obj_file):
    """Test upload → skeleton → skinning → download."""
    # Upload
    upload_response = test_client.post('/api/upload', files=...)
    
    # Create job
    job_response = test_client.post('/api/jobs/skeleton', json=...)
    
    # Wait for completion
    # ...
    
    # Download result
    result = test_client.get('/results/...')
    assert result.status_code == 200
```

## Pull Request Process

### Before Submitting

1. **Run tests**:
```bash
# Backend
cd unirig-ui/backend
pytest --cov=app

# Frontend
cd unirig-ui/frontend
npm test
```

2. **Check code style**:
```bash
# Backend
black app/
flake8 app/

# Frontend
npm run lint
npm run format
```

3. **Update documentation**: If you changed APIs or added features

4. **Test locally**: Ensure everything works in Docker environment
```bash
docker compose down -v
docker compose up --build
```

### Submitting PR

1. **Push your branch**:
```bash
git push origin feature/your-feature-name
```

2. **Create PR on GitHub**:
   - Go to your fork on GitHub
   - Click "Pull Request"
   - Select your branch
   - Fill in the template

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Tested in Docker environment
- [ ] Tested on GPU hardware (if applicable)

## Screenshots
(If UI changes)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex sections
- [ ] Updated documentation
- [ ] No warnings from linters
- [ ] Tests pass locally
- [ ] Added/updated tests

## Related Issues
Fixes #123
Relates to #456
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linters
2. **Code Review**: Maintainers review code
3. **Feedback**: Address review comments
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainer merges PR

### After PR is Merged

1. **Delete branch**:
```bash
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

2. **Update local main**:
```bash
git checkout main
git pull upstream main
```

## Project Structure

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── api/                 # API endpoints
│   │   ├── upload.py
│   │   ├── jobs.py
│   │   └── sessions.py
│   ├── models/              # Database models
│   │   ├── job.py
│   │   └── session.py
│   ├── services/            # Business logic
│   │   ├── file_service.py
│   │   ├── job_service.py
│   │   └── session_service.py
│   ├── tasks/               # Celery tasks
│   │   ├── celery_app.py
│   │   ├── skeleton.py
│   │   └── skinning.py
│   ├── middleware/          # Security middleware
│   │   ├── rate_limiter.py
│   │   ├── csrf.py
│   │   └── security_headers.py
│   └── utils/               # Utilities
│       ├── errors.py
│       └── validation.py
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_file_service.py
│   └── ...
└── requirements.txt
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Upload/
│   │   ├── Jobs/
│   │   ├── Viewer/
│   │   └── Common/
│   ├── services/            # API clients
│   │   └── api.ts
│   ├── hooks/               # Custom hooks
│   │   ├── useJobs.ts
│   │   └── useWebSocket.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Utilities
│   │   └── formatters.ts
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
└── package.json
```

## Areas for Contribution

### High Priority

- [ ] Manual skeleton editing UI
- [ ] Batch processing for multiple models
- [ ] Advanced 3D viewer controls (bone manipulation)
- [ ] Export format options (COLLADA, USD)
- [ ] Cloud deployment guides (AWS, GCP, Azure)

### Medium Priority

- [ ] Model comparison view (before/after)
- [ ] Animation playback in preview
- [ ] Mobile-responsive UI
- [ ] Dark mode theme
- [ ] Internationalization (i18n)

### Documentation

- [ ] Video tutorials
- [ ] More API examples
- [ ] Blender integration guide
- [ ] Unity/Unreal import guide
- [ ] Performance optimization guide

### Testing

- [ ] E2E tests with Playwright
- [ ] Frontend component tests
- [ ] Load testing scripts
- [ ] Security penetration testing

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/VAST-AI-Research/UniRig/discussions)
- **Bugs**: [GitHub Issues](https://github.com/VAST-AI-Research/UniRig/issues)
- **Chat**: Discord (if available)
- **Email**: Contact maintainers for sensitive issues

## Recognition

Contributors will be recognized in:
- `README.md` acknowledgments section
- Release notes for their contributions
- `CONTRIBUTORS.md` (if created)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to UniRig Web UI!** 🎉
