# UniRig Web UI

A Docker-based web application for automatic 3D model rigging using UniRig. Upload your 3D models through an intuitive web interface and get rigged models ready for animation.

![UniRig UI](https://img.shields.io/badge/status-production-green)
![Docker](https://img.shields.io/badge/docker-required-blue)
![GPU](https://img.shields.io/badge/GPU-NVIDIA-76B900)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- 🎨 **Web-Based Interface** - No command-line expertise required
- 🤖 **Automatic Rigging** - AI-powered skeleton and skinning generation
- 🔍 **3D Preview** - Interactive preview of rigged models
- 📦 **Multiple Formats** - Support for OBJ, FBX, GLB, VRM
- 🐳 **Docker Deployment** - One-command installation and setup
- ⚡ **GPU Acceleration** - Fast processing with NVIDIA GPUs
- 🔄 **Background Processing** - Queue multiple rigging jobs
- 💾 **Export Options** - Download rigged models in FBX or GLB

## Quick Start

### Prerequisites

- **OS**: Ubuntu 24.04, WSL2, or any Linux with Docker support
- **GPU**: NVIDIA GPU with 8GB+ VRAM (required)
- **RAM**: 16GB minimum
- **Disk**: 50GB free space
- **Software**: 
  - Docker 24.0+ ([Install Guide](https://docs.docker.com/engine/install/))
  - Docker Compose 2.20+ ([Install Guide](https://docs.docker.com/compose/install/))
  - NVIDIA Container Toolkit ([Install Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/VAST-AI-Research/UniRig
cd UniRig
```

2. **Run the installation script**
```bash
chmod +x install.sh
./install.sh
```

The installation script will:
- ✅ Check system prerequisites (Docker, GPU, resources)
- ✅ Create necessary directories
- ✅ Generate configuration files
- ✅ Build Docker images (takes 10-15 minutes)
- ✅ Start all services
- ✅ Validate the installation

3. **Access the application**

Open your browser and navigate to:
```
http://localhost
```

## Usage

### 1. Upload a 3D Model

- Drag and drop a model file (OBJ, FBX, GLB, VRM) into the upload zone
- Or click to browse and select a file
- Supported file size: up to 100MB

### 2. Generate Skeleton

- Click **"Generate Skeleton"** after upload completes
- Wait for AI to predict the skeleton structure (1-3 minutes)
- Preview the skeleton overlaid on your mesh
- Rotate, zoom, and pan to inspect the result

### 3. Generate Skinning

- Click **"Generate Skinning"** once skeleton is approved
- Wait for skinning weight prediction (2-5 minutes)
- Preview the fully rigged model with animation
- Check weight distribution with heatmap visualization

### 4. Export Rigged Model

- Click **"Export"** and select format (FBX or GLB)
- Download the rigged model
- Import into your animation software (Blender, Maya, Unity, Unreal)

## Docker Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart a specific service
docker compose restart backend
docker compose restart worker

# View service status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f nginx
```

### Troubleshooting Commands

```bash
# Check worker GPU access
docker exec unirig-worker nvidia-smi

# Enter backend container for debugging
docker exec -it unirig-backend bash

# Check Redis connection
docker exec unirig-redis redis-cli ping

# Rebuild after code changes
docker compose build --no-cache
docker compose up -d

# Full cleanup (removes volumes)
docker compose down -v
```

## System Architecture

```
┌─────────────────┐
│  User Browser   │
│   (Port 3000)   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Nginx Proxy    │
│   (Port 80)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Backend │ │   Frontend   │
│ FastAPI │ │ React + Vite │
└────┬────┘ └──────────────┘
     │
     ├──> Redis (Message Queue)
     │
     └──> Celery Worker (GPU)
          └──> UniRig Models
```

### Docker Services

| Service | Port | Purpose | GPU |
|---------|------|---------|-----|
| **nginx** | 80, 443 | Reverse proxy, serves frontend | No |
| **backend** | 8000 | FastAPI REST API | No |
| **worker** | - | Celery background jobs | Yes |
| **redis** | 6379 | Message broker | No |

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Backend Configuration
BACKEND_PORT=8000
UPLOAD_MAX_SIZE=104857600  # 100MB

# Worker Configuration
WORKER_CONCURRENCY=1
CELERY_LOG_LEVEL=info

# Model Configuration
HF_HOME=/root/.cache/huggingface
TORCH_HOME=/root/.cache/torch
```

### Configuration File

The `config.yaml` file is generated during installation:

```yaml
system:
  python_version: "3.11"
  cuda_version: "12.1"
  gpu_available: true

paths:
  project_root: "/app"
  model_checkpoint: "/root/.cache/huggingface/hub"
  upload_dir: "/app/uploads"
  results_dir: "/app/results"

server:
  host: "0.0.0.0"
  port: 8000
  workers: 1

celery:
  broker_url: "redis://redis:6379/0"
  result_backend: "redis://redis:6379/0"
```

## Data Persistence

### Docker Volumes

- **model_cache**: UniRig model checkpoints (~5GB)
- **redis_data**: Job queue and results

### Host Directories

- **uploads/**: User-uploaded 3D models
- **results/**: Generated rigged models

### Backup & Restore

**Backup volumes:**
```bash
docker run --rm -v unirig_model_cache:/data -v $(pwd):/backup \
  alpine tar czf /backup/model_cache_backup.tar.gz /data
```

**Restore volumes:**
```bash
docker run --rm -v unirig_model_cache:/data -v $(pwd):/backup \
  alpine tar xzf /backup/model_cache_backup.tar.gz -C /
```

## Performance Tuning

### GPU Memory Optimization

If you encounter GPU out-of-memory errors:

1. **Reduce worker concurrency** (already set to 1 by default):
```yaml
# docker-compose.yml
worker:
  environment:
    - WORKER_CONCURRENCY=1
```

2. **Restart worker after each job**:
```bash
docker compose restart worker
```

### Scaling Workers

To run multiple workers (requires sufficient GPU memory):

```bash
docker compose up -d --scale worker=2
```

**Note**: Each worker requires ~4GB VRAM. Monitor with `nvidia-smi`.

## Security Considerations

- Session-based authentication with HTTPOnly cookies
- CSRF protection on all POST/PUT/DELETE requests
- File validation and MIME type checking
- Path traversal prevention
- Rate limiting (10 uploads per hour per session)
- Secure file deletion with shred utility
- Security headers (CSP, X-Frame-Options, etc.)

See [SECURITY.md](SECURITY.md) for detailed security information.

## Monitoring

### Health Checks

All services have health check endpoints:

```bash
# Backend health
curl http://localhost/api/health

# Redis health
docker exec unirig-redis redis-cli ping

# Worker GPU health
docker exec unirig-worker nvidia-smi
```

### Resource Monitoring

```bash
# View container resource usage
docker stats

# Monitor disk space
docker system df

# View service logs
docker compose logs -f
```

See [docs/MONITORING.md](docs/MONITORING.md) for comprehensive monitoring setup.

## Development

### Local Development Setup

1. **Install Python dependencies:**
```bash
cd unirig-ui/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Start backend locally:**
```bash
uvicorn app.main:app --reload --port 8000
```

3. **Start frontend development server:**
```bash
cd unirig-ui/frontend
npm install
npm run dev
```

4. **Run tests:**
```bash
cd unirig-ui/backend
pytest --cov=app --cov-report=html
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## API Documentation

FastAPI provides automatic API documentation:

- **Swagger UI**: http://localhost/api/docs
- **ReDoc**: http://localhost/api/redoc

See [API.md](API.md) for detailed endpoint specifications.

## Troubleshooting

### Common Issues

**1. Worker can't access GPU**
```bash
# Check NVIDIA Container Toolkit installation
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If fails, reinstall NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

**2. Backend won't start**
```bash
# Check logs
docker compose logs backend

# Common causes:
# - Redis not ready (wait and retry)
# - Port 8000 already in use (check with: lsof -i :8000)
```

**3. Model download fails**
```bash
# Check internet connection
ping huggingface.co

# Manually download model
docker exec -it unirig-worker bash
python -c "from inference.download import download_model_checkpoint; download_model_checkpoint()"
```

**4. Upload fails with "File too large"**
```bash
# Increase upload size limit in config.yaml
server:
  max_upload_size: 209715200  # 200MB

# Restart backend
docker compose restart backend
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

## FAQ

**Q: Can I run this without a GPU?**
A: No, UniRig requires an NVIDIA GPU for model inference. CPU-only mode is not supported.

**Q: How long does rigging take?**
A: Skeleton generation: 1-3 minutes. Skinning: 2-5 minutes. Varies by model complexity and GPU.

**Q: What's the maximum model size?**
A: Up to 100MB per file (configurable). Large models may cause GPU memory issues.

**Q: Can I run multiple jobs simultaneously?**
A: By default, only 1 job runs at a time to prevent GPU memory overflow. Increase workers if you have sufficient VRAM.

**Q: Where are the model checkpoints stored?**
A: In the Docker volume `model_cache` (~5GB). Downloaded automatically on first use.

**Q: Can I edit the generated skeleton?**
A: Not currently. Skeleton editing is planned for a future release.

## Project Structure

```
UniRig/
├── UniRig/                    # Original UniRig framework
├── unirig-ui/                 # Web UI application
│   ├── backend/               # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/          # REST API endpoints
│   │   │   ├── models/       # Database models
│   │   │   ├── services/     # Business logic
│   │   │   ├── tasks/        # Celery tasks
│   │   │   └── middleware/   # Security middleware
│   │   └── tests/            # Test suite (91% coverage)
│   └── frontend/             # React + TypeScript frontend
│       └── src/
│           ├── components/   # React components
│           ├── services/     # API clients
│           └── hooks/        # Custom React hooks
├── docker/                   # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.worker
│   ├── Dockerfile.nginx
│   └── nginx.conf
├── docker-compose.yml        # Service orchestration
├── install.sh                # Installation script
└── config.yaml               # Application configuration
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Development setup
- Code style guidelines
- Testing requirements
- Pull request process
- Community guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

UniRig framework is developed by VAST-AI-Research and distributed under its own license.

## Acknowledgments

- **UniRig Team** - VAST-AI-Research for the core rigging framework
- **Hugging Face** - For model hosting and distribution
- **Contributors** - All developers who have contributed to this project

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/VAST-AI-Research/UniRig/issues)
- **Discussions**: [GitHub Discussions](https://github.com/VAST-AI-Research/UniRig/discussions)

## Changelog

### Version 1.0.0 (2025-11-13)
- ✨ Initial release
- 🐳 Docker-based deployment
- 🎨 Web UI for model upload and preview
- 🤖 Automatic skeleton and skinning generation
- 📦 Multi-format support (OBJ, FBX, GLB, VRM)
- 🔒 Security hardening (CSRF, rate limiting, secure deletion)
- ✅ Comprehensive test suite (91% coverage)
- 📚 Complete documentation

---

**Made with ❤️ for the 3D animation community**
