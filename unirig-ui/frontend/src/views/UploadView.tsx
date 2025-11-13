import React, { useState } from 'react';
import { UploadZone } from '../components/Upload/UploadZone';
import { useNotifications } from '../components/Common/Notification';
import type { UploadResponse } from '../types';

interface UploadViewProps {
  sessionId: string | null;
}

/**
 * Main upload view with drag-and-drop and processing workflow
 */
export const UploadView: React.FC<UploadViewProps> = ({ sessionId }) => {
  const [uploadedJob, setUploadedJob] = useState<UploadResponse | null>(null);
  const { addNotification } = useNotifications();

  const handleUploadComplete = (response: UploadResponse) => {
    setUploadedJob(response);
    addNotification({
      variant: 'success',
      title: 'Upload Successful!',
      message: `File "${response.filename}" uploaded successfully. Job ID: ${response.job_id}`,
      duration: 5000
    });
  };

  const handleUploadError = (error: string) => {
    addNotification({
      variant: 'error',
      title: 'Upload Failed',
      message: error,
      duration: 5000
    });
  };

  const handleStartNew = () => {
    setUploadedJob(null);
  };

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
    <div className="max-w-7xl mx-auto">
      {!uploadedJob ? (
        <div className="space-y-6">
          {/* Welcome Section */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Welcome to UniRig 🦴
            </h2>
            <p className="text-gray-700 mb-4">
              Automatically generate skeletons and skinning weights for your 3D models using deep learning.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-start space-x-2">
                <span className="text-2xl">📤</span>
                <div>
                  <h3 className="font-semibold text-gray-900">1. Upload</h3>
                  <p className="text-gray-600">Drop your 3D model</p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-2xl">🦴</span>
                <div>
                  <h3 className="font-semibold text-gray-900">2. Generate</h3>
                  <p className="text-gray-600">Create skeleton & skinning</p>
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-2xl">📦</span>
                <div>
                  <h3 className="font-semibold text-gray-900">3. Export</h3>
                  <p className="text-gray-600">Download rigged model</p>
                </div>
              </div>
            </div>
          </div>

          {/* Upload Zone */}
          <UploadZone
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
          />

          {/* Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                ✅ Supported Formats
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <span className="w-16 font-mono text-gray-900">.obj</span>
                  <span>Wavefront OBJ</span>
                </li>
                <li className="flex items-center">
                  <span className="w-16 font-mono text-gray-900">.fbx</span>
                  <span>Autodesk FBX</span>
                </li>
                <li className="flex items-center">
                  <span className="w-16 font-mono text-gray-900">.glb</span>
                  <span>GL Transmission Format</span>
                </li>
                <li className="flex items-center">
                  <span className="w-16 font-mono text-gray-900">.vrm</span>
                  <span>VRM (VRoid format)</span>
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                ⚡ Performance Tips
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Models under 50MB process faster</li>
                <li>• Clean topology improves results</li>
                <li>• Manifold meshes work best</li>
                <li>• GPU acceleration enabled</li>
              </ul>
            </div>
          </div>

          {/* Requirements Note */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">⚠️</span>
              <div className="text-sm">
                <h4 className="font-semibold text-yellow-900 mb-1">
                  Model Requirements
                </h4>
                <p className="text-yellow-800">
                  For best results, ensure your model has clean geometry and is positioned upright (Y-up).
                  Models should be centered at the origin and have appropriate scale.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Show upload success and next steps */
        <div className="space-y-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <span className="text-3xl">✅</span>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-green-900 mb-2">
                  Upload Successful!
                </h3>
                <p className="text-green-800 mb-4">
                  File <strong>{uploadedJob.filename}</strong> has been uploaded successfully.
                </p>
                <div className="bg-white rounded-lg p-4 border border-green-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Job ID</div>
                      <div className="font-mono text-xs text-gray-900">
                        {uploadedJob.job_id}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Session ID</div>
                      <div className="font-mono text-xs text-gray-900">
                        {uploadedJob.session_id}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">File Size</div>
                      <div className="font-mono text-xs text-gray-900">
                        {(uploadedJob.file_size / (1024 * 1024)).toFixed(2)} MB
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Status</div>
                      <div className="font-mono text-xs text-gray-900">
                        {uploadedJob.status}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">
              Next Steps
            </h3>
            <div className="space-y-3 text-sm text-blue-800">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">1️⃣</span>
                <div>
                  <strong>Navigate to Jobs:</strong> Click the "Jobs" tab in the header to view your job
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-2xl">2️⃣</span>
                <div>
                  <strong>Generate Skeleton:</strong> Once in the jobs view, click your job to start skeleton generation
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-2xl">3️⃣</span>
                <div>
                  <strong>Generate Skinning:</strong> After skeleton approval, generate skinning weights
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-2xl">4️⃣</span>
                <div>
                  <strong>Export Model:</strong> Download your rigged model in FBX or GLB format
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={handleStartNew}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              ← Upload Another Model
            </button>
            <button
              onClick={() => window.location.href = '/#jobs'}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
            >
              View Jobs →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
