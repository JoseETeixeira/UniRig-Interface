# API Reference

Complete API documentation for UniRig Web UI backend.

**Base URL**: `http://localhost/api`

**API Version**: 1.0

## Authentication

Session-based authentication using HTTPOnly cookies. CSRF protection is enabled for all state-changing operations (POST, PUT, DELETE).

### Get CSRF Token

```http
GET /api/csrf-token
```

**Response:**
```json
{
  "csrf_token": "a1b2c3d4e5f6..."
}
```

**Usage:**
Include the token in the `X-CSRF-Token` header for POST/PUT/DELETE requests.

---

## Health Check

### Check API Health

```http
GET /api/health
```

**Response 200 OK:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T10:30:00Z",
  "version": "1.0.0"
}
```

---

## File Upload

### Upload 3D Model

```http
POST /api/upload
Content-Type: multipart/form-data
X-CSRF-Token: {csrf_token}
```

**Parameters:**
- `file` (required): 3D model file (OBJ, FBX, GLB, VRM)

**Request Example:**
```bash
curl -X POST http://localhost/api/upload \
  -H "X-CSRF-Token: a1b2c3d4" \
  -F "file=@model.obj" \
  --cookie "session_id=session123"
```

**Response 200 OK:**
```json
{
  "filename": "model.obj",
  "path": "/uploads/session123/model.obj",
  "size": 1048576,
  "mime_type": "model/obj",
  "uploaded_at": "2025-11-13T10:30:00Z"
}
```

**Error Responses:**

**400 Bad Request** - Invalid file format
```json
{
  "detail": "Invalid file format. Supported: .obj, .fbx, .glb, .vrm"
}
```

**413 Request Entity Too Large** - File exceeds size limit
```json
{
  "detail": "File size exceeds maximum allowed size of 100MB"
}
```

**429 Too Many Requests** - Rate limit exceeded
```json
{
  "detail": "Rate limit exceeded. Maximum 10 uploads per hour."
}
```

---

## Job Management

### Create Skeleton Generation Job

```http
POST /api/jobs/skeleton
Content-Type: application/json
X-CSRF-Token: {csrf_token}
```

**Request Body:**
```json
{
  "input_file": "/uploads/session123/model.obj"
}
```

**Response 200 OK:**
```json
{
  "job_id": "job-uuid-1234",
  "status": "pending",
  "type": "skeleton",
  "input_file": "/uploads/session123/model.obj",
  "created_at": "2025-11-13T10:30:00Z",
  "progress": 0
}
```

**Error Responses:**

**409 Conflict** - Active job already exists
```json
{
  "detail": "Cannot create new job: Active job already exists for this session"
}
```

### Create Skinning Generation Job

```http
POST /api/jobs/skinning
Content-Type: application/json
X-CSRF-Token: {csrf_token}
```

**Request Body:**
```json
{
  "input_file": "/uploads/session123/model_skeleton.obj"
}
```

**Response**: Same structure as skeleton job with `"type": "skinning"`

### Create Merge Job

```http
POST /api/jobs/merge
Content-Type: application/json
X-CSRF-Token: {csrf_token}
```

**Request Body:**
```json
{
  "skeleton_file": "/results/session123/skeleton.fbx",
  "skinning_file": "/results/session123/skinning.fbx",
  "output_format": "fbx"
}
```

**Response**: Same structure with `"type": "merge"`

### Get Job Status

```http
GET /api/jobs/{job_id}
```

**Response 200 OK:**
```json
{
  "job_id": "job-uuid-1234",
  "status": "running",
  "type": "skeleton",
  "input_file": "/uploads/session123/model.obj",
  "output_file": null,
  "progress": 45,
  "error": null,
  "created_at": "2025-11-13T10:30:00Z",
  "started_at": "2025-11-13T10:30:15Z",
  "completed_at": null
}
```

**Job Status Values:**
- `pending`: Waiting in queue
- `running`: Currently processing
- `completed`: Successfully finished
- `failed`: Processing error occurred
- `cancelled`: Cancelled by user

### List Session Jobs

```http
GET /api/jobs
```

**Query Parameters:**
- `status` (optional): Filter by status (pending, running, completed, failed)
- `limit` (optional): Max jobs to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response 200 OK:**
```json
{
  "jobs": [
    {
      "job_id": "job-uuid-1234",
      "status": "completed",
      "type": "skeleton",
      "progress": 100,
      "created_at": "2025-11-13T10:30:00Z",
      "completed_at": "2025-11-13T10:33:00Z"
    },
    {
      "job_id": "job-uuid-5678",
      "status": "running",
      "type": "skinning",
      "progress": 65,
      "created_at": "2025-11-13T10:35:00Z",
      "completed_at": null
    }
  ],
  "total": 2,
  "limit": 50,
  "offset": 0
}
```

### Cancel Job

```http
POST /api/jobs/{job_id}/cancel
X-CSRF-Token: {csrf_token}
```

**Response 200 OK:**
```json
{
  "job_id": "job-uuid-1234",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Error 400 Bad Request** - Job cannot be cancelled
```json
{
  "detail": "Cannot cancel job: Job already completed"
}
```

### Delete Job

```http
DELETE /api/jobs/{job_id}
X-CSRF-Token: {csrf_token}
```

**Response 200 OK:**
```json
{
  "message": "Job deleted successfully"
}
```

---

## Session Management

### Get Session Statistics

```http
GET /api/sessions/{session_id}/stats
```

**Response 200 OK:**
```json
{
  "session_id": "session123",
  "total_jobs": 5,
  "completed_jobs": 3,
  "failed_jobs": 1,
  "pending_jobs": 1,
  "total_uploads": 10,
  "storage_used_mb": 250.5,
  "created_at": "2025-11-13T08:00:00Z",
  "last_activity": "2025-11-13T10:30:00Z"
}
```

### Delete Session

```http
DELETE /api/sessions/{session_id}
X-CSRF-Token: {csrf_token}
```

**Response 200 OK:**
```json
{
  "message": "Session deleted successfully",
  "files_deleted": 15,
  "storage_freed_mb": 250.5
}
```

### Get Disk Space

```http
GET /api/disk-space
```

**Response 200 OK:**
```json
{
  "total": 107374182400,
  "used": 53687091200,
  "free": 53687091200,
  "percent_used": 50.0,
  "status": "ok",
  "warning_threshold_gb": 10,
  "critical_threshold_gb": 5
}
```

**Status Values:**
- `ok`: Sufficient disk space (>10GB free)
- `warning`: Low disk space (5-10GB free)
- `critical`: Very low disk space (<5GB free)

---

## File Download

### Download Result File

```http
GET /results/{session_id}/{filename}
```

**Response 200 OK:**
- Content-Type: `application/octet-stream`
- Content-Disposition: `attachment; filename="{filename}"`
- Body: Binary file data

**Example:**
```bash
curl -O http://localhost/results/session123/model_rigged.fbx
```

---

## WebSocket Events

Real-time job progress updates via WebSocket.

**Endpoint:** `ws://localhost/ws?session={session_id}`

### Connection

```javascript
const ws = new WebSocket('ws://localhost/ws?session=session123');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Job update:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

### Event Types

**Job Progress Update:**
```json
{
  "type": "job_progress",
  "job_id": "job-uuid-1234",
  "progress": 45,
  "status": "running",
  "message": "Processing skeleton..."
}
```

**Job Completed:**
```json
{
  "type": "job_completed",
  "job_id": "job-uuid-1234",
  "status": "completed",
  "output_file": "/results/session123/model_skeleton.obj"
}
```

**Job Failed:**
```json
{
  "type": "job_failed",
  "job_id": "job-uuid-1234",
  "status": "failed",
  "error": "GPU out of memory"
}
```

---

## Rate Limiting

Rate limits are applied per session:

- **File Uploads**: 10 per hour
- **Job Creation**: No explicit limit (enforced by concurrent job limit)
- **API Requests**: 1000 per hour

**Rate Limit Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699876800
```

**429 Response:**
```json
{
  "detail": "Rate limit exceeded. Try again in 45 minutes.",
  "retry_after": 2700
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "detail": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-11-13T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | CSRF token invalid or missing |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., concurrent job limit) |
| 413 | Payload Too Large | File exceeds size limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FILE_FORMAT` | Unsupported file type |
| `FILE_TOO_LARGE` | File exceeds 100MB limit |
| `CSRF_TOKEN_MISSING` | CSRF token not provided |
| `CSRF_TOKEN_INVALID` | CSRF token verification failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `JOB_NOT_FOUND` | Job ID doesn't exist |
| `SESSION_NOT_FOUND` | Session ID doesn't exist |
| `CONCURRENT_JOB_LIMIT` | Active job already exists |
| `GPU_OUT_OF_MEMORY` | Insufficient GPU memory |
| `MODEL_CHECKPOINT_MISSING` | UniRig model not downloaded |
| `PROCESSING_FAILED` | UniRig processing error |

---

## Request/Response Examples

### Complete Workflow Example

**1. Get CSRF Token**
```bash
curl http://localhost/api/csrf-token
# Response: {"csrf_token": "abc123"}
```

**2. Upload Model**
```bash
curl -X POST http://localhost/api/upload \
  -H "X-CSRF-Token: abc123" \
  -F "file=@character.obj" \
  --cookie-jar cookies.txt

# Response: {"filename": "character.obj", "path": "/uploads/session456/character.obj"}
```

**3. Create Skeleton Job**
```bash
curl -X POST http://localhost/api/jobs/skeleton \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: abc123" \
  -d '{"input_file": "/uploads/session456/character.obj"}' \
  --cookie cookies.txt

# Response: {"job_id": "job-789", "status": "pending"}
```

**4. Poll Job Status**
```bash
curl http://localhost/api/jobs/job-789 \
  --cookie cookies.txt

# Response: {"job_id": "job-789", "status": "running", "progress": 65}
```

**5. Download Result**
```bash
curl -O http://localhost/results/session456/character_skeleton.obj
```

### Python Client Example

```python
import requests
from pathlib import Path

class UniRigClient:
    def __init__(self, base_url="http://localhost/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.csrf_token = self._get_csrf_token()
    
    def _get_csrf_token(self):
        response = self.session.get(f"{self.base_url}/csrf-token")
        return response.json()["csrf_token"]
    
    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f)}
            headers = {'X-CSRF-Token': self.csrf_token}
            response = self.session.post(
                f"{self.base_url}/upload",
                files=files,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    
    def create_skeleton_job(self, input_file):
        headers = {'X-CSRF-Token': self.csrf_token}
        data = {'input_file': input_file}
        response = self.session.post(
            f"{self.base_url}/jobs/skeleton",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id):
        response = self.session.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(self, job_id, poll_interval=5):
        import time
        while True:
            job = self.get_job_status(job_id)
            if job['status'] in ['completed', 'failed', 'cancelled']:
                return job
            print(f"Progress: {job['progress']}%")
            time.sleep(poll_interval)

# Usage
client = UniRigClient()

# Upload and process
upload_result = client.upload_file('character.obj')
job = client.create_skeleton_job(upload_result['path'])
final_job = client.wait_for_job(job['job_id'])

if final_job['status'] == 'completed':
    print(f"Success! Output: {final_job['output_file']}")
else:
    print(f"Failed: {final_job['error']}")
```

### JavaScript/TypeScript Client Example

```typescript
class UniRigClient {
  private baseUrl: string;
  private csrfToken: string | null = null;

  constructor(baseUrl: string = 'http://localhost/api') {
    this.baseUrl = baseUrl;
  }

  async init(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/csrf-token`, {
      credentials: 'include'
    });
    const data = await response.json();
    this.csrfToken = data.csrf_token;
  }

  async uploadFile(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      headers: {
        'X-CSRF-Token': this.csrfToken!
      },
      body: formData,
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  async createSkeletonJob(inputFile: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/jobs/skeleton`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': this.csrfToken!
      },
      body: JSON.stringify({ input_file: inputFile }),
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Job creation failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getJobStatus(jobId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error(`Failed to get job status: ${response.statusText}`);
    }

    return response.json();
  }

  async waitForJob(
    jobId: string,
    onProgress?: (progress: number) => void,
    pollInterval: number = 5000
  ): Promise<any> {
    while (true) {
      const job = await this.getJobStatus(jobId);
      
      if (onProgress) {
        onProgress(job.progress);
      }

      if (['completed', 'failed', 'cancelled'].includes(job.status)) {
        return job;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }
}

// Usage
const client = new UniRigClient();
await client.init();

const fileInput = document.querySelector<HTMLInputElement>('#file-input');
const file = fileInput.files[0];

const uploadResult = await client.uploadFile(file);
const job = await client.createSkeletonJob(uploadResult.path);

const finalJob = await client.waitForJob(job.job_id, (progress) => {
  console.log(`Progress: ${progress}%`);
});

if (finalJob.status === 'completed') {
  console.log(`Success! Download from: ${finalJob.output_file}`);
}
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost/api/docs
- **ReDoc**: http://localhost/api/redoc

These provide:
- Complete endpoint specifications
- Request/response schemas
- Interactive API testing
- Auto-generated from FastAPI code

---

**API Version**: 1.0  
**Last Updated**: November 13, 2025
