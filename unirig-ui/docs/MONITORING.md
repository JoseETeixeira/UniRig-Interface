# Monitoring and Logging Guide

This guide covers setting up comprehensive monitoring, logging, and alerting for the UniRig Web UI in production.

## Table of Contents

- [Overview](#overview)
- [Logging Setup](#logging-setup)
- [Metrics Collection](#metrics-collection)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Log Aggregation](#log-aggregation)
- [Performance Monitoring](#performance-monitoring)
- [Troubleshooting with Logs](#troubleshooting-with-logs)

---

## Overview

### Monitoring Stack

We recommend the following open-source stack:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Loki**: Log aggregation
- **Promtail**: Log shipping
- **AlertManager**: Alert routing and notifications
- **Node Exporter**: System metrics
- **cAdvisor**: Container metrics
- **NVIDIA DCGM Exporter**: GPU metrics

### Architecture

```
[Application Logs] --> [Promtail] --> [Loki] --> [Grafana]
[Prometheus] --> [Application Metrics]
            --> [Node Exporter]
            --> [cAdvisor]
            --> [DCGM Exporter (GPU)]
            --> [AlertManager] --> [Notifications]
```

---

## Logging Setup

### 1. Application Logging Configuration

Update `backend/app/core/logging.py`:

```python
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO", log_file: str = "/var/log/unirig/app.log"):
    """Configure application logging."""
    
    # Create log directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (JSON format)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Separate error log
    error_handler = logging.FileHandler("/var/log/unirig/error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    return logger
```

### 2. Request Logging Middleware

Add structured request logging:

```python
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request info
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        session_id = request.cookies.get("session_id", "anonymous")
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )
        
        return response

# Add to FastAPI app
app.add_middleware(RequestLoggingMiddleware)
```

### 3. Job Event Logging

Log important job events:

```python
def log_job_event(job: Job, event: str, **kwargs):
    """Log job lifecycle events."""
    logger.info(
        f"Job {event}",
        extra={
            "job_id": job.id,
            "session_id": job.session_id,
            "job_type": job.job_type,
            "status": job.status,
            "event": event,
            **kwargs
        }
    )

# Usage
log_job_event(job, "created", file_size=file.size)
log_job_event(job, "started", worker_id=worker.id)
log_job_event(job, "completed", duration=duration, output_size=output.size)
log_job_event(job, "failed", error=str(exc))
```

### 4. Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# /etc/logrotate.d/unirig
/var/log/unirig/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker compose -f /opt/unirig-ui/docker-compose.yml exec backend kill -USR1 1 2>/dev/null || true
    endscript
}
```

---

## Metrics Collection

### 1. Prometheus Setup

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'unirig-production'

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules
rule_files:
  - '/etc/prometheus/rules/*.yml'

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Application metrics
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # Node metrics (system)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # GPU metrics
  - job_name: 'gpu'
    static_configs:
      - targets: ['dcgm-exporter:9400']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 2. Application Metrics

Add Prometheus metrics to FastAPI:

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

upload_size = Histogram(
    'upload_file_size_bytes',
    'File upload size',
    buckets=[1e6, 10e6, 50e6, 100e6, 500e6]  # 1MB to 500MB
)

job_duration = Histogram(
    'job_processing_duration_seconds',
    'Job processing duration',
    ['job_type'],
    buckets=[10, 30, 60, 120, 300, 600, 1800]  # 10s to 30min
)

active_jobs = Gauge(
    'active_jobs',
    'Number of active jobs',
    ['job_type']
)

job_queue_length = Gauge(
    'job_queue_length',
    'Number of jobs in queue'
)

gpu_memory_usage = Gauge(
    'gpu_memory_usage_bytes',
    'GPU memory usage',
    ['gpu_id']
)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Usage in endpoints
@app.post("/api/upload")
async def upload_file(file: UploadFile):
    start_time = time.time()
    
    try:
        # Track upload size
        upload_size.observe(file.size)
        
        # Process upload
        result = await process_upload(file)
        
        # Track success
        request_count.labels(method="POST", endpoint="/upload", status="200").inc()
        
        return result
    
    except Exception as exc:
        # Track failure
        request_count.labels(method="POST", endpoint="/upload", status="500").inc()
        raise
    
    finally:
        # Track duration
        duration = time.time() - start_time
        request_duration.labels(method="POST", endpoint="/upload").observe(duration)

# Job metrics
def track_job_start(job: Job):
    active_jobs.labels(job_type=job.job_type).inc()
    job_queue_length.dec()

def track_job_complete(job: Job, duration: float):
    active_jobs.labels(job_type=job.job_type).dec()
    job_duration.labels(job_type=job.job_type).observe(duration)

# GPU metrics (update periodically)
async def update_gpu_metrics():
    while True:
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                text=True
            )
            for line in output.strip().split("\n"):
                gpu_id, memory_mb = line.split(", ")
                gpu_memory_usage.labels(gpu_id=gpu_id).set(float(memory_mb) * 1e6)
        except Exception as e:
            logger.error(f"Failed to update GPU metrics: {e}")
        
        await asyncio.sleep(15)

# Start GPU metrics collection
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_gpu_metrics())
```

### 3. Docker Compose Monitoring Stack

Add to `docker-compose.yml`:

```yaml
services:
  # ... existing services ...

  prometheus:
    image: prom/prometheus:latest
    restart: always
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/rules:/etc/prometheus/rules:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
    networks:
      - monitoring-network

  grafana:
    image: grafana/grafana:latest
    restart: always
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3000:3000"
    networks:
      - monitoring-network

  loki:
    image: grafana/loki:latest
    restart: always
    volumes:
      - ./monitoring/loki.yml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    ports:
      - "3100:3100"
    networks:
      - monitoring-network

  promtail:
    image: grafana/promtail:latest
    restart: always
    volumes:
      - ./monitoring/promtail.yml:/etc/promtail/config.yml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring-network

  node-exporter:
    image: prom/node-exporter:latest
    restart: always
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring-network

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    restart: always
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    privileged: true
    networks:
      - monitoring-network

  dcgm-exporter:
    image: nvcr.io/nvidia/k8s/dcgm-exporter:latest
    restart: always
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    cap_add:
      - SYS_ADMIN
    networks:
      - monitoring-network

  redis-exporter:
    image: oliver006/redis_exporter:latest
    restart: always
    environment:
      - REDIS_ADDR=redis:6379
    networks:
      - monitoring-network

networks:
  monitoring-network:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
  loki-data:
```

### 4. Grafana Datasource Configuration

Create `monitoring/grafana/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

---

## Alerting

### 1. Alert Rules

Create `monitoring/rules/alerts.yml`:

```yaml
groups:
  - name: unirig_alerts
    interval: 30s
    rules:
      # Service availability
      - alert: ServiceDown
        expr: up{job=~"backend|worker"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} has been down for more than 1 minute"

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes"

      # Slow requests
      - alert: SlowRequests
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile request duration is high"
          description: "95th percentile latency is {{ $value }}s"

      # Queue backup
      - alert: JobQueueBackup
        expr: job_queue_length > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Job queue is backing up"
          description: "{{ $value }} jobs in queue"

      # Disk space
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/app/data"} / node_filesystem_size_bytes{mountpoint="/app/data"}) < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on data volume"
          description: "Only {{ $value | humanizePercentage }} space remaining"

      - alert: DiskSpaceCritical
        expr: (node_filesystem_avail_bytes{mountpoint="/app/data"} / node_filesystem_size_bytes{mountpoint="/app/data"}) < 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical disk space on data volume"
          description: "Only {{ $value | humanizePercentage }} space remaining"

      # Memory
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # GPU
      - alert: GPUMemoryHigh
        expr: DCGM_FI_DEV_FB_USED / DCGM_FI_DEV_FB_FREE > 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU memory usage high"
          description: "GPU {{ $labels.gpu }} memory usage is {{ $value | humanizePercentage }}"

      - alert: GPUTemperatureHigh
        expr: DCGM_FI_DEV_GPU_TEMP > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU temperature high"
          description: "GPU {{ $labels.gpu }} temperature is {{ $value }}°C"

      # Job failures
      - alert: HighJobFailureRate
        expr: rate(job_failures_total[10m]) / rate(job_completions_total[10m]) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High job failure rate"
          description: "{{ $value | humanizePercentage }} of jobs are failing"
```

### 2. AlertManager Configuration

Create `monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://webhook-receiver:8080/alert'

  - name: 'critical'
    email_configs:
      - to: 'ops-team@yourdomain.com'
        from: 'alertmanager@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@yourdomain.com'
        auth_password: '${SMTP_PASSWORD}'
        headers:
          Subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
    
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts-critical'
        title: '🚨 {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'warning'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts-warning'
        title: '⚠️ {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster']
```

Add AlertManager to `docker-compose.yml`:

```yaml
  alertmanager:
    image: prom/alertmanager:latest
    restart: always
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/config.yml:ro
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring-network
```

---

## Dashboards

### 1. System Overview Dashboard

Create `monitoring/grafana/dashboards/system-overview.json`:

```json
{
  "dashboard": {
    "title": "UniRig System Overview",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Jobs",
        "targets": [
          {
            "expr": "active_jobs",
            "legendFormat": "{{job_type}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "GPU Memory Usage",
        "targets": [
          {
            "expr": "gpu_memory_usage_bytes / 1e9",
            "legendFormat": "GPU {{gpu_id}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### 2. Job Processing Dashboard

Key metrics to display:
- Job queue length over time
- Job processing duration by type
- Job success/failure rate
- GPU utilization during jobs
- Memory usage during jobs

### 3. Infrastructure Dashboard

Key metrics:
- CPU usage per container
- Memory usage per container
- Network I/O
- Disk I/O
- Container restarts

---

## Log Aggregation

### 1. Promtail Configuration

Create `monitoring/promtail.yml`:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Application logs
  - job_name: application
    static_configs:
      - targets:
          - localhost
        labels:
          job: unirig-app
          __path__: /var/log/unirig/*.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            session_id: session_id
            job_id: job_id
      - labels:
          level:
          session_id:
          job_id:
      - timestamp:
          source: timestamp
          format: RFC3339

  # Docker container logs
  - job_name: docker
    static_configs:
      - targets:
          - localhost
        labels:
          job: docker-logs
          __path__: /var/lib/docker/containers/*/*.log
    pipeline_stages:
      - json:
          expressions:
            stream: stream
            log: log
      - labels:
          stream:
```

### 2. Loki Configuration

Create `monitoring/loki.yml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-05-15
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  retention_period: 30d

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 30d
```

---

## Performance Monitoring

### Key Metrics to Track

1. **Request Metrics:**
   - Requests per second
   - Response time (p50, p95, p99)
   - Error rate

2. **Job Metrics:**
   - Queue length
   - Processing time by job type
   - Success/failure rate
   - Throughput (jobs/hour)

3. **System Metrics:**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

4. **GPU Metrics:**
   - GPU utilization
   - GPU memory usage
   - GPU temperature
   - CUDA errors

### Query Examples

```promql
# Average request duration
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Request rate by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Job processing rate
rate(job_completions_total[10m])

# GPU memory utilization percentage
(gpu_memory_usage_bytes / 24e9) * 100

# Error rate percentage
(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100
```

---

## Troubleshooting with Logs

### Common Log Queries

**Find all errors in the last hour:**
```logql
{job="unirig-app"} |= "ERROR" | json
```

**Find failed jobs:**
```logql
{job="unirig-app"} | json | job_id != "" | status = "failed"
```

**Find slow requests (>5s):**
```logql
{job="unirig-app"} | json | duration_ms > 5000
```

**Find requests from specific session:**
```logql
{job="unirig-app"} | json | session_id = "abc123"
```

**Count errors by type:**
```logql
sum by (error_type) (count_over_time({job="unirig-app"} | json | level="ERROR" [1h]))
```

### Debugging Workflow

1. **Check service health:**
   ```bash
   curl http://localhost:9090/-/healthy  # Prometheus
   curl http://localhost:3000/api/health  # Grafana
   curl http://localhost:3100/ready      # Loki
   ```

2. **View recent logs:**
   ```bash
   docker compose logs --tail=100 -f backend
   ```

3. **Query specific timeframe:**
   ```logql
   {job="unirig-app"} 
   | json 
   | timestamp >= "2025-01-13T10:00:00Z" 
   | timestamp <= "2025-01-13T11:00:00Z"
   ```

4. **Correlate logs with metrics:**
   - Find spike in error rate → Query logs for that time
   - Find slow request → Look for corresponding job_id logs
   - Find high GPU usage → Check concurrent jobs

---

## Access Monitoring Tools

After deploying the monitoring stack:

- **Grafana**: http://localhost:3000 (admin / your_password)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

---

## Best Practices

1. **Set up alerts early**: Don't wait for production issues
2. **Use structured logging**: JSON format for easy parsing
3. **Include context**: Add session_id, job_id, user_id to logs
4. **Monitor trends**: Look for gradual degradation, not just incidents
5. **Set up log retention**: Balance storage cost vs. debugging needs
6. **Test alerts**: Regularly verify alerting works
7. **Document runbooks**: Link alerts to troubleshooting steps
8. **Review dashboards**: Regular review sessions with team

---

**Last Updated**: November 13, 2025  
**Maintained By**: DevOps Team
