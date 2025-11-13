import React, { useEffect, useState } from 'react';
import { JobCard } from './JobCard';
import { listJobs } from '../../services/api';
import { useSession } from '../../hooks';
import type { Job, JobStatus } from '../../types';

interface JobListProps {
  onJobSelect?: (jobId: string) => void;
}

/**
 * Display list of jobs with filtering and auto-refresh
 */
export const JobList: React.FC<JobListProps> = ({ onJobSelect }) => {
  const { sessionId } = useSession();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<JobStatus | 'all'>('all' as JobStatus | 'all');

  const fetchJobs = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      const jobList = await listJobs(sessionId);
      setJobs(jobList);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchJobs();
  }, [sessionId]);

  // Auto-refresh when there are active jobs
  useEffect(() => {
    const hasActiveJobs = jobs.some(
      (job) => job.status === 'processing' || job.status === 'queued'
    );

    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      fetchJobs();
    }, 3000); // Refresh every 3 seconds

    return () => clearInterval(interval);
  }, [jobs]);

  // Filter jobs by status
  const filteredJobs =
    filterStatus === 'all'
      ? jobs
      : jobs.filter((job) => job.status === filterStatus);

  // Count jobs by status
  const statusCounts = {
    all: jobs.length,
    queued: jobs.filter((j) => j.status === 'queued').length,
    processing: jobs.filter((j) => j.status === 'processing').length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
  };

  return (
    <div className="space-y-4">
      {/* Header with filters */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Jobs</h2>
        <button
          onClick={fetchJobs}
          disabled={loading}
          className="px-3 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        {(['all', 'queued', 'processing', 'completed', 'failed'] as const).map(
          (status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status as JobStatus | 'all')}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                filterStatus === status
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)} (
              {statusCounts[status]})
            </button>
          )
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Job List */}
      {filteredJobs.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs</h3>
          <p className="mt-1 text-sm text-gray-500">
            {filterStatus === 'all'
              ? 'Upload a model to get started'
              : `No ${filterStatus} jobs`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredJobs.map((job) => (
            <JobCard
              key={job.job_id}
              job={job}
              onClick={() => onJobSelect?.(job.job_id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
