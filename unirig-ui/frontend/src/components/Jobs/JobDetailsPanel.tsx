import React, { useEffect, useState, useCallback } from 'react';
import { ModelViewer } from '../Viewer/ModelViewer';
import { ViewerErrorBoundary } from '../Viewer/ViewerErrorBoundary';
import { getJob } from '../../services/api';
import { downloadFile } from '../../utils/downloadFile';
import type { Job, JobStage } from '../../types';

interface JobDetailsPanelProps {
  jobId: string | null;
  onClose?: () => void;
}

/**
 * Detailed job information panel with 3D viewer integration
 * 
 * Features:
 * - Displays job status, progress, timestamps, and metadata
 * - Auto-refreshes processing jobs every 5 seconds
 * - Integrates ModelViewer for completed jobs
 * - Provides download button for completed models
 * - Shows retry button for failed jobs
 */
export const JobDetailsPanel: React.FC<JobDetailsPanelProps> = ({
  jobId,
  onClose,
}) => {
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Download state
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const fetchJobDetails = useCallback(async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      const jobData = await getJob(jobId);
      setJob(jobData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch job details');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  // Initial fetch when jobId changes
  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId, fetchJobDetails]);

  // Auto-refresh for processing jobs (every 5 seconds)
  useEffect(() => {
    if (!job || !jobId) return;

    // Only poll for non-terminal states
    const isProcessing = job.status === 'processing' || job.status === 'queued';
    if (!isProcessing) return;

    const interval = setInterval(() => {
      fetchJobDetails();
    }, 5000); // 5 seconds

    return () => clearInterval(interval);
  }, [job, jobId, fetchJobDetails]);

  const handleDownload = async () => {
    if (!job || !job.results?.final_file) return;

    // Reset download state
    setDownloading(true);
    setDownloadProgress(0);
    setDownloadError(null);

    try {
      // Construct download URL using the API endpoint
      const downloadUrl = `/api/download/${job.job_id}?type=final`;
      
      // Create a filename from the original file
      const baseFilename = job.filename.replace(/\.[^/.]+$/, '');
      const downloadFilename = `${baseFilename}_rigged.glb`;
      
      // Use downloadFile utility with progress tracking
      await downloadFile(downloadUrl, downloadFilename, {
        onProgress: (progress) => {
          setDownloadProgress(progress.percentage);
        },
        onComplete: () => {
          setDownloading(false);
          setDownloadProgress(100);
          // Reset progress after 2 seconds
          setTimeout(() => {
            setDownloadProgress(0);
          }, 2000);
        },
        onError: (error) => {
          setDownloadError(error.message || 'Download failed');
          setDownloading(false);
          setDownloadProgress(0);
        },
      });
    } catch (error: any) {
      // Handle any uncaught errors
      setDownloadError(error.message || 'Failed to download model');
      setDownloading(false);
      setDownloadProgress(0);
    }
  };

  const handleRetry = async () => {
    if (!job) return;
    
    // TODO: Implement retry logic - trigger job reprocessing
    console.log('Retry job:', job.job_id);
    alert('Retry functionality coming soon!');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusColor = () => {
    if (!job) return 'bg-gray-500';
    
    switch (job.status) {
      case 'queued':
        return 'bg-gray-500';
      case 'processing':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStageLabel = (stage: JobStage | null): string => {
    if (!stage) return '';
    
    switch (stage) {
      case 'upload':
        return 'Uploading';
      case 'skeleton_generation':
        return 'Generating Skeleton';
      case 'skinning_generation':
        return 'Generating Skinning';
      case 'merge':
        return 'Merging Results';
      default:
        return stage;
    }
  };

  const getModelUrl = (): string | undefined => {
    if (!job || job.status !== 'completed' || !job.results?.final_file) {
      return undefined;
    }
    
    return `/results/${job.session_id}/${job.results.final_file}`;
  };

  if (!jobId) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
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
          <p className="mt-2 text-sm">Select a job to view details</p>
        </div>
      </div>
    );
  }

  if (loading && !job) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading job details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-red-600">
          <div className="text-4xl mb-4">❌</div>
          <p className="text-lg font-semibold">Error Loading Job</p>
          <p className="text-sm mt-2">{error}</p>
          <button
            onClick={fetchJobDetails}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!job) {
    return null;
  }

  const modelUrl = getModelUrl();

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-800 text-white p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
          <div>
            <h2 className="text-lg font-semibold">{job.filename}</h2>
            <p className="text-xs text-gray-300">Job ID: {job.job_id}</p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-300 hover:text-white transition-colors"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {/* Status Section */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Status</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-500">Status</div>
              <div className="text-sm font-medium text-gray-900 mt-1">
                {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Progress</div>
              <div className="text-sm font-medium text-gray-900 mt-1">
                {job.progress*100}%
              </div>
            </div>
            {job.stage && job.status === 'processing' && (
              <div className="col-span-2">
                <div className="text-xs text-gray-500">Current Phase</div>
                <div className="text-sm font-medium text-blue-600 mt-1">
                  {getStageLabel(job.stage)}
                </div>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {(job.status === 'processing' || job.status === 'queued') && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${job.progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {job.error_message && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-700">{job.error_message}</p>
            </div>
          )}
        </div>

        {/* Metadata Section */}
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Details</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-gray-500">File Size</div>
              <div className="text-gray-900 mt-1">
                {formatFileSize(job.file_size)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Format</div>
              <div className="text-gray-900 mt-1">
                {job.filename.split('.').pop()?.toUpperCase() || 'Unknown'}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Created</div>
              <div className="text-gray-900 mt-1">
                {formatDate(job.created_at)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Last Updated</div>
              <div className="text-gray-900 mt-1">
                {formatDate(job.updated_at)}
              </div>
            </div>
          </div>
        </div>

        {/* Results Section - Only show for completed jobs */}
        {job.status === 'completed' && job.results && (
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Results</h3>
            <div className="space-y-2 text-sm">
              {job.results.skeleton_file && (
                <div className="flex items-center space-x-2">
                  <svg
                    className="w-4 h-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-700">Skeleton: </span>
                  <span className="text-gray-900 font-mono text-xs">
                    {job.results.skeleton_file}
                  </span>
                </div>
              )}
              {job.results.skin_file && (
                <div className="flex items-center space-x-2">
                  <svg
                    className="w-4 h-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-700">Skin: </span>
                  <span className="text-gray-900 font-mono text-xs">
                    {job.results.skin_file}
                  </span>
                </div>
              )}
              {job.results.final_file && (
                <div className="flex items-center space-x-2">
                  <svg
                    className="w-4 h-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-700">Final: </span>
                  <span className="text-gray-900 font-mono text-xs">
                    {job.results.final_file}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3D Viewer - Only show for completed jobs */}
        {job.status === 'completed' && modelUrl && (
          <div className="p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">
              3D Preview
            </h3>
            <div className="rounded-lg overflow-hidden border border-gray-300">
              <ViewerErrorBoundary modelUrl={modelUrl}>
                <ModelViewer 
                  modelUrl={modelUrl} 
                  jobId={job.job_id}
                  showGrid={true}
                  modelFileSize={job.file_size}
                />
              </ViewerErrorBoundary>
            </div>
          </div>
        )}
      </div>

      {/* Footer with Actions */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        {/* Download Error Message */}
        {downloadError && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-start space-x-2">
            <svg
              className="w-5 h-5 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="font-semibold">Download Failed</p>
              <p className="mt-1">{downloadError}</p>
              <button
                onClick={() => setDownloadError(null)}
                className="mt-2 text-xs underline hover:no-underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Download Progress Bar */}
        {downloading && downloadProgress > 0 && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-sm text-gray-700 mb-1">
              <span>Downloading...</span>
              <span>{downloadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${downloadProgress}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-end space-x-3">
          {job.status === 'failed' && (
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded transition-colors flex items-center space-x-2"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>Retry</span>
            </button>
          )}
          
          {job.status === 'completed' && job.results?.final_file && (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className={`px-4 py-2 rounded transition-colors flex items-center space-x-2 ${
                downloading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              } text-white`}
            >
              {downloading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Downloading...</span>
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  <span>Download Model</span>
                </>
              )}
            </button>
          )}

          {loading && (
            <div className="text-sm text-gray-500 flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Updating...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
