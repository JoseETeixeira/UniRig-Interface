import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import type { Mocked } from 'vitest';
import {
  uploadFile,
  getJob,
  // listJobs,
  // triggerSkeleton,
  // triggerSkinning,
  // deleteJob,
  // downloadFile,
  // checkHealth,
} from '../api';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as Mocked<typeof axios>;

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('uploadFile', () => {
    it('should upload file with progress tracking', async () => {
      const mockFile = new File(['content'], 'test.glb', {
        type: 'model/gltf-binary',
      });
      const mockResponse = {
        data: {
          job_id: 'test-job-id',
          session_id: 'test-session-id',
          filename: 'test.glb',
          file_size: 1024,
          status: 'uploaded',
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const progressCallback = vi.fn();
      const result = await uploadFile(mockFile, 'session-123', progressCallback);

      expect(result).toEqual(mockResponse.data);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      );
    });
  });

  describe('getJob', () => {
    it('should fetch job by ID', async () => {
      const mockJob = {
        job_id: 'job-123',
        status: 'processing',
        progress: 0.5,
      };
      mockedAxios.get.mockResolvedValue({ data: mockJob });

      const result = await getJob('job-123');

      expect(result).toEqual(mockJob);
      expect(mockedAxios.get).toHaveBeenCalledWith('/jobs/job-123');
    });
  });

  describe('triggerSkeleton', () => {
    it('should trigger skeleton generation with seed', async () => {
      const mockResponse = { task_id: 'task-123', status: 'queued' };
      mockedAxios.post.mockResolvedValue({ data: mockResponse });

      const result = await triggerSkeleton('job-123', 42);

      expect(result).toEqual(mockResponse);
      expect(mockedAxios.post).toHaveBeenCalledWith('/jobs/job-123/skeleton', {
        seed: 42,
      });
    });
  });

  // Add more test cases for other API methods...
});
