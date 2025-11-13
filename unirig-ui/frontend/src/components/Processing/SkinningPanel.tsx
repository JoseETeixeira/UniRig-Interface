import React, { useState } from 'react';
import { Job } from '../../types';

interface SkinningPanelProps {
  job: Job | null;
  skeletonApproved: boolean;
  onGenerateSkinning: (options?: { iterations?: number }) => Promise<void>;
}

export const SkinningPanel: React.FC<SkinningPanelProps> = ({
  job,
  skeletonApproved,
  onGenerateSkinning
}) => {
  const [iterations, setIterations] = useState<number>(5);
  const [isGenerating, setIsGenerating] = useState(false);

  const hasSkinning = job?.results?.skin_file;
  const isProcessing = job?.status === 'processing' && job?.stage === 'skinning_generation';
  const canGenerate = skeletonApproved && !isProcessing;

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await onGenerateSkinning({ iterations });
    } catch (error) {
      console.error('Failed to generate skinning:', error);
      setIsGenerating(false);
    }
  };

  if (!skeletonApproved) {
    return (
      <div className="bg-gray-50 rounded-lg shadow-md p-6 border-2 border-dashed border-gray-300">
        <h2 className="text-2xl font-bold mb-4 text-gray-500">Skinning Generation</h2>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <span className="text-4xl mb-4 block">🔒</span>
            <p className="text-gray-600">
              Approve the skeleton in the previous step to unlock skinning generation
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Skinning Generation</h2>

      {/* Quality Options */}
      <div className="mb-6">
        <label htmlFor="iterations" className="block text-sm font-medium text-gray-700 mb-2">
          Quality / Iterations
        </label>
        <select
          id="iterations"
          value={iterations}
          onChange={(e) => setIterations(parseInt(e.target.value))}
          disabled={isGenerating || isProcessing}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          <option value={3}>Fast (3 iterations)</option>
          <option value={5}>Balanced (5 iterations)</option>
          <option value={10}>High Quality (10 iterations)</option>
          <option value={15}>Maximum Quality (15 iterations)</option>
        </select>
        <p className="text-xs text-gray-500 mt-1">
          Higher iterations produce smoother deformations but take longer to process
        </p>
      </div>

      {/* Generate Button */}
      <div className="mb-6">
        <button
          onClick={handleGenerate}
          disabled={!canGenerate || isGenerating}
          className="w-full px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isGenerating ? 'Generating Skinning...' : hasSkinning ? 'Regenerate Skinning' : 'Generate Skinning'}
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
              className="bg-purple-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${job.progress * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Computing skinning weights and binding mesh to skeleton...
          </p>
        </div>
      )}

      {/* Skinning Complete Status */}
      {hasSkinning && !isProcessing && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-start gap-3">
            <span className="text-2xl">✅</span>
            <div className="flex-1">
              <h3 className="font-semibold text-green-800">Skinning Generated</h3>
              <p className="text-sm text-green-700 mt-1">
                Preview the rigged model with animation controls. The model is now ready for export.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Preview Controls Info */}
      {hasSkinning && !isProcessing && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
          <h3 className="font-semibold text-blue-800 mb-2">Preview Tips</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Use animation controls to test deformation quality</li>
            <li>• Select bones to view weight influence heatmap</li>
            <li>• Check for proper mesh deformation in problem areas</li>
            <li>• Regenerate with different iteration count if needed</li>
          </ul>
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
                Try adjusting the iteration count or regenerate the skeleton with a different seed.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
