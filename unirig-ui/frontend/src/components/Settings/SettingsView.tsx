import React, { useState, useEffect } from 'react';
import { Button } from '../Common/Button';
import { ConfirmModal } from '../Common/ConfirmModal';
import { useNotifications } from '../Common/Notification';
import axios from 'axios';

interface DiskSpaceInfo {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  percent_used: number;
  warning?: string;
}

interface SessionStats {
  session_id: string;
  created_at: string;
  last_accessed: string;
  upload_count: number;
  uploads_size_mb: number;
  results_size_mb: number;
  total_size_mb: number;
}

/**
 * Settings view with session management and disk space info
 */
export const SettingsView: React.FC = () => {
  const [diskSpace, setDiskSpace] = useState<DiskSpaceInfo | null>(null);
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const { addNotification } = useNotifications();

  // Get session ID from cookie
  const getSessionId = (): string | null => {
    const match = document.cookie.match(/session_id=([^;]+)/);
    return match ? match[1] : null;
  };

  // Load disk space and session stats
  useEffect(() => {
    loadDiskSpace();
    loadSessionStats();
  }, []);

  const loadDiskSpace = async () => {
    try {
      const response = await axios.get('/api/disk-space');
      setDiskSpace(response.data);
    } catch (error) {
      console.error('Failed to load disk space:', error);
    }
  };

  const loadSessionStats = async () => {
    try {
      const sessionId = getSessionId();
      if (!sessionId) return;

      const response = await axios.get(`/api/sessions/${sessionId}/stats`);
      setSessionStats(response.data);
    } catch (error) {
      console.error('Failed to load session stats:', error);
    }
  };

  const handleClearResults = async () => {
    setIsClearing(true);
    try {
      const sessionId = getSessionId();
      if (!sessionId) {
        throw new Error('No session ID found');
      }

      await axios.delete(`/api/sessions/${sessionId}`);
      
      addNotification({
        title: 'Results Cleared',
        message: 'All your uploads and results have been deleted.',
        variant: 'success',
      });

      setShowConfirmClear(false);
      
      // Reload stats and refresh page
      setTimeout(() => {
        window.location.reload();
      }, 1500);
      
    } catch (error: any) {
      addNotification({
        title: 'Clear Failed',
        message: error.response?.data?.detail || 'Failed to clear results',
        variant: 'error',
      });
    } finally {
      setIsClearing(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const formatSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`;
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(2)} GB`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Disk Space Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">💾 Disk Space</h2>
        {diskSpace ? (
          <div>
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Storage Used</span>
                <span>{diskSpace.percent_used.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    diskSpace.percent_used > 90
                      ? 'bg-red-500'
                      : diskSpace.percent_used > 75
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(diskSpace.percent_used, 100)}%` }}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-lg font-semibold text-gray-900">
                  {diskSpace.total_gb.toFixed(1)} GB
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Used</p>
                <p className="text-lg font-semibold text-gray-900">
                  {diskSpace.used_gb.toFixed(1)} GB
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Free</p>
                <p className="text-lg font-semibold text-gray-900">
                  {diskSpace.free_gb.toFixed(1)} GB
                </p>
              </div>
            </div>

            {diskSpace.warning && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm text-yellow-800">{diskSpace.warning}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500">Loading disk space info...</p>
        )}
      </div>

      {/* Session Info Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">📊 Session Info</h2>
        {sessionStats ? (
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Session ID:</span>
              <span className="font-mono text-sm text-gray-900">
                {sessionStats.session_id.slice(0, 8)}...
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Created:</span>
              <span className="text-gray-900">{formatDate(sessionStats.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Last Activity:</span>
              <span className="text-gray-900">{formatDate(sessionStats.last_accessed)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Uploaded Files:</span>
              <span className="text-gray-900">{sessionStats.upload_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Storage Used:</span>
              <span className="font-semibold text-gray-900">
                {formatSize(sessionStats.total_size_mb)}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">Loading session info...</p>
        )}
      </div>

      {/* Data Management Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">🗑️ Data Management</h2>
        <p className="text-gray-600 mb-4">
          Clear all your uploaded files and generated results. This action cannot be undone.
        </p>
        <p className="text-sm text-gray-500 mb-4">
          Note: Sessions automatically expire after 24 hours of inactivity.
        </p>
        <Button
          variant="danger"
          size="md"
          onClick={() => setShowConfirmClear(true)}
        >
          Clear All Results
        </Button>
      </div>

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={showConfirmClear}
        onClose={() => setShowConfirmClear(false)}
        onConfirm={handleClearResults}
        title="Clear All Results?"
        message="This will permanently delete all your uploads and generated rigging results. This action cannot be undone."
        confirmText="Yes, Clear Everything"
        cancelText="Cancel"
        variant="danger"
        isLoading={isClearing}
      />
    </div>
  );
};
