import React from 'react';
import { JobList } from '../components/Jobs/JobList';

interface JobsViewProps {
  sessionId: string | null;
}

/**
 * Jobs management view with filtering and monitoring
 */
export const JobsView: React.FC<JobsViewProps> = ({ sessionId }) => {
  if (!sessionId) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-6xl mb-4">⏳</div>
          <p className="text-gray-600">Initializing session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Job Management</h2>
            <p className="text-gray-600 mt-1">
              Monitor and manage your 3D model processing jobs
            </p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="font-mono text-xs">Session:</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
              {sessionId.slice(0, 8)}...
            </span>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">🔄</div>
            <div className="text-xs text-gray-600 mt-1">Processing</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">✓</div>
            <div className="text-xs text-gray-600 mt-1">Completed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-400">⏸</div>
            <div className="text-xs text-gray-600 mt-1">Queued</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">✗</div>
            <div className="text-xs text-gray-600 mt-1">Failed</div>
          </div>
        </div>
      </div>

      {/* Job List */}
      <JobList />

      {/* Info Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <span className="text-2xl">💡</span>
          <div className="text-sm">
            <h4 className="font-semibold text-blue-900 mb-1">Job Management Tips</h4>
            <ul className="text-blue-800 space-y-1">
              <li>• Jobs are processed sequentially for optimal GPU utilization</li>
              <li>• You can have one active job at a time per session</li>
              <li>• Completed job results are available for 7 days</li>
              <li>• Click on any job to view detailed progress and results</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            📊 Job Status Guide
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs font-medium">
                Queued
              </span>
              <span className="text-gray-600">Waiting for processing</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                Processing
              </span>
              <span className="text-gray-600">Currently running on GPU</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">
                Completed
              </span>
              <span className="text-gray-600">Ready to download</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium">
                Failed
              </span>
              <span className="text-gray-600">Error during processing</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            ⚡ Processing Stages
          </h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div>
              <strong className="text-gray-900">1. Upload:</strong> File validation and storage
            </div>
            <div>
              <strong className="text-gray-900">2. Skeleton:</strong> Bone structure generation (~30-60s)
            </div>
            <div>
              <strong className="text-gray-900">3. Skinning:</strong> Weight calculation (~60-120s)
            </div>
            <div>
              <strong className="text-gray-900">4. Merge:</strong> Final model assembly (~10-20s)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
