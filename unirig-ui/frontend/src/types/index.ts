// TypeScript interfaces matching backend data models

export enum JobStatus {
  UPLOADED = 'uploaded',
  QUEUED = 'queued',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum JobStage {
  UPLOAD = 'upload',
  SKELETON = 'skeleton_generation',
  SKINNING = 'skinning_generation',
  MERGE = 'merge',
}

export interface JobResults {
  skeleton_file: string | null;
  skin_file: string | null;
  final_file: string | null;
}

export interface Job {
  job_id: string;
  session_id: string;
  filename: string;
  file_size: number;
  file_path: string;
  status: JobStatus;
  progress: number;
  stage: JobStage | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
  results: JobResults;
}

export interface Session {
  session_id: string;
  created_at: string;
  last_accessed: string;
  expired: boolean;
}

export interface UploadResponse {
  job_id: string;
  session_id: string;
  filename: string;
  file_size: number;
  status: JobStatus;
}

export interface HealthResponse {
  status: string;
  version: string;
  gpu_available: boolean;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: string;
    suggestion?: string;
    documentation?: string;
  };
}
