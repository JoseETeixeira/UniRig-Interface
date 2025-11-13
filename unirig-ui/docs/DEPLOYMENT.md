# Production Deployment Guide

This guide covers best practices for deploying the UniRig Web UI to production environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Infrastructure Requirements](#infrastructure-requirements)
- [Deployment Architecture](#deployment-architecture)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Configuration Management](#configuration-management)
- [SSL/TLS Setup](#ssltls-setup)
- [Load Balancing](#load-balancing)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)
- [Zero-Downtime Updates](#zero-downtime-updates)
- [Disaster Recovery](#disaster-recovery)

---

## Pre-Deployment Checklist

Before deploying to production:

- [ ] **Hardware Verified**: NVIDIA GPU with 8GB+ VRAM, 16GB+ RAM, 100GB+ disk
- [ ] **Network Configured**: Firewall rules, DNS records, SSL certificates
- [ ] **Backups Configured**: Automated backup schedule, tested restore procedure
- [ ] **Monitoring Setup**: Log aggregation, metrics collection, alerting
- [ ] **Security Hardened**: SSL enabled, firewall configured, security headers set
- [ ] **Documentation Updated**: All configuration and runbooks current
- [ ] **Testing Complete**: Load testing, security scanning, end-to-end tests passed
- [ ] **Rollback Plan**: Documented procedure to revert to previous version

---

## Infrastructure Requirements

### Minimum Production Specs

| Component | Requirement |
|-----------|-------------|
| **CPU** | 8 cores (16 threads recommended) |
| **RAM** | 32GB (64GB recommended for scaling) |
| **GPU** | NVIDIA RTX 3090 / A4000 or better |
| **VRAM** | 16GB minimum (24GB recommended) |
| **Storage** | 500GB SSD (NVMe preferred) |
| **Network** | 1Gbps connection, static IP |
| **OS** | Ubuntu 24.04 LTS Server |

### Recommended Production Specs (Multi-User)

| Component | Requirement |
|-----------|-------------|
| **CPU** | 16 cores (32 threads) |
| **RAM** | 128GB ECC memory |
| **GPU** | 2x NVIDIA A5000 or A6000 |
| **VRAM** | 48GB total (24GB per GPU) |
| **Storage** | 2TB NVMe SSD (RAID 1) |
| **Network** | 10Gbps connection |

---

## Deployment Architecture

### Single-Server Architecture

```
Internet
   |
   v
[Nginx Reverse Proxy] :443 (HTTPS)
   |
   +-- [FastAPI Backend] :8000
   |
   +-- [Celery Worker + GPU]
   |
   +-- [Redis] :6379
   |
   v
[Persistent Volumes]
   - uploads/
   - results/
   - models/
```

### Multi-Server Architecture (High Availability)

```
Internet
   |
   v
[Load Balancer] (HAProxy/AWS ALB)
   |
   +-- [Nginx 1] --> [Backend 1] --> [Redis Cluster]
   |                                      |
   +-- [Nginx 2] --> [Backend 2] --------+
                                          |
   +-- [Worker Node 1 + GPU 1] ----------+
   |
   +-- [Worker Node 2 + GPU 2] ----------+

[Shared Storage] (NFS/S3)
   - uploads/
   - results/
   - models/
```

---

## Step-by-Step Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    ufw \
    fail2ban \
    unattended-upgrades

# Configure automatic security updates
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 2. Install Docker & NVIDIA Container Toolkit

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 3. Clone Repository & Configure

```bash
# Create deployment directory
sudo mkdir -p /opt/unirig-ui
sudo chown $USER:$USER /opt/unirig-ui
cd /opt/unirig-ui

# Clone repository
git clone https://github.com/vastai-research/unirig-ui.git .
git checkout v1.0.0  # Use specific version tag

# Run installation script
chmod +x install.sh
./install.sh
```

### 4. Production Configuration

Create production configuration file:

```bash
nano /opt/unirig-ui/config.yaml
```

**Production `config.yaml`:**

```yaml
# Production Configuration
environment: production

# Server Configuration
server:
  host: 0.0.0.0
  port: 8000
  workers: 4  # CPU cores
  log_level: info
  max_upload_size: 100  # MB

# CORS Configuration (adjust for your domain)
cors:
  allowed_origins:
    - https://unirig.yourdomain.com
  allowed_methods:
    - GET
    - POST
    - DELETE
  allowed_headers:
    - "*"
  allow_credentials: true

# Security
security:
  session_secret: ${SESSION_SECRET}  # Load from environment
  csrf_enabled: true
  secure_cookies: true
  samesite: strict

# Rate Limiting
rate_limiting:
  upload_limit: 10
  upload_window: 3600
  api_limit: 1000
  api_window: 3600

# Worker Configuration
worker:
  concurrency: 1
  max_tasks_per_child: 10
  task_soft_time_limit: 1800  # 30 minutes
  task_hard_time_limit: 3600  # 1 hour

# Model Configuration
models:
  skeleton:
    checkpoint: /app/models/checkpoints/skeleton.ckpt
    config: /app/models/configs/skeleton.yaml
  skinning:
    checkpoint: /app/models/checkpoints/skinning.ckpt
    config: /app/models/configs/skinning.yaml

# Storage
storage:
  uploads_dir: /app/data/uploads
  results_dir: /app/data/results
  max_disk_usage_percent: 85
  cleanup_interval: 3600  # seconds
  retention_days: 7

# Redis
redis:
  host: redis
  port: 6379
  db: 0
  max_connections: 50

# Logging
logging:
  level: INFO
  format: json
  output: /var/log/unirig/app.log
  max_size: 100  # MB
  backup_count: 10
```

### 5. Environment Variables

Create `.env` file for sensitive data:

```bash
nano /opt/unirig-ui/.env
```

```bash
# .env - PRODUCTION SECRETS
# NEVER commit this file to version control

# Session secret (generate with: openssl rand -hex 32)
SESSION_SECRET=your_generated_secret_here

# Redis password (if using authentication)
REDIS_PASSWORD=your_redis_password

# Optional: External storage credentials
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=unirig-production

# Monitoring credentials
SENTRY_DSN=your_sentry_dsn

# Set permissions
chmod 600 /opt/unirig-ui/.env
```

### 6. Update Docker Compose for Production

Edit `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.backend
    restart: always
    environment:
      - ENV=production
      - SESSION_SECRET=${SESSION_SECRET}
    volumes:
      - ./uploads:/app/data/uploads
      - ./results:/app/data/results
      - ./models:/app/models:ro  # Read-only
      - ./config.yaml:/app/config.yaml:ro
      - /var/log/unirig:/var/log/unirig
    networks:
      - backend-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.worker
    restart: always
    environment:
      - ENV=production
    volumes:
      - ./uploads:/app/data/uploads
      - ./results:/app/data/results
      - ./models:/app/models:ro
      - ./config.yaml:/app/config.yaml:ro
      - /var/log/unirig:/var/log/unirig
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    networks:
      - backend-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
        limits:
          memory: 16G

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    build:
      context: .
      dockerfile: docker/Dockerfile.nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./results:/usr/share/nginx/html/results:ro
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro  # SSL certificates
      - /var/log/nginx:/var/log/nginx
    networks:
      - backend-network
    depends_on:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  backend-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
```

### 7. Build and Deploy

```bash
# Build containers
docker compose build --no-cache

# Start services
docker compose up -d

# Verify all services are running
docker compose ps

# Check logs
docker compose logs -f

# Verify health
curl http://localhost/api/health
```

---

## SSL/TLS Setup

### Option 1: Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker compose stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d unirig.yourdomain.com

# Certificates will be in: /etc/letsencrypt/live/unirig.yourdomain.com/

# Copy certificates to project
sudo mkdir -p /opt/unirig-ui/ssl
sudo cp /etc/letsencrypt/live/unirig.yourdomain.com/fullchain.pem /opt/unirig-ui/ssl/cert.pem
sudo cp /etc/letsencrypt/live/unirig.yourdomain.com/privkey.pem /opt/unirig-ui/ssl/key.pem
sudo chown $USER:$USER /opt/unirig-ui/ssl/*.pem

# Setup auto-renewal
sudo crontab -e
# Add: 0 0 * * * certbot renew --post-hook "docker compose -f /opt/unirig-ui/docker-compose.yml restart nginx"

# Restart nginx
docker compose up -d nginx
```

### Option 2: Self-Signed Certificate (Testing)

```bash
# Generate self-signed certificate
mkdir -p /opt/unirig-ui/ssl
cd /opt/unirig-ui/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=unirig.yourdomain.com"

chmod 600 key.pem
```

### Nginx SSL Configuration

Update `docker/nginx.conf`:

```nginx
upstream backend {
    least_conn;
    server backend:8000;
}

server {
    listen 80;
    server_name unirig.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name unirig.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' wss:;" always;

    client_max_body_size 100M;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /ws {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }
    
    location /results {
        alias /usr/share/nginx/html/results;
        autoindex off;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Load Balancing

### Using HAProxy

Install HAProxy on a separate server:

```bash
sudo apt install -y haproxy
```

Configure `/etc/haproxy/haproxy.cfg`:

```
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/unirig.pem
    
    redirect scheme https code 301 if !{ ssl_fc }
    
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /api/health
    
    server node1 192.168.1.10:443 check ssl verify none
    server node2 192.168.1.11:443 check ssl verify none
    
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats auth admin:your_password_here
```

---

## Scaling

### Horizontal Scaling (Multiple Workers)

To add more GPU workers:

1. **Provision additional GPU servers**
2. **Install Docker + NVIDIA Container Toolkit**
3. **Deploy worker-only configuration:**

```yaml
# docker-compose.worker.yml
version: '3.8'

services:
  worker:
    build:
      context: ./backend
      dockerfile: ../docker/Dockerfile.worker
    restart: always
    environment:
      - ENV=production
      - REDIS_HOST=redis.central.local  # Central Redis
    volumes:
      - nfs-uploads:/app/data/uploads
      - nfs-results:/app/data/results
      - ./models:/app/models:ro
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  nfs-uploads:
    driver: local
    driver_opts:
      type: nfs
      o: addr=storage.local,rw
      device: ":/mnt/unirig/uploads"
  
  nfs-results:
    driver: local
    driver_opts:
      type: nfs
      o: addr=storage.local,rw
      device: ":/mnt/unirig/results"
```

### Vertical Scaling (More Resources)

Update `docker-compose.yml` resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 16G
  
  worker:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 32G
        reservations:
          devices:
            - driver: nvidia
              count: 2  # Use 2 GPUs
              capabilities: [gpu]
```

---

## Backup and Recovery

### Automated Backup Script

Create `/opt/unirig-ui/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/mnt/backups/unirig"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Backup volumes
echo "Backing up uploads..."
tar czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /opt/unirig-ui uploads/

echo "Backing up results..."
tar czf $BACKUP_DIR/results_$DATE.tar.gz -C /opt/unirig-ui results/

echo "Backing up models..."
tar czf $BACKUP_DIR/models_$DATE.tar.gz -C /opt/unirig-ui models/

# Backup configuration
echo "Backing up config..."
cp /opt/unirig-ui/config.yaml $BACKUP_DIR/config_$DATE.yaml
cp /opt/unirig-ui/docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.yml

# Backup Redis data
echo "Backing up Redis..."
docker compose exec -T redis redis-cli BGSAVE
sleep 5
docker cp unirig-redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backup complete: $BACKUP_DIR"
```

Schedule with cron:

```bash
chmod +x /opt/unirig-ui/backup.sh
sudo crontab -e
# Add: 0 2 * * * /opt/unirig-ui/backup.sh >> /var/log/unirig-backup.log 2>&1
```

### Restore Procedure

```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1  # Format: YYYYMMDD_HHMMSS
BACKUP_DIR="/mnt/backups/unirig"

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: ./restore.sh YYYYMMDD_HHMMSS"
    exit 1
fi

echo "Stopping services..."
docker compose down

echo "Restoring uploads..."
rm -rf /opt/unirig-ui/uploads/*
tar xzf $BACKUP_DIR/uploads_$BACKUP_DATE.tar.gz -C /opt/unirig-ui

echo "Restoring results..."
rm -rf /opt/unirig-ui/results/*
tar xzf $BACKUP_DIR/results_$BACKUP_DATE.tar.gz -C /opt/unirig-ui

echo "Restoring models..."
rm -rf /opt/unirig-ui/models/*
tar xzf $BACKUP_DIR/models_$BACKUP_DATE.tar.gz -C /opt/unirig-ui

echo "Restoring configuration..."
cp $BACKUP_DIR/config_$BACKUP_DATE.yaml /opt/unirig-ui/config.yaml
cp $BACKUP_DIR/docker-compose_$BACKUP_DATE.yml /opt/unirig-ui/docker-compose.yml

echo "Restoring Redis..."
docker compose up -d redis
sleep 5
docker cp $BACKUP_DIR/redis_$BACKUP_DATE.rdb unirig-redis:/data/dump.rdb
docker compose restart redis

echo "Starting all services..."
docker compose up -d

echo "Restore complete!"
```

---

## Zero-Downtime Updates

### Blue-Green Deployment

1. **Setup secondary stack:**

```bash
# Copy production to staging
cp -r /opt/unirig-ui /opt/unirig-ui-staging
cd /opt/unirig-ui-staging

# Update code
git pull origin main

# Build new containers
docker compose build --no-cache

# Start on different ports
sed -i 's/80:80/8080:80/g' docker-compose.yml
sed -i 's/443:443/8443:443/g' docker-compose.yml
docker compose up -d
```

2. **Test staging:**

```bash
curl https://localhost:8443/api/health
# Run integration tests
```

3. **Switch traffic (HAProxy):**

```
# /etc/haproxy/haproxy.cfg
backend http_back
    balance roundrobin
    
    # Drain old
    server prod 192.168.1.10:443 check backup
    
    # Activate new
    server staging 192.168.1.10:8443 check
```

4. **Verify and cleanup:**

```bash
# Monitor for issues
tail -f /var/log/haproxy.log

# If successful, stop old stack
cd /opt/unirig-ui
docker compose down

# Cleanup
rm -rf /opt/unirig-ui-staging
```

---

## Disaster Recovery

### Recovery Time Objective (RTO): 4 hours
### Recovery Point Objective (RPO): 24 hours

**Disaster Recovery Steps:**

1. **Provision new infrastructure** (1 hour)
2. **Restore from backup** (1 hour)
3. **Verify functionality** (1 hour)
4. **Switch DNS/traffic** (1 hour)

**Disaster Recovery Checklist:**

- [ ] Maintain off-site backups (S3, GCS)
- [ ] Document all infrastructure as code
- [ ] Keep copy of SSL certificates secure
- [ ] Test restore procedure monthly
- [ ] Maintain list of dependencies and versions
- [ ] Document external integrations

---

## Monitoring Integration

See [MONITORING.md](MONITORING.md) for detailed monitoring setup.

Quick health checks:

```bash
# Service health
docker compose ps

# Resource usage
docker stats

# Application health
curl https://unirig.yourdomain.com/api/health

# GPU status
docker exec unirig-worker nvidia-smi

# Disk usage
df -h /opt/unirig-ui
```

---

## Troubleshooting Production Issues

See [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) for detailed troubleshooting.

**Common Production Issues:**

1. **High memory usage:** Scale worker resources or limit concurrent jobs
2. **Slow processing:** Check GPU utilization, add more workers
3. **Disk full:** Enable automatic cleanup, increase retention
4. **SSL certificate expired:** Renew with certbot
5. **Database connection errors:** Check Redis health, increase max connections

---

## Maintenance Windows

Recommended maintenance schedule:

- **Weekly:** Security updates, log rotation
- **Monthly:** Backup verification, dependency updates
- **Quarterly:** Performance tuning, capacity planning
- **Annually:** Disaster recovery test, security audit

---

**Last Updated**: November 13, 2025  
**Maintained By**: DevOps Team
