import { useState, useEffect, useCallback, useRef } from 'react';
import { getJob, triggerSkeleton, triggerSkinning } from '../services/api';
import type { Job } from '../types';

interface UseJobReturn {
  job: Job | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  generateSkeleton: (seed?: number) => Promise<void>;
  generateSkinning: () => Promise<void>;
}

/**
 * Custom hook for job management with automatic polling
 * Polls every 2 seconds when job is processing or queued
 */
export const useJob = (jobId: string | null): UseJobReturn => {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchJob = useCallback(async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      const jobData = await getJob(jobId);
      setJob(jobData);
      setError(null);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to fetch job';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const generateSkeleton = useCallback(
    async (seed?: number) => {
      if (!jobId) return;

      try {
        await triggerSkeleton(jobId, seed);
        await fetchJob(); // Refresh job status
      } catch (err: any) {
        const errorMessage = err.message || 'Failed to generate skeleton';
        setError(errorMessage);
      }
    },
    [jobId, fetchJob]
  );

  const generateSkinning = useCallback(async () => {
    if (!jobId) return;

    try {
      await triggerSkinning(jobId);
      await fetchJob(); // Refresh job status
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to generate skinning';
      setError(errorMessage);
    }
  }, [jobId, fetchJob]);

  // Set up polling when job is processing or queued
  useEffect(() => {
    if (!jobId) return;

    // Initial fetch
    fetchJob();

    // Start polling if job is processing or queued
    const shouldPoll =
      job?.status === 'processing' || job?.status === 'queued';

    if (shouldPoll) {
      intervalRef.current = setInterval(() => {
        fetchJob();
      }, 2000); // Poll every 2 seconds
    }

    // Cleanup interval on unmount or when polling should stop
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [jobId, job?.status, fetchJob]);

  return {
    job,
    loading,
    error,
    refresh: fetchJob,
    generateSkeleton,
    generateSkinning,
  };
};
