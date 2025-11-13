# Troubleshooting Guide

Common issues and solutions for UniRig Web UI.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Docker Issues](#docker-issues)
3. [GPU Issues](#gpu-issues)
4. [Network Issues](#network-issues)
5. [Processing Issues](#processing-issues)
6. [Performance Issues](#performance-issues)
7. [Data Issues](#data-issues)

---

## Installation Issues

### Prerequisites Not Met

**Problem**: Installation script fails with "Docker is not installed"

**Solution**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
```

**Problem**: "Docker Compose is not installed"

**Solution**:
```bash
# Docker Compose V2 (recommended)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify
docker compose version
```

### NVIDIA Container Toolkit Issues

**Problem**: "NVIDIA Container Toolkit is not properly configured"

**Solution**:
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Insufficient Resources

**Problem**: Warning about insufficient RAM or disk space

**Solution**:
- **RAM**: Close unnecessary applications, consider upgrading to 16GB+
- **Disk**: Free up space, use external storage for uploads/results
```bash
# Check disk space
df -h

# Clean Docker cache
docker system prune -a --volumes

# Check RAM
free -h
```

---

## Docker Issues

### Container Won't Start

**Problem**: Backend container exits immediately

**Solution**:
```bash
# Check logs for errors
docker compose logs backend

# Common causes:
# 1. Redis not ready - wait and restart
docker compose restart backend

# 2. Port already in use
sudo lsof -i :8000
# Kill process using port 8000

# 3. Permission issues with volumes
sudo chown -R $USER:$USER uploads results
docker compose restart backend
```

**Problem**: Worker container won't start

**Solution**:
```bash
# Check worker logs
docker compose logs worker

# Verify GPU access
docker exec unirig-worker nvidia-smi

# If GPU not visible, check Docker GPU configuration
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Services Not Communicating

**Problem**: Backend can't connect to Redis

**Solution**:
```bash
# Check Redis status
docker compose ps redis

# Test Redis connection
docker exec unirig-redis redis-cli ping
# Should return: PONG

# Check network
docker network ls
docker network inspect unirig-network

# Restart all services
docker compose down
docker compose up -d
```

### Image Build Failures

**Problem**: Docker build fails with network timeout

**Solution**:
```bash
# Increase Docker build timeout
DOCKER_BUILDKIT=1 docker compose build --no-cache

# Use different mirror for pip packages
docker compose build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Check internet connection
ping pypi.org
```

**Problem**: Out of disk space during build

**Solution**:
```bash
# Clean up Docker images and volumes
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Check available space
docker system df
df -h /var/lib/docker
```

---

## GPU Issues

### GPU Not Detected

**Problem**: Worker can't access GPU, `nvidia-smi` fails inside container

**Solution**:
```bash
# 1. Check host GPU
nvidia-smi

# 2. Verify NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# 3. Check Docker daemon configuration
cat /etc/docker/daemon.json
# Should contain:
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia"
}

# 4. Restart Docker
sudo systemctl restart docker
docker compose down
docker compose up -d
```

### GPU Out of Memory (OOM)

**Problem**: Processing fails with "CUDA out of memory"

**Solution**:
```bash
# 1. Check GPU memory usage
nvidia-smi

# 2. Reduce worker concurrency (already set to 1)
# Edit docker-compose.yml if needed:
worker:
  environment:
    - WORKER_CONCURRENCY=1

# 3. Restart worker to clear GPU memory
docker compose restart worker

# 4. Process smaller models or reduce batch size
# For very large models (>50MB), split into chunks

# 5. Upgrade GPU if consistently hitting limits
# UniRig requires 8GB+ VRAM (12GB recommended)
```

### CUDA Version Mismatch

**Problem**: "CUDA version mismatch" or "incompatible cu version"

**Solution**:
```bash
# Check host CUDA version
nvidia-smi | grep "CUDA Version"

# Rebuild worker with correct CUDA version
# Edit docker/Dockerfile.worker:
# FROM nvidia/cuda:XX.X.0-cudnn8-runtime-ubuntu22.04

# Rebuild
docker compose build --no-cache worker
docker compose up -d worker
```

---

## Network Issues

### Can't Access Web UI

**Problem**: Browser can't connect to http://localhost

**Solution**:
```bash
# 1. Check if Nginx is running
docker compose ps nginx

# 2. Check Nginx logs
docker compose logs nginx

# 3. Verify port binding
sudo lsof -i :80
sudo netstat -tulpn | grep :80

# 4. Test backend directly
curl http://localhost:8000/api/health

# 5. Check firewall
sudo ufw status
sudo ufw allow 80/tcp

# 6. Access via IP address instead
ip addr show
# Then browse to http://<your-ip>
```

### API Requests Fail

**Problem**: Frontend shows "Network Error" or "Failed to fetch"

**Solution**:
```bash
# 1. Check backend health
curl http://localhost/api/health

# 2. Check Nginx routing
docker compose logs nginx | grep error

# 3. Verify CORS headers (if accessing from different domain)
# Edit backend app/main.py to add CORS middleware

# 4. Check browser console for errors
# Open DevTools (F12) > Console tab

# 5. Test API with curl
curl -X POST http://localhost/api/upload \
  -F "file=@test.obj" \
  -H "X-CSRF-Token: <token>"
```

### WebSocket Connection Fails

**Problem**: Real-time updates not working

**Solution**:
```bash
# 1. Check Nginx WebSocket configuration
# Verify in docker/nginx.conf:
location /ws {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
}

# 2. Restart Nginx
docker compose restart nginx

# 3. Check browser WebSocket connection
# DevTools > Network > WS filter
```

---

## Processing Issues

### Job Stuck in "Pending"

**Problem**: Jobs never start processing

**Solution**:
```bash
# 1. Check worker status
docker compose ps worker
docker compose logs worker

# 2. Verify Celery worker is running
docker exec unirig-worker celery -A app.tasks.celery_app inspect active

# 3. Check Redis connection
docker exec unirig-worker python -c "import redis; r = redis.Redis(host='redis'); print(r.ping())"

# 4. Restart worker
docker compose restart worker

# 5. Check for crashed tasks
docker compose logs worker | grep ERROR
```

### Job Fails Immediately

**Problem**: Job shows "Failed" status right after starting

**Solution**:
```bash
# 1. Check worker logs for specific error
docker compose logs worker | tail -100

# 2. Common errors:
# - File not found: Check uploads/ directory permissions
# - Model checkpoint missing: Re-download model
# - GPU OOM: Reduce model size or upgrade GPU

# 3. Test UniRig directly
docker exec -it unirig-worker bash
cd /app/UniRig
python run.py configs/task/quick_inference_skeleton_articulationxl_ar_256.yaml \
  --input /app/uploads/<session_id>/model.obj \
  --output /app/results
```

### Skeleton Generation Issues

**Problem**: Skeleton looks incorrect or malformed

**Solution**:
- **Issue**: Model scale is too large/small
  - **Fix**: Normalize model in Blender before upload
  - **Command**: Scale to fit within 2-unit cube

- **Issue**: Model is not centered
  - **Fix**: Center model at origin (0,0,0)

- **Issue**: Model has non-manifold geometry
  - **Fix**: Clean mesh in Blender (Mesh > Clean Up > Make Manifold)

- **Issue**: Multiple disconnected components
  - **Fix**: Join all meshes (Ctrl+J in Blender)

### Skinning Weight Issues

**Problem**: Deformation looks incorrect

**Solution**:
- **Issue**: Skeleton was malformed
  - **Fix**: Regenerate skeleton with cleaned mesh

- **Issue**: Model has extreme vertex density variations
  - **Fix**: Remesh model for uniform density

- **Issue**: Model has inverted normals
  - **Fix**: Recalculate normals in Blender (Shift+N)

---

## Performance Issues

### Slow Processing

**Problem**: Rigging takes much longer than expected (>10 minutes)

**Solution**:
```bash
# 1. Check GPU utilization
nvidia-smi -l 1
# Should show 80-100% GPU utilization during processing

# 2. Check if using CPU instead of GPU
docker compose logs worker | grep "CUDA"

# 3. Verify CUDA is available
docker exec unirig-worker python -c "import torch; print(torch.cuda.is_available())"

# 4. Check system load
docker stats

# 5. Reduce model complexity
# Decimate mesh in Blender before upload
```

### High Memory Usage

**Problem**: System runs out of RAM

**Solution**:
```bash
# 1. Monitor memory usage
docker stats

# 2. Limit Docker memory
# Edit /etc/docker/daemon.json:
{
  "default-ulimits": {
    "memlock": {
      "Name": "memlock",
      "Hard": 16777216000,
      "Soft": 16777216000
    }
  }
}

# 3. Restart Docker
sudo systemctl restart docker

# 4. Close unnecessary applications
# 5. Process one job at a time
```

### Slow Upload

**Problem**: File upload is very slow

**Solution**:
```bash
# 1. Check network speed
# Test with: speedtest-cli

# 2. Increase Nginx upload limits
# Edit docker/nginx.conf:
client_max_body_size 200M;
client_body_timeout 300s;

# 3. Restart Nginx
docker compose restart nginx

# 4. Use wired connection instead of WiFi
# 5. Compress model before upload (if possible)
```

---

## Data Issues

### Upload Directory Full

**Problem**: "No space left on device" during upload

**Solution**:
```bash
# 1. Check disk usage
df -h
du -sh uploads/ results/

# 2. Clean old uploads
find uploads/ -type f -mtime +7 -delete
find results/ -type f -mtime +7 -delete

# 3. Clean Docker volumes
docker system prune --volumes

# 4. Move uploads/results to external storage
# Stop services
docker compose down

# Move directories
mv uploads /mnt/external/uploads
mv results /mnt/external/results

# Create symlinks
ln -s /mnt/external/uploads uploads
ln -s /mnt/external/results results

# Restart
docker compose up -d
```

### Model Checkpoint Missing

**Problem**: "Model checkpoint not found" error

**Solution**:
```bash
# 1. Check model cache
docker exec unirig-worker ls -lh /root/.cache/huggingface/hub

# 2. Manually download model
docker exec -it unirig-worker bash
python -c "
from huggingface_hub import snapshot_download
snapshot_download('VAST-AI/UniRig-AR-350M')
"

# 3. If download fails, check internet
ping huggingface.co

# 4. Use HuggingFace mirror if blocked
export HF_ENDPOINT=https://hf-mirror.com
docker compose restart worker
```

### Corrupted Results

**Problem**: Downloaded file is corrupted or won't open

**Solution**:
```bash
# 1. Check file size
ls -lh results/<session_id>/<output_file>

# 2. Verify file integrity
file results/<session_id>/output.fbx

# 3. Check worker logs for errors during merge
docker compose logs worker | grep merge

# 4. Try different export format (GLB instead of FBX)

# 5. Re-run merge operation
docker exec -it unirig-worker bash
cd /app/UniRig/launch/inference
./merge.sh /app/uploads/<session>/model.obj \
           /app/results/<session>/skeleton.fbx \
           /app/results/<session>/skinning.fbx \
           /app/results/<session>/merged.fbx
```

---

## Advanced Debugging

### Enable Debug Logging

```bash
# Edit docker-compose.yml
worker:
  environment:
    - CELERY_LOG_LEVEL=debug
    - PYTHONUNBUFFERED=1

backend:
  environment:
    - LOG_LEVEL=debug

# Restart services
docker compose down
docker compose up -d

# Watch logs
docker compose logs -f
```

### Inspect Running Container

```bash
# Enter container shell
docker exec -it unirig-worker bash
docker exec -it unirig-backend bash

# Check Python environment
python --version
pip list

# Test imports
python -c "import torch; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available())"

# Check files
ls -la /app/uploads
ls -la /app/results
```

### Network Debugging

```bash
# Inside container, test connectivity
docker exec unirig-backend ping redis
docker exec unirig-backend nc -zv redis 6379
docker exec unirig-backend curl http://backend:8000/api/health

# Check DNS resolution
docker exec unirig-backend nslookup redis
```

---

## Getting Help

If you still have issues after trying these solutions:

1. **Check GitHub Issues**: [UniRig Issues](https://github.com/VAST-AI-Research/UniRig/issues)
2. **Search Discussions**: [GitHub Discussions](https://github.com/VAST-AI-Research/UniRig/discussions)
3. **Create New Issue**: Include:
   - Docker version: `docker --version`
   - Docker Compose version: `docker compose version`
   - GPU info: `nvidia-smi`
   - Full error logs: `docker compose logs > logs.txt`
   - Steps to reproduce
4. **Community Support**: Discord/Slack (if available)

### Useful Diagnostic Commands

```bash
# System info
docker info
docker compose version
nvidia-smi
free -h
df -h

# Service status
docker compose ps -a
docker compose logs --tail=100

# Container health
docker inspect unirig-backend | grep -A 10 Health
docker inspect unirig-worker | grep -A 10 Health

# Resource usage
docker stats --no-stream
```

---

**Last Updated**: November 13, 2025
