// TypeScript interfaces matching backend data models
import * as THREE from 'three';

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

export interface Animation {
  id: string;
  name: string;
  duration: number; // Duration in seconds
  frameCount: number;
  clip: THREE.AnimationClip;
  source: 'embedded' | 'retargeted';
  retargetingJobId?: string; // If retargeted
}

export interface MotionClip {
  id: string;
  name: string;
  fileName: string;
  duration: number; // Duration in seconds
  frameCount: number;
  skeletonType: 'humanoid' | 'quadruped' | 'other';
  tags: string[];
  thumbnailUrl?: string;
  boneCount: number;
  datasetSource: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface MotionClipsResponse {
  clips: MotionClip[];
  total: number;
  limit: number;
  offset: number;
}

export interface RetargetingJob {
  id: string;
  jobId: string;
  motionClipId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  resultPath?: string;
  error?: string;
  skeletonCompatibility?: Record<string, unknown>;
  processingTime?: number; // seconds
  createdAt: string;
  completedAt?: string;
}

export interface DatasetStatus {
  exists: boolean;
  downloadStatus: 'not_started' | 'downloading' | 'completed' | 'failed';
  progress: number; // 0-100
  message: string;
  integrityValid: boolean;
  clipCount: number;
}

export interface RefreshDatasetResponse {
  status: 'started' | 'completed' | 'exists';
  message: string;
  clipCount: number;
}
