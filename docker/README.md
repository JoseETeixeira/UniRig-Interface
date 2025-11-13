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

The `docker-compose.yml` in the root directory orchestrates 4 services:

1. **redis**: Message broker for Celery (Redis 7 Alpine)
2. **backend**: FastAPI application (port 8000)
3. **worker**: GPU-enabled Celery worker
4. **nginx**: Reverse proxy and frontend server (port 80/443)

### Volumes
- `redis_data`: Persistent Redis data
- `model_cache`: Hugging Face model checkpoints
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
The worker service has GPU resource allocation:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## Building Images

```bash
# Build all images
docker compose build

# Build specific service
docker compose build backend
docker compose build worker
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
- NVIDIA Container Toolkit (for GPU support)
- NVIDIA GPU with CUDA 12.1 support

## Design Alignment

This infrastructure strictly follows the design specified in:
- `.kiro/specs/unirig-setup-and-ui/design.md` (Section 13: Deployment Considerations)
- Requirements 1.1-1.3 (Docker-based deployment)
- Requirements 2.1-2.2 (System validation through containerization)
