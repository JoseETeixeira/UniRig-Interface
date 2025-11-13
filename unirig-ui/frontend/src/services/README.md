# API Services & Custom Hooks

This directory contains the frontend data layer that interfaces with the backend API.

## API Service (`api.ts`)

Axios-based HTTP client with automatic request/response handling.

### Configuration
- **Base URL**: `/api` (proxied to backend via Vite)
- **Content-Type**: `application/json` by default
- **Error Handling**: Automatic interceptors for structured error responses

### Available Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `uploadFile(file, sessionId?, onProgress?)` | `POST /upload` | Upload 3D model with progress tracking |
| `getJob(jobId)` | `GET /jobs/:jobId` | Fetch job status and results |
| `listJobs(sessionId)` | `GET /sessions/:sessionId/jobs` | List all jobs for a session |
| `triggerSkeleton(jobId, seed?)` | `POST /jobs/:jobId/skeleton` | Start skeleton generation |
| `triggerSkinning(jobId)` | `POST /jobs/:jobId/skinning` | Start skinning generation |
| `deleteJob(jobId)` | `DELETE /jobs/:jobId` | Delete a job and its files |
| `downloadFile(jobId, type)` | `GET /download/:jobId?type=...` | Download result files |
| `checkHealth()` | `GET /health` | Check API health status |

### Error Handling

All API methods return structured errors with:
```typescript
{
  code: string;        // Error code (e.g., "INVALID_FILE_FORMAT")
  message: string;     // Human-readable message
  details?: string;    // Additional details
  suggestion?: string; // Suggested action
}
```

## Custom Hooks

### `useUpload()`

Manages file upload state with progress tracking.

**Returns:**
- `upload(file)` - Upload function
- `uploading` - Boolean upload state
- `progress` - Upload progress (0-100)
- `error` - Error message if upload fails

**Usage:**
```typescript
const { upload, uploading, progress, error } = useUpload();

const handleUpload = async (file: File) => {
  const response = await upload(file);
  if (response) {
    console.log('Upload successful:', response.job_id);
  }
};
```

### `useJob(jobId)`

Manages job state with automatic polling.

**Features:**
- Automatic polling every 2 seconds when job is `processing` or `queued`
- Stops polling when job is `completed` or `failed`
- Provides methods to trigger skeleton and skinning generation

**Returns:**
- `job` - Current job data
- `loading` - Loading state
- `error` - Error message
- `refresh()` - Manual refresh function
- `generateSkeleton(seed?)` - Trigger skeleton generation
- `generateSkinning()` - Trigger skinning generation

**Usage:**
```typescript
const { job, generateSkeleton, generateSkinning } = useJob(jobId);

useEffect(() => {
  if (job?.status === 'completed') {
    console.log('Job completed!', job.results);
  }
}, [job]);
```

### `useSession()`

Manages user session with localStorage persistence.

**Features:**
- Automatically creates session ID on first use
- Persists session ID across page refreshes
- Provides methods to create new session or clear current one

**Returns:**
- `sessionId` - Current session ID (or null if not initialized)
- `createSession()` - Create new session ID
- `clearSession()` - Clear current session

**Usage:**
```typescript
const { sessionId, createSession, clearSession } = useSession();

// Session ID is automatically available for API calls
const { upload } = useUpload(); // Uses sessionId internally
```

## Testing

Unit tests are located in `__tests__/api.test.ts`. Tests cover:
- File upload with progress tracking
- Job status fetching
- Skeleton/skinning triggers
- Error handling

Run tests with:
```bash
npm test
```
