import React, { useState, useEffect } from 'react';
import { Job } from '../../types';

interface SkeletonPanelProps {
  job: Job | null;
  onGenerateSkeleton: (seed?: number) => Promise<void>;
  onApprove: () => void;
}

export const SkeletonPanel: React.FC<SkeletonPanelProps> = ({
  job,
  onGenerateSkeleton,
  onApprove
}) => {
  const [seed, setSeed] = useState<number>(() => Math.floor(Math.random() * 10000));
  const [isGenerating, setIsGenerating] = useState(false);
  const [previousSeeds, setPreviousSeeds] = useState<number[]>([]);

  const hasSkeleton = job?.results?.skeleton_file;
  const isProcessing = job?.status === 'processing' && job?.stage === 'skeleton_generation';
  const canGenerate = job?.status === 'uploaded' || job?.status === 'completed' || hasSkeleton;

  useEffect(() => {
    if (isProcessing) {
      setIsGenerating(true);
    } else if (isGenerating) {
      setIsGenerating(false);
      // Save the seed that was just used
      if (hasSkeleton && !previousSeeds.includes(seed)) {
        setPreviousSeeds(prev => [...prev, seed]);
      }
    }
  }, [isProcessing, hasSkeleton, isGenerating, seed, previousSeeds]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await onGenerateSkeleton(seed);
    } catch (error) {
      console.error('Failed to generate skeleton:', error);
      setIsGenerating(false);
    }
  };

  const handleRegenerate = () => {
    const newSeed = Math.floor(Math.random() * 10000);
    setSeed(newSeed);
  };

  const handleApprove = () => {
    onApprove();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Skeleton Generation</h2>
      
      {/* Seed Input */}
      <div className="mb-6">
        <label htmlFor="seed" className="block text-sm font-medium text-gray-700 mb-2">
          Random Seed
        </label>
        <div className="flex gap-2">
          <input
            id="seed"
            type="number"
            value={seed}
            onChange={(e) => setSeed(parseInt(e.target.value) || 0)}
            disabled={isGenerating}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Enter seed value"
          />
          <button
            onClick={handleRegenerate}
            disabled={isGenerating}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Generate random seed"
          >
            🎲
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Different seeds produce different skeleton structures
        </p>
      </div>

      {/* Generate Button */}
      <div className="mb-6">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate || isGenerating}
          className="w-full px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isGenerating ? 'Generating Skeleton...' : hasSkeleton ? 'Regenerate Skeleton' : 'Generate Skeleton'}
        </button>
      </div>

      {/* Progress Display */}
      {isProcessing && job?.progress !== undefined && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(job.progress * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${job.progress * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Analyzing mesh topology and predicting bone structure...
          </p>
        </div>
      )}

      {/* Skeleton Preview Status */}
      {hasSkeleton && !isProcessing && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-start gap-3">
            <span className="text-2xl">✅</span>
            <div className="flex-1">
              <h3 className="font-semibold text-green-800">Skeleton Generated</h3>
              <p className="text-sm text-green-700 mt-1">
                Preview the skeleton structure in the 3D viewer. If satisfied, approve to continue to skinning.
              </p>
              {previousSeeds.length > 0 && (
                <p className="text-xs text-green-600 mt-2">
                  Previous seeds used: {previousSeeds.join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Regenerate with Different Seed Option */}
      {hasSkeleton && !isProcessing && (
        <div className="mb-6">
          <button
            onClick={handleRegenerate}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium"
          >
            Try Different Seed
          </button>
        </div>
      )}

      {/* Approve and Continue Button */}
      {hasSkeleton && !isProcessing && (
        <div>
          <button
            onClick={handleApprove}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
          >
            ✓ Approve and Continue to Skinning
          </button>
        </div>
      )}

      {/* Error Display */}
      {job?.status === 'failed' && job?.error_message && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start gap-3">
            <span className="text-2xl">❌</span>
            <div>
              <h3 className="font-semibold text-red-800">Generation Failed</h3>
              <p className="text-sm text-red-700 mt-1">{job.error_message}</p>
              <p className="text-xs text-red-600 mt-2">
                Try regenerating with a different seed or check the model topology.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
