import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Job,
  UploadResponse,
  HealthResponse,
  ErrorResponse,
} from '../types';

// Create axios instance with base configuration
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    // Handle common errors
    if (error.response) {
      const errorData = error.response.data;
      if (errorData?.error) {
        // Return structured error
        return Promise.reject({
          code: errorData.error.code,
          message: errorData.error.message,
          details: errorData.error.details,
          suggestion: errorData.error.suggestion,
        });
      }
    }
    // Return generic error
    return Promise.reject({
      code: 'NETWORK_ERROR',
      message: error.message || 'An unexpected error occurred',
    });
  }
);

// API Methods

/**
 * Upload a 3D model file
 */
export const uploadFile = async (
  file: File,
  sessionId?: string,
  onProgress?: (progress: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const progress = (progressEvent.loaded / progressEvent.total) * 100;
        onProgress(progress);
      }
    },
  });

  return response.data;
};

/**
 * Get job status by ID
 */
export const getJob = async (jobId: string): Promise<Job> => {
  const response = await api.get<Job>(`/jobs/${jobId}`);
  return response.data;
};

/**
 * List all jobs for a session
 */
export const listJobs = async (sessionId: string): Promise<Job[]> => {
  const response = await api.get<{ jobs: Job[] }>(
    `/sessions/${sessionId}/jobs`
  );
  return response.data.jobs;
};

/**
 * Trigger skeleton generation
 */
export const triggerSkeleton = async (
  jobId: string,
  seed?: number
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post(`/jobs/${jobId}/skeleton`, { seed });
  return response.data;
};

/**
 * Trigger skinning generation
 */
export const triggerSkinning = async (
  jobId: string
): Promise<{ task_id: string; status: string }> => {
  const response = await api.post(`/jobs/${jobId}/skinning`);
  return response.data;
};

/**
 * Delete a job
 */
export const deleteJob = async (jobId: string): Promise<void> => {
  await api.delete(`/jobs/${jobId}`);
};

/**
 * Download result file
 */
export const downloadFile = async (
  jobId: string,
  type: 'skeleton' | 'skin' | 'final'
): Promise<Blob> => {
  const response = await api.get(`/download/${jobId}`, {
    params: { type },
    responseType: 'blob',
  });
  return response.data;
};

/**
 * Check API health
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

export default api;
