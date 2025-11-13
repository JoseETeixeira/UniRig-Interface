#!/bin/bash

set -e

echo "=== UniRig UI Installation Script ==="
echo ""

# Check prerequisites
check_prerequisites() {
    echo "[1/7] Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed."
        echo "Install Docker: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    # Verify Docker version (24.0+)
    docker_version=$(docker --version | grep -oP '\d+\.\d+' | head -1)
    docker_major=$(echo "$docker_version" | cut -d. -f1)
    if [ "$docker_major" -lt 24 ]; then
        echo "❌ Docker version $docker_version detected. Version 24.0+ is required."
        exit 1
    fi
    echo "✅ Docker $docker_version detected"
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose is not installed."
        echo "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Verify Docker Compose version (2.20+)
    compose_version=$(docker compose version | grep -oP '\d+\.\d+\.\d+' | head -1)
    compose_major=$(echo "$compose_version" | cut -d. -f1)
    compose_minor=$(echo "$compose_version" | cut -d. -f2)
    if [ "$compose_major" -lt 2 ] || { [ "$compose_major" -eq 2 ] && [ "$compose_minor" -lt 20 ]; }; then
        echo "❌ Docker Compose version $compose_version detected. Version 2.20+ is required."
        exit 1
    fi
    echo "✅ Docker Compose $compose_version detected"
    
    # Check NVIDIA GPU
    if ! command -v nvidia-smi &> /dev/null; then
        echo "⚠️  Warning: nvidia-smi not found. GPU support may not work."
        read -p "Continue without GPU? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    fi
    
    # Check NVIDIA Container Toolkit
    if command -v nvidia-smi &> /dev/null; then
        echo "Verifying NVIDIA Container Toolkit..."
        if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            echo "❌ NVIDIA Container Toolkit is not properly configured."
            echo "Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
            exit 1
        fi
        echo "✅ NVIDIA Container Toolkit verified"
    fi
    
    echo "✅ Prerequisites check passed"
}

# Check system resources
check_resources() {
    echo "[2/7] Checking system resources..."
    
    # Check RAM
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram" -lt 16 ]; then
        echo "⚠️  Warning: Less than 16GB RAM detected (${total_ram}GB)"
        echo "Recommended: 16GB minimum for optimal performance"
    else
        echo "✅ RAM: ${total_ram}GB"
    fi
    
    # Check disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 50 ]; then
        echo "⚠️  Warning: Less than 50GB free disk space (${available_space}GB)"
        echo "Recommended: 50GB minimum for models and data"
    else
        echo "✅ Disk space: ${available_space}GB available"
    fi
}

# Create directory structure
create_directories() {
    echo "[3/7] Creating directory structure..."
    mkdir -p uploads results docker
    echo "✅ Directories created: uploads/, results/, docker/"
}

# Generate configuration
generate_config() {
    echo "[4/7] Generating configuration..."
    
    cat > config.yaml <<EOF
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
EOF
    
    echo "✅ Configuration generated: config.yaml"
}

# Pull/Build Docker images
build_images() {
    echo "[5/7] Building Docker images (this may take 10-15 minutes)..."
    echo "This will download base images and install dependencies..."
    
    if ! docker compose build; then
        echo "❌ Docker image build failed"
        echo "Check logs above for error details"
        exit 1
    fi
    
    echo "✅ Docker images built successfully"
}

# Start services
start_services() {
    echo "[6/7] Starting services..."
    
    if ! docker compose up -d; then
        echo "❌ Failed to start services"
        echo "Run 'docker compose logs' to see error details"
        exit 1
    fi
    
    echo "✅ Services started"
    
    # Wait for services to be healthy
    echo "Waiting for services to initialize..."
    sleep 10
    
    echo ""
    echo "Service status:"
    docker compose ps
    echo ""
}

# Run validation test
validate_installation() {
    echo "[7/7] Running validation test..."
    
    # Check if backend is responding
    max_retries=30
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s http://localhost/api/health > /dev/null 2>&1; then
            echo "✅ Backend is healthy"
            break
        fi
        
        retry_count=$((retry_count + 1))
        echo "Waiting for backend... ($retry_count/$max_retries)"
        sleep 2
    done
    
    if [ $retry_count -eq $max_retries ]; then
        echo "❌ Backend health check failed after $max_retries attempts"
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Check backend logs: docker compose logs backend"
        echo "2. Check worker logs: docker compose logs worker"
        echo "3. Check nginx logs: docker compose logs nginx"
        echo "4. Verify all services are running: docker compose ps"
        echo ""
        exit 1
    fi
    
    echo "✅ Validation completed successfully"
}

# Main installation flow
main() {
    check_prerequisites
    check_resources
    create_directories
    generate_config
    build_images
    start_services
    validate_installation
    
    echo ""
    echo "=========================================="
    echo "✅ UniRig UI Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Access the application at: http://localhost"
    echo ""
    echo "Useful commands:"
    echo "  Start:   docker compose up -d"
    echo "  Stop:    docker compose down"
    echo "  Logs:    docker compose logs -f [service]"
    echo "  Restart: docker compose restart [service]"
    echo ""
    echo "Services:"
    echo "  - Frontend: http://localhost"
    echo "  - Backend API: http://localhost/api"
    echo "  - Health Check: http://localhost/api/health"
    echo ""
}

main
