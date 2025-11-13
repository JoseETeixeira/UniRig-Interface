import React, { useState, useEffect } from 'react';
import { SkeletonPanel } from './SkeletonPanel';
import { SkinningPanel } from './SkinningPanel';
import { ExportPanel } from './ExportPanel';
import { useJob } from '../../hooks/useJob';

interface ProcessingViewProps {
  jobId: string;
  sessionId: string;
  filename: string;
  onComplete?: () => void;
}

type ProcessingStage = 'skeleton' | 'skinning' | 'export';

/**
 * Main processing workflow view
 * Handles skeleton generation, skinning, and export
 */
export const ProcessingView: React.FC<ProcessingViewProps> = ({
  jobId,
  sessionId,
  filename,
  onComplete,
}) => {
  const { job, loading, error } = useJob(jobId);
  const [currentStage, setCurrentStage] = useState<ProcessingStage>('skeleton');
  const [skeletonJobId, setSkeletonJobId] = useState<string | null>(null);
  const [skinningJobId, setSkinningJobId] = useState<string | null>(null);

  useEffect(() => {
    // Auto-advance to skinning stage when skeleton is completed
    if (skeletonJobId && job?.status === 'completed' && currentStage === 'skeleton') {
      // Wait a moment before auto-advancing to give user time to see completion
      const timer = setTimeout(() => {
        setCurrentStage('skinning');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [skeletonJobId, job, currentStage]);

  useEffect(() => {
    // Auto-advance to export stage when skinning is completed
    if (skinningJobId && job?.status === 'completed' && currentStage === 'skinning') {
      const timer = setTimeout(() => {
        setCurrentStage('export');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [skinningJobId, job, currentStage]);

  const handleSkeletonGenerated = (newJobId: string) => {
    setSkeletonJobId(newJobId);
  };

  const handleSkinningGenerated = (newJobId: string) => {
    setSkinningJobId(newJobId);
  };

  const handleExportComplete = () => {
    if (onComplete) {
      onComplete();
    }
  };

  const handleNewUpload = () => {
    if (onComplete) {
      onComplete();
    }
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <span className="text-2xl">❌</span>
          <div>
            <h3 className="font-semibold text-red-900 mb-2">Processing Error</h3>
            <p className="text-red-800 mb-4">{error}</p>
            <button
              onClick={handleNewUpload}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Upload New Model
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Stepper */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between">
          {/* Step 1: Skeleton */}
          <div className="flex items-center space-x-3 flex-1">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                currentStage === 'skeleton'
                  ? 'bg-blue-500 border-blue-500 text-white'
                  : skeletonJobId
                  ? 'bg-green-500 border-green-500 text-white'
                  : 'bg-gray-200 border-gray-300 text-gray-600'
              }`}
            >
              {skeletonJobId ? '✓' : '1'}
            </div>
            <div>
              <div className="font-semibold text-sm text-gray-900">Skeleton</div>
              <div className="text-xs text-gray-500">Generate bone structure</div>
            </div>
          </div>

          <div className="flex-shrink-0 w-16 h-0.5 bg-gray-300 mx-2" />

          {/* Step 2: Skinning */}
          <div className="flex items-center space-x-3 flex-1">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                currentStage === 'skinning'
                  ? 'bg-blue-500 border-blue-500 text-white'
                  : skinningJobId
                  ? 'bg-green-500 border-green-500 text-white'
                  : 'bg-gray-200 border-gray-300 text-gray-600'
              }`}
            >
              {skinningJobId ? '✓' : '2'}
            </div>
            <div>
              <div className="font-semibold text-sm text-gray-900">Skinning</div>
              <div className="text-xs text-gray-500">Generate weights</div>
            </div>
          </div>

          <div className="flex-shrink-0 w-16 h-0.5 bg-gray-300 mx-2" />

          {/* Step 3: Export */}
          <div className="flex items-center space-x-3 flex-1">
            <div
              className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                currentStage === 'export'
                  ? 'bg-blue-500 border-blue-500 text-white'
                  : 'bg-gray-200 border-gray-300 text-gray-600'
              }`}
            >
              3
            </div>
            <div>
              <div className="font-semibold text-sm text-gray-900">Export</div>
              <div className="text-xs text-gray-500">Download model</div>
            </div>
          </div>
        </div>
      </div>

      {/* Model Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600">Processing Model</div>
            <div className="font-semibold text-gray-900">{filename}</div>
          </div>
          <div className="text-sm text-gray-600">
            Session: <span className="font-mono text-xs">{sessionId.slice(0, 8)}...</span>
          </div>
        </div>
      </div>

      {/* Stage Content */}
      <div>
        {currentStage === 'skeleton' && (
          <SkeletonPanel
            jobId={jobId}
            sessionId={sessionId}
            onSkeletonGenerated={handleSkeletonGenerated}
            onNext={() => setCurrentStage('skinning')}
          />
        )}

        {currentStage === 'skinning' && skeletonJobId && (
          <SkinningPanel
            jobId={skeletonJobId}
            sessionId={sessionId}
            onSkinningGenerated={handleSkinningGenerated}
            onNext={() => setCurrentStage('export')}
            onBack={() => setCurrentStage('skeleton')}
          />
        )}

        {currentStage === 'export' && skinningJobId && (
          <ExportPanel
            jobId={skinningJobId}
            sessionId={sessionId}
            onComplete={handleExportComplete}
            onNewUpload={handleNewUpload}
          />
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between">
          <button
            onClick={handleNewUpload}
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Start Over with New Model
          </button>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <button
              onClick={() => setCurrentStage('skeleton')}
              disabled={currentStage === 'skeleton'}
              className="hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Skeleton
            </button>
            <button
              onClick={() => setCurrentStage('skinning')}
              disabled={!skeletonJobId || currentStage === 'skinning'}
              className="hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Skinning
            </button>
            <button
              onClick={() => setCurrentStage('export')}
              disabled={!skinningJobId || currentStage === 'export'}
              className="hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Export
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
