import React from 'react';
import type { JobStage } from '../../types';

interface JobProgressProps {
  progress: number;
  stage?: JobStage | null;
}

/**
 * Progress bar component for job processing
 */
export const JobProgress: React.FC<JobProgressProps> = ({ progress, stage }) => {
  const getProgressColor = () => {
    if (progress < 30) return 'bg-blue-400';
    if (progress < 70) return 'bg-blue-500';
    return 'bg-blue-600';
  };

  const formatProgress = () => {
    return `${Math.round(progress * 100)}%`;
  };

  return (
    <div className="space-y-1">
      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`absolute top-0 left-0 h-full transition-all duration-300 ease-out rounded-full ${getProgressColor()}`}
          style={{ width: `${progress * 100}%` }}
        />
      </div>

      {/* Progress Text */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>{formatProgress()}</span>
        {stage && (
          <span className="text-gray-500">
            {stage === 'skeleton_generation' && 'Skeleton'}
            {stage === 'skinning_generation' && 'Skinning'}
            {stage === 'merge' && 'Merging'}
            {stage === 'upload' && 'Uploading'}
          </span>
        )}
      </div>
    </div>
  );
};
