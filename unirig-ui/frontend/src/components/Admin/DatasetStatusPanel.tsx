/**
 * DatasetStatusPanel component for monitoring and managing motion dataset status
 * Shows dataset download progress, integrity status, and provides admin controls
 */

import { useState, useEffect, useCallback } from 'react';
import { getDatasetStatus, refreshDataset } from '../../services/api';
import type { DatasetStatus } from '../../types';

/**
 * Get status badge color based on download status
 */
function getStatusBadgeColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-600';
    case 'downloading':
      return 'bg-blue-600';
    case 'failed':
      return 'bg-red-600';
    case 'not_started':
      return 'bg-gray-600';
    default:
      return 'bg-gray-600';
  }
}

/**
 * Get status display text
 */
function getStatusText(status: string): string {
  switch (status) {
    case 'completed':
      return 'Ready';
    case 'downloading':
      return 'Downloading';
    case 'failed':
      return 'Failed';
    case 'not_started':
      return 'Not Started';
    default:
      return 'Unknown';
  }
}

/**
 * DatasetStatusPanel displays motion dataset status and provides admin controls
 */
export const DatasetStatusPanel: React.FC = () => {
  const [status, setStatus] = useState<DatasetStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshSuccess, setRefreshSuccess] = useState<string | null>(null);

  /**
   * Fetch dataset status from API
   */
  const fetchStatus = useCallback(async () => {
    try {
      const data = await getDatasetStatus();
      setStatus(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch dataset status:', err);
      setError(err.message || 'Failed to fetch dataset status');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Handle refresh button click
   */
  const handleRefresh = useCallback(async (force: boolean = false) => {
    setRefreshing(true);
    setRefreshError(null);
    setRefreshSuccess(null);

    try {
      const result = await refreshDataset(force);
      setRefreshSuccess(result.message);
      
      // Refresh status after a short delay
      setTimeout(() => {
        fetchStatus();
      }, 1000);
    } catch (err: any) {
      console.error('Failed to refresh dataset:', err);
      setRefreshError(err.response?.data?.detail?.message || err.message || 'Failed to refresh dataset');
    } finally {
      setRefreshing(false);
    }
  }, [fetchStatus]);

  // Initial fetch and polling
  useEffect(() => {
    fetchStatus();

    // Poll every 5 seconds if downloading
    const interval = setInterval(() => {
      if (status?.downloadStatus === 'downloading') {
        fetchStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchStatus, status?.downloadStatus]);

  // Auto-hide success message after 5 seconds
  useEffect(() => {
    if (refreshSuccess) {
      const timeout = setTimeout(() => {
        setRefreshSuccess(null);
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [refreshSuccess]);

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <svg className="animate-spin h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="ml-3 text-gray-300">Loading dataset status...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="bg-red-900 border border-red-700 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-6 h-6 text-red-400 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h4 className="text-red-300 font-semibold mb-1">Error Loading Dataset Status</h4>
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  const isDownloading = status.downloadStatus === 'downloading';
  const isCompleted = status.downloadStatus === 'completed';

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-200 flex items-center">
            <svg className="w-6 h-6 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
            Motion Dataset Status
          </h2>
          
          {/* Status Badge */}
          <span className={`px-3 py-1 rounded-full text-sm font-medium text-white ${getStatusBadgeColor(status.downloadStatus)}`}>
            {getStatusText(status.downloadStatus)}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Download Progress */}
        {isDownloading && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-300">Download Progress</span>
              <span className="text-sm font-semibold text-blue-400">{status.progress}%</span>
            </div>
            <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-300 ease-out relative overflow-hidden"
                style={{ width: `${status.progress}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">{status.message}</p>
          </div>
        )}

        {/* Status Message */}
        {!isDownloading && (
          <div className="bg-gray-900 rounded-lg p-4">
            <p className="text-sm text-gray-300">{status.message}</p>
          </div>
        )}

        {/* Dataset Info Grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Dataset Exists */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Dataset Exists</span>
              {status.exists ? (
                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>
          </div>

          {/* Integrity Valid */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Integrity Valid</span>
              {status.integrityValid ? (
                <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              )}
            </div>
          </div>

          {/* Motion Clips Count */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex flex-col">
              <span className="text-sm text-gray-400 mb-1">Motion Clips</span>
              <span className="text-2xl font-bold text-blue-400">{status.clipCount}</span>
            </div>
          </div>

          {/* Dataset Size (Estimated) */}
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex flex-col">
              <span className="text-sm text-gray-400 mb-1">Est. Dataset Size</span>
              <span className="text-2xl font-bold text-blue-400">~5-10 GB</span>
            </div>
          </div>
        </div>

        {/* Admin Actions */}
        <div className="border-t border-gray-700 pt-6">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Admin Actions</h3>
          
          <div className="flex flex-wrap gap-3">
            {/* Refresh Button */}
            <button
              onClick={() => handleRefresh(false)}
              disabled={refreshing || isDownloading}
              className={`
                px-4 py-2 rounded-lg font-medium transition-colors flex items-center
                ${refreshing || isDownloading
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
                }
              `}
            >
              {refreshing ? (
                <>
                  <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Refreshing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh Dataset
                </>
              )}
            </button>

            {/* Force Re-download Button */}
            {isCompleted && (
              <button
                onClick={() => handleRefresh(true)}
                disabled={refreshing || isDownloading}
                className={`
                  px-4 py-2 rounded-lg font-medium transition-colors flex items-center
                  ${refreshing || isDownloading
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                  }
                `}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Force Re-download
              </button>
            )}
          </div>

          {/* Action Feedback */}
          {refreshSuccess && (
            <div className="mt-4 bg-green-900 border border-green-700 rounded-lg p-3 flex items-start">
              <svg className="w-5 h-5 text-green-400 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-green-200">{refreshSuccess}</p>
            </div>
          )}

          {refreshError && (
            <div className="mt-4 bg-red-900 border border-red-700 rounded-lg p-3 flex items-start">
              <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-sm text-red-200">{refreshError}</p>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-blue-400 mr-3 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="text-sm text-blue-200">
              <p className="font-medium mb-1">About Motion Dataset</p>
              <p>The motion dataset contains pre-captured animations that can be retargeted to your rigged models. The dataset is downloaded once and cached locally for fast access.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
