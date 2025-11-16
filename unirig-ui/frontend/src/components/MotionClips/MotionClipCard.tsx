import React from 'react';
import { MotionClip } from '../../types';

interface MotionClipCardProps {
  clip: MotionClip;
  onSelect?: (clip: MotionClip) => void;
  selected?: boolean;
}

/**
 * Motion clip card component displaying clip metadata.
 * Shows thumbnail, name, duration, skeleton type, and tags.
 */
export const MotionClipCard: React.FC<MotionClipCardProps> = ({
  clip,
  onSelect,
  selected = false,
}) => {
  const handleClick = () => {
    if (onSelect) {
      onSelect(clip);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const getSkeletonTypeColor = (type: string): string => {
    switch (type) {
      case 'humanoid':
        return 'bg-blue-100 text-blue-800';
      case 'quadruped':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div
      className={`
        relative rounded-lg border-2 transition-all duration-200 cursor-pointer
        hover:shadow-lg hover:scale-105
        ${selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}
      `}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
      aria-label={`Select motion clip: ${clip.name}`}
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-t-lg overflow-hidden">
        {clip.thumbnailUrl ? (
          <img
            src={clip.thumbnailUrl}
            alt={clip.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg
              className="w-12 h-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
        )}
        
        {/* Selected indicator */}
        {selected && (
          <div className="absolute top-2 right-2 bg-blue-500 text-white rounded-full p-1">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Name */}
        <h3 className="font-semibold text-gray-900 mb-2 truncate" title={clip.name}>
          {clip.name}
        </h3>

        {/* Metadata */}
        <div className="flex items-center gap-2 mb-3 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            {formatDuration(clip.duration)}
          </span>
          <span className="text-gray-300">•</span>
          <span>{clip.frameCount} frames</span>
        </div>

        {/* Skeleton type badge */}
        <div className="mb-3">
          <span
            className={`inline-block px-2 py-1 text-xs font-medium rounded ${getSkeletonTypeColor(
              clip.skeletonType
            )}`}
          >
            {clip.skeletonType}
          </span>
        </div>

        {/* Tags */}
        {clip.tags && clip.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {clip.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
              >
                {tag}
              </span>
            ))}
            {clip.tags.length > 3 && (
              <span className="inline-block px-2 py-0.5 text-xs text-gray-500">
                +{clip.tags.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
