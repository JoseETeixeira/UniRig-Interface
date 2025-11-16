# Deep Motion Editing Integration Guide

## Overview

This guide documents the Deep Motion Editing (DME) worker service integration for motion retargeting in UniRig UI. The DME worker enables transferring animations from a preprocessed motion dataset to newly rigged models.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       UniRig UI System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌─────────────┐          │
│  │ Frontend │───▶│ Backend  │───▶│   Redis     │          │
│  │ (React)  │    │ (FastAPI)│    │   Broker    │          │
│  └──────────┘    └──────────┘    └──────┬──────┘          │
│                                           │                  │
│                       ┌───────────────────┴────────┐        │
│                       │                            │        │
│                  ┌────▼─────┐            ┌────────▼────┐   │
│                  │  Worker  │            │ DME Worker  │   │
│                  │ (UniRig) │            │   (Motion   │   │
│                  │  + GPU   │            │ Retargeting)│   │
│                  └──────────┘            │   + GPU     │   │
│                                          └─────┬───────┘   │
│                                                │            │
│                                     ┌──────────▼─────────┐ │
│                                     │  Motion Dataset    │ │
│                                     │  Cache (5-10GB)    │ │
│                                     └────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Dockerfile.dme-worker

**Location**: `docker/Dockerfile.dme-worker`

**Features**:
- Base: NVIDIA CUDA 11.8.0 with cuDNN 8
- Miniconda for Python environment isolation
- Conda environment `dme` with Python 3.11
- PyTorch 2.3.1 with CUDA support
- Deep Motion Editing repository integration
- Celery worker for async task processing

**Key Configuration**:
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
ENV CONDA_DIR=/opt/conda
WORKDIR /app
# Clone DME repository
RUN git clone <dme-repo-url> /app/deep-motion-editing
# Create conda environment
RUN conda create -n dme python=3.11 -y
# Install PyTorch with CUDA
RUN conda install pytorch=2.3.1 pytorch-cuda=11.8 -c pytorch -c nvidia
```

### 2. Docker Compose Service

**Service Name**: `dme-worker`

**Configuration Highlights**:
```yaml
dme-worker:
  build:
    context: .
    dockerfile: docker/Dockerfile.dme-worker
  volumes:
    - motion_cache:/app/motion_cache  # Persistent motion dataset
    - ./results:/app/results          # Shared results storage
    - db_data:/app/db_data            # Shared database
  environment:
    - MOTION_CACHE_DIR=/app/motion_cache
    - DME_TIMEOUT_SECONDS=90
    - MAX_RETARGETING_CONCURRENT=1
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### 3. Celery Task Queue

**Queue Name**: `dme-retargeting`

**Purpose**: Isolates motion retargeting tasks from UniRig processing tasks

**Worker Configuration**:
```bash
celery -A app.celery_app worker -Q dme-retargeting --loglevel=info --concurrency=1
```

## Prerequisites

### System Requirements

1. **Hardware**:
   - NVIDIA GPU with CUDA 11.8+ support
   - Minimum 8GB GPU memory (16GB recommended)
   - 20GB disk space for motion cache

2. **Software**:
   - Docker 24.0+
   - Docker Compose 2.20+
   - NVIDIA Driver 525.60.13+ (for CUDA 11.8)
   - nvidia-docker2 package

### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker daemon
sudo systemctl restart docker

# Verify installation
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Expected output should show your GPU information.

## Setup and Installation

### Step 1: Verify GPU Access

```bash
# Check GPU on host
nvidia-smi

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Step 2: Update Deep Motion Editing Repository URL

Edit `docker/Dockerfile.dme-worker` line ~40:
```dockerfile
# Replace with actual DME repository URL when available
RUN git clone https://github.com/DeepMotionEditing/deep-motion-editing.git /app/deep-motion-editing
```

**Note**: If the repository requires authentication or has moved, update accordingly.

### Step 3: Build DME Worker Image

```bash
# Navigate to project root
cd /path/to/unirig-ui

# Build image (this may take 10-15 minutes)
docker compose build dme-worker
```

**Build Process**:
1. Downloads CUDA base image (~5GB)
2. Installs Miniconda (~500MB)
3. Clones DME repository
4. Creates conda environment
5. Installs PyTorch with CUDA (~2GB)
6. Installs dependencies

### Step 4: Start DME Worker

```bash
# Start only DME worker
docker compose up -d dme-worker

# Or start all services
docker compose up -d
```

### Step 5: Verify Installation

```bash
# Check service status
docker compose ps dme-worker

# View logs
docker compose logs -f dme-worker

# Verify GPU access
docker compose exec dme-worker /bin/bash -c \
  "source activate dme && python -c 'import torch; print(f\"CUDA: {torch.cuda.is_available()}\")'"

# Check DME repository
docker compose exec dme-worker ls -la /app/deep-motion-editing

# Verify Celery connection
docker compose exec dme-worker /bin/bash -c \
  "source activate dme && celery -A app.celery_app inspect ping"
```

Expected outputs:
- Status: `Up`
- GPU: `CUDA: True`
- DME repo: Directory listing with Python files
- Celery: `pong` response

## Configuration

### Environment Variables

Set in `docker-compose.yml` or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOTION_CACHE_DIR` | `/app/motion_cache` | Motion dataset cache location |
| `DME_TIMEOUT_SECONDS` | `90` | Max retargeting time per request |
| `MAX_RETARGETING_CONCURRENT` | `1` | Concurrent retargeting tasks |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Result backend URL |
| `NVIDIA_VISIBLE_DEVICES` | `all` | GPU visibility |

### Motion Dataset Configuration

The motion dataset is managed by the backend service and stored in the `motion_cache` volume.

**Initial Download** (handled by backend):
1. Backend checks for dataset in `/app/motion_cache`
2. If missing, downloads from configured Google Drive URL
3. Validates dataset integrity
4. DME worker accesses cached dataset

**Manual Pre-population** (optional):
```bash
# Download dataset locally
wget -O motion_dataset.tar.gz <google-drive-url>
tar -xzf motion_dataset.tar.gz

# Copy to Docker volume
docker compose run --rm -v $(pwd)/motion_dataset:/source dme-worker \
  bash -c "cp -r /source/* /app/motion_cache/"
```

## Usage

### Processing Flow

1. **User Action**: Select completed job → Click "Retarget Animation"
2. **Frontend**: Sends POST to `/api/retarget-motion` with jobId and motionClipId
3. **Backend**: Validates request, queues Celery task to `dme-retargeting` queue
4. **DME Worker**:
   - Receives task from queue
   - Loads target skeleton from completed model
   - Loads source motion from cached dataset
   - Invokes Deep Motion Editing retargeting
   - Saves retargeted animation to `/app/results/<session>/<job>_retargeted_<motion>.fbx`
   - Updates task status in Redis
5. **Frontend**: Polls for completion, loads retargeted animation into viewer

### Task Monitoring

```bash
# View active tasks
docker compose exec dme-worker celery -A app.celery_app inspect active

# View registered tasks
docker compose exec dme-worker celery -A app.celery_app inspect registered

# View worker statistics
docker compose exec dme-worker celery -A app.celery_app inspect stats

# Flower dashboard (if configured)
docker compose exec dme-worker celery -A app.celery_app flower
```

### GPU Monitoring

```bash
# Real-time GPU usage
watch -n 1 'docker exec unirig-dme-worker nvidia-smi'

# GPU memory timeline
docker exec unirig-dme-worker nvidia-smi dmon -s mu

# Container resource usage
docker stats unirig-dme-worker
```

## Troubleshooting

### Common Issues

#### 1. GPU Not Detected

**Symptoms**:
```
RuntimeError: No CUDA GPUs are available
NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver
```

**Solutions**:
```bash
# Check GPU on host
nvidia-smi

# Verify nvidia-docker2 is installed
dpkg -l | grep nvidia-docker

# Restart Docker daemon
sudo systemctl restart docker

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Rebuild container
docker compose build --no-cache dme-worker
docker compose up -d dme-worker
```

#### 2. Out of GPU Memory

**Symptoms**:
```
RuntimeError: CUDA out of memory. Tried to allocate X.XX GiB
```

**Solutions**:
```bash
# Reduce concurrent tasks (in docker-compose.yml)
environment:
  - MAX_RETARGETING_CONCURRENT=1

# Monitor GPU memory
nvidia-smi

# Restart container to clear GPU memory
docker compose restart dme-worker

# Check for zombie processes
docker compose exec dme-worker ps aux | grep python
```

#### 3. Conda Environment Not Activated

**Symptoms**:
```
conda: command not found
python: command not found (inside container)
```

**Solutions**:
```bash
# Check conda installation
docker compose exec dme-worker ls -la /opt/conda

# Manually activate and test
docker compose exec dme-worker /bin/bash
source /opt/conda/bin/activate dme
python --version

# Rebuild image if conda installation failed
docker compose build --no-cache dme-worker
```

#### 4. DME Repository Not Found

**Symptoms**:
```
fatal: repository 'https://...' not found
ls: cannot access '/app/deep-motion-editing': No such file or directory
```

**Solutions**:
```bash
# Update Dockerfile with correct repository URL
# Edit docker/Dockerfile.dme-worker line ~40

# Or manually clone after build
docker compose exec dme-worker /bin/bash
cd /app
git clone <actual-dme-repo-url> deep-motion-editing

# Install DME dependencies
source activate dme
cd deep-motion-editing
pip install -r requirements.txt  # if DME has requirements.txt
```

#### 5. Celery Worker Not Connecting

**Symptoms**:
```
[ERROR/MainProcess] consumer: Cannot connect to redis://redis:6379/0
```

**Solutions**:
```bash
# Check Redis is running
docker compose ps redis

# Check network connectivity
docker compose exec dme-worker ping redis

# Verify Redis URL
docker compose exec dme-worker printenv | grep REDIS

# Check Redis logs
docker compose logs redis

# Restart services
docker compose restart redis dme-worker
```

#### 6. Motion Retargeting Timeout

**Symptoms**:
```
Task exceeded time limit of 90 seconds
```

**Solutions**:
```bash
# Increase timeout in docker-compose.yml
environment:
  - DME_TIMEOUT_SECONDS=180

# Or configure in Celery task
# backend/app/tasks.py
@celery_app.task(time_limit=180)
def retarget_motion(job_id, motion_clip_id):
    ...

# Restart worker
docker compose restart dme-worker
```

### Debugging Commands

```bash
# Access container shell
docker compose exec dme-worker /bin/bash

# Activate conda environment
source activate dme

# Test imports
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"

# Check installed packages
conda list

# View worker logs with debug level
docker compose stop dme-worker
docker compose run --rm dme-worker \
  /bin/bash -c "source activate dme && celery -A app.celery_app worker -Q dme-retargeting --loglevel=debug"

# Test DME scripts directly
source activate dme
cd /app/deep-motion-editing
python <test_script>.py  # if DME provides test scripts
```

## Performance Tuning

### GPU Memory Optimization

```yaml
# docker-compose.yml adjustments
environment:
  # Use mixed precision (FP16) if DME supports it
  - TORCH_DTYPE=float16
  
  # Limit GPU memory per process
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Concurrent Task Tuning

```yaml
# For GPUs with >8GB memory, increase concurrency
environment:
  - MAX_RETARGETING_CONCURRENT=2

# Update Celery worker concurrency
# In Dockerfile.dme-worker entrypoint
ENTRYPOINT ["/bin/bash", "-c", "source activate dme && celery -A app.celery_app worker -Q dme-retargeting --loglevel=info --concurrency=2"]
```

### Batch Processing

For future optimization, DME worker can be configured to batch multiple retargeting requests:

```python
# backend/app/tasks.py (example)
@celery_app.task
def batch_retarget_motions(job_ids, motion_clip_ids):
    # Process multiple retargeting requests in a single GPU call
    # Reduces GPU context switching overhead
    pass
```

## Monitoring and Maintenance

### Health Checks

```bash
# Automated health check (runs every 30s)
docker compose exec dme-worker /bin/bash -c \
  "source activate dme && python -c 'import torch; assert torch.cuda.is_available()'"

# Manual health check script
cat > check_dme_health.sh << 'EOF'
#!/bin/bash
echo "Checking DME Worker Health..."
docker compose exec dme-worker /bin/bash -c "source activate dme && python -c '
import torch
import sys
if not torch.cuda.is_available():
    print(\"❌ CUDA not available\")
    sys.exit(1)
print(f\"✅ CUDA available: {torch.cuda.get_device_name(0)}\")
print(f\"✅ PyTorch version: {torch.__version__}\")
print(f\"✅ CUDA version: {torch.version.cuda}\")
'" && echo "✅ DME Worker is healthy"
EOF
chmod +x check_dme_health.sh
./check_dme_health.sh
```

### Regular Maintenance

```bash
# Weekly: Check GPU memory leaks
docker exec unirig-dme-worker nvidia-smi --query-gpu=memory.used --format=csv,noheader

# Weekly: Clear old task results
docker compose exec dme-worker celery -A app.celery_app purge

# Monthly: Update DME repository
docker compose exec dme-worker /bin/bash -c \
  "cd /app/deep-motion-editing && git pull origin main"
docker compose restart dme-worker

# Quarterly: Update PyTorch
# Edit Dockerfile.dme-worker with new PyTorch version
docker compose build --no-cache dme-worker
docker compose up -d dme-worker
```

### Backup and Recovery

```bash
# Backup motion cache (if customized)
docker run --rm -v unirig-ui_motion_cache:/data -v $(pwd):/backup \
  alpine tar czf /backup/motion_cache_backup.tar.gz -C /data .

# Restore motion cache
docker run --rm -v unirig-ui_motion_cache:/data -v $(pwd):/backup \
  alpine tar xzf /backup/motion_cache_backup.tar.gz -C /data

# Motion dataset is re-downloadable, so backup is optional
```

## Integration with Backend

### Celery Task Definition

**File**: `unirig-ui/backend/app/tasks.py`

```python
from celery import Celery
from app.services.motion_retargeting import retarget_motion_dme

celery_app = Celery('app')

@celery_app.task(queue='dme-retargeting', time_limit=90)
def retarget_motion(job_id: str, motion_clip_id: str) -> dict:
    """
    Retarget motion from dataset to rigged model skeleton.
    
    Args:
        job_id: Completed rigging job ID
        motion_clip_id: Motion clip ID from dataset
        
    Returns:
        dict with result_path or error
    """
    try:
        result_path = retarget_motion_dme(job_id, motion_clip_id)
        return {"status": "success", "result_path": result_path}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### API Endpoint

**File**: `unirig-ui/backend/app/api/retargeting.py`

```python
from fastapi import APIRouter, HTTPException
from app.tasks import retarget_motion

router = APIRouter()

@router.post("/retarget-motion")
async def create_retargeting_job(job_id: str, motion_clip_id: str):
    """Queue motion retargeting task"""
    task = retarget_motion.delay(job_id, motion_clip_id)
    return {"retargetingJobId": task.id, "status": "queued"}
```

## References

- **Deep Motion Editing**: [GitHub Repository](https://github.com/DeepMotionEditing/deep-motion-editing) (Update with actual URL)
- **NVIDIA Docker**: [Documentation](https://github.com/NVIDIA/nvidia-docker)
- **PyTorch CUDA**: [Installation Guide](https://pytorch.org/get-started/locally/)
- **Celery**: [Documentation](https://docs.celeryproject.org/)
- **Design Specification**: `.kiro/specs/model-viewer-and-animation/design.md` (Section: DeepMotionEditingWorker)
- **Requirements**: `.kiro/specs/model-viewer-and-animation/requirements.md` (Requirement 6: Deep Motion Editing Integration)

## Next Steps

After completing Task 21 (this setup), proceed to:

- **Task 22**: Implement motion dataset download and caching
- **Task 23**: Create retargeting API endpoints
- **Task 24**: Implement DME worker Celery tasks
- **Task 25**: Add skeleton compatibility detection
- **Task 26**: Implement motion retargeting UI
- **Task 27**: Add retargeted animation playback

These tasks build upon the DME infrastructure established in Task 21.
