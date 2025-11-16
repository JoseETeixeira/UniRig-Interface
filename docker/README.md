# Docker Infrastructure for UniRig UI

This directory contains the Docker configuration for the UniRig UI application.

## Files

### Dockerfile.backend
- **Base Image**: `python:3.11-slim`
- **Purpose**: FastAPI backend application server
- **Port**: 8000
- **Features**:
  - System dependencies (curl, git)
  - FastAPI and backend requirements
  - Backend application code
  - Upload and results directories

### Dockerfile.worker
- **Base Image**: `nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04`
- **Purpose**: GPU-enabled Celery worker for UniRig processing
- **Features**:
  - Python 3.11 installation
  - CUDA 12.1 support
  - PyTorch with CUDA
  - UniRig dependencies (spconv, torch_scatter, torch_cluster)
  - Celery for background task processing
  - GPU access for model inference

### Dockerfile.dme-worker
- **Base Image**: `nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04`
- **Purpose**: GPU-enabled Celery worker for Deep Motion Editing (motion retargeting)
- **Features**:
  - Miniconda for environment management
  - Python 3.11 conda environment
  - PyTorch 2.3.1 with CUDA 11.8
  - Deep Motion Editing repository integration
  - Motion processing dependencies (NumPy, SciPy, trimesh)
  - Dedicated Celery queue for retargeting tasks
  - GPU access for accelerated motion retargeting

### Dockerfile.nginx
- **Multi-stage Build**:
  1. **Stage 1**: Node 18 Alpine - Build React frontend
  2. **Stage 2**: Nginx Alpine - Serve static files and reverse proxy
- **Port**: 80, 443
- **Purpose**: Reverse proxy and static file server

### nginx.conf
- **Configuration**:
  - Reverse proxy to backend (port 8000)
  - WebSocket support for real-time updates
  - 100MB max upload size
  - Static file serving for frontend
  - Result file download endpoints
  - Extended timeouts for long-running operations (300s)

## Docker Compose Services

The `docker-compose.yml` in the root directory orchestrates 5 services:

1. **redis**: Message broker for Celery (Redis 7 Alpine)
2. **backend**: FastAPI application (port 8000)
3. **worker**: GPU-enabled Celery worker for UniRig processing
4. **dme-worker**: GPU-enabled Celery worker for Deep Motion Editing (motion retargeting)
5. **nginx**: Reverse proxy and static file server (port 80/443)
4. **nginx**: Reverse proxy and frontend server (port 80/443)

### Volumes
- `redis_data`: Persistent Redis data
- `model_cache`: Hugging Face model checkpoints
- `motion_cache`: Deep Motion Editing preprocessed motion dataset (~5-10GB)
- `db_data`: SQLite database files
- `./uploads`: User-uploaded 3D models (host-mounted)
- `./results`: Generated rigging results (host-mounted)

### Networks
- `unirig-network`: Internal network for service communication

### Health Checks
All services have configured health checks for automatic recovery:
- **redis**: `redis-cli ping` every 10s
- **backend**: `curl /api/health` every 30s
- **nginx**: `curl /api/health` (proxied) every 30s

### GPU Configuration
Both worker and dme-worker services have GPU resource allocation:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

The `worker` service uses GPU for UniRig skeleton/skinning inference.
The `dme-worker` service uses GPU for Deep Motion Editing retargeting operations.

## Building Images

```bash
# Build all images
docker compose build

# Build specific service
docker compose build backend
docker compose build worker
docker compose build dme-worker
docker compose build nginx
```

## Running Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f worker

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Requirements

- Docker 24.0+
- Docker Compose 2.20+
- NVIDIA Container Toolkit (nvidia-docker2)
- NVIDIA GPU with CUDA 11.8+ support (for dme-worker)
- NVIDIA GPU with CUDA 12.1+ support (for worker)

### Installing NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## Deep Motion Editing Worker

For detailed information about the DME worker service, see:
- [Deep Motion Editing Setup Guide](./DME_SETUP.md) (comprehensive setup and troubleshooting)
- Docker service: `dme-worker` in `docker-compose.yml`
- Dockerfile: `docker/Dockerfile.dme-worker`

### Quick Start DME Worker

```bash
# Build DME worker image
docker compose build dme-worker

# Start DME worker
docker compose up -d dme-worker

# Verify DME worker is running
docker compose ps dme-worker
docker compose logs -f dme-worker

# Test GPU access
docker compose exec dme-worker /bin/bash -c \
  "source activate dme && python -c 'import torch; print(torch.cuda.is_available())'"
```

## Design Alignment

This infrastructure strictly follows the design specified in:
- `.kiro/specs/unirig-setup-and-ui/design.md` (Section 13: Deployment Considerations)
- Requirements 1.1-1.3 (Docker-based deployment)
- Requirements 2.1-2.2 (System validation through containerization)
