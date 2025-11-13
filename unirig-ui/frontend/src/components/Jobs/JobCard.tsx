import React from 'react';
import { JobProgress } from './JobProgress';
import type { Job } from '../../types';

interface JobCardProps {
  job: Job;
  onClick?: () => void;
  onDelete?: () => void;
}

/**
 * Display individual job details with status and actions
 */
export const JobCard: React.FC<JobCardProps> = ({ job, onClick, onDelete }) => {
  const getStatusColor = () => {
    switch (job.status) {
      case 'queued':
        return 'bg-gray-50 border-gray-300';
      case 'processing':
        return 'bg-blue-50 border-blue-300';
      case 'completed':
        return 'bg-green-50 border-green-300';
      case 'failed':
        return 'bg-red-50 border-red-300';
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  const getStatusBadge = () => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (job.status) {
      case 'queued':
        return (
          <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
            Queued
          </span>
        );
      case 'processing':
        return (
          <span className={`${baseClasses} bg-blue-100 text-blue-800`}>
            Processing
          </span>
        );
      case 'completed':
        return (
          <span className={`${baseClasses} bg-green-100 text-green-800`}>
            Completed
          </span>
        );
      case 'failed':
        return (
          <span className={`${baseClasses} bg-red-100 text-red-800`}>
            Failed
          </span>
        );
      default:
        return (
          <span className={`${baseClasses} bg-gray-100 text-gray-800`}>
            {job.status}
          </span>
        );
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const getStageLabel = () => {
    switch (job.stage) {
      case 'upload':
        return 'Uploading';
      case 'skeleton_generation':
        return 'Generating Skeleton';
      case 'skinning_generation':
        return 'Generating Skinning';
      case 'merge':
        return 'Merging Results';
      default:
        return job.stage;
    }
  };

  return (
    <div
      className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${getStatusColor()}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Filename and Status */}
          <div className="flex items-center space-x-2 mb-2">
            <h3 className="text-sm font-medium text-gray-900 truncate">
              {job.filename}
            </h3>
            {getStatusBadge()}
          </div>

          {/* Job Details */}
          <div className="flex items-center space-x-4 text-xs text-gray-500">
            <span>{formatFileSize(job.file_size)}</span>
            <span>•</span>
            <span>{formatDate(job.created_at)}</span>
            {job.stage && job.status === 'processing' && (
              <>
                <span>•</span>
                <span className="text-blue-600 font-medium">
                  {getStageLabel()}
                </span>
              </>
            )}
          </div>

          {/* Progress Bar */}
          {(job.status === 'processing' || job.status === 'queued') && (
            <div className="mt-3">
              <JobProgress progress={job.progress} stage={job.stage} />
            </div>
          )}

          {/* Error Message */}
          {job.error_message && (
            <div className="mt-2 text-xs text-red-600">
              {job.error_message}
            </div>
          )}

          {/* Results */}
          {job.status === 'completed' && job.results && (
            <div className="mt-2 flex items-center space-x-2 text-xs">
              {job.results.skeleton_file && (
                <span className="inline-flex items-center text-green-600">
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Skeleton
                </span>
              )}
              {job.results.skin_file && (
                <span className="inline-flex items-center text-green-600">
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Skinning
                </span>
              )}
              {job.results.final_file && (
                <span className="inline-flex items-center text-green-600">
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Final
                </span>
              )}
            </div>
          )}
        </div>

        {/* Delete Button */}
        {onDelete && job.status !== 'processing' && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="ml-4 p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete job"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
