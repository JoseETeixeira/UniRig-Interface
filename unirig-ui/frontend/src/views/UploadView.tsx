import React, { useState } from 'react';
import { UploadZone } from '../components/Upload/UploadZone';
import { ProcessingView } from '../components/Processing/ProcessingView';
import type { UploadResponse } from '../types';

interface UploadViewProps {
  sessionId: string | null;
}

/**
 * Main upload view with drag-and-drop and processing workflow
 */
export const UploadView: React.FC<UploadViewProps> = ({ sessionId }) => {
  const [uploadedJob, setUploadedJob] = useState<UploadResponse | null>(null);

  const handleUploadComplete = (response: UploadResponse) => {
    setUploadedJob(response);
  };

  const handleUploadError = (error: string) => {
    console.error('Upload error:', error);
  };

  const handleJobComplete = () => {
    // Reset to upload state after job completion
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
        <ProcessingView
          jobId={uploadedJob.job_id}
          sessionId={sessionId}
          filename={uploadedJob.filename}
          onComplete={handleJobComplete}
        />
      )}
    </div>
  );
};
