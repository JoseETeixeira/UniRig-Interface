import React, { useState, useEffect, useMemo } from 'react';
import { getMotionClips } from '../../services/api';
import { MotionClip } from '../../types';
import { MotionClipCard } from './MotionClipCard';

interface MotionClipsBrowserProps {
  onSelectClip?: (clip: MotionClip) => void;
  selectedClipId?: string;
}

/**
 * Motion clips browser component.
 * Displays available motion clips from the dataset with filtering and search.
 */
export const MotionClipsBrowser: React.FC<MotionClipsBrowserProps> = ({
  onSelectClip,
  selectedClipId,
}) => {
  const [clips, setClips] = useState<MotionClip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [skeletonTypeFilter, setSkeletonTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // View mode
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Fetch motion clips on mount
  useEffect(() => {
    fetchMotionClips();
  }, []);

  const fetchMotionClips = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await getMotionClips({
        limit: 100, // Fetch up to 100 clips
      });
      
      setClips(response.clips);
    } catch (err) {
      console.error('Failed to fetch motion clips:', err);
      setError('Failed to load motion clips. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Filter and search clips
  const filteredClips = useMemo(() => {
    let result = clips;

    // Filter by skeleton type
    if (skeletonTypeFilter !== 'all') {
      result = result.filter((clip) => clip.skeletonType === skeletonTypeFilter);
    }

    // Search by name or tags
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter((clip) => {
        const nameMatch = clip.name.toLowerCase().includes(query);
        const tagsMatch = clip.tags.some((tag) =>
          tag.toLowerCase().includes(query)
        );
        return nameMatch || tagsMatch;
      });
    }

    return result;
  }, [clips, skeletonTypeFilter, searchQuery]);

  const handleSelectClip = (clip: MotionClip) => {
    if (onSelectClip) {
      onSelectClip(clip);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600">Loading motion clips...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <svg
          className="w-16 h-16 text-red-500 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchMotionClips}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  // Empty state
  if (clips.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <svg
          className="w-16 h-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <p className="text-gray-600 mb-2">No motion clips available</p>
        <p className="text-sm text-gray-500">
          The motion dataset has not been downloaded yet.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with filters */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Motion Clips</h2>
          
          {/* View mode toggle */}
          <div className="flex gap-1 bg-gray-100 p-1 rounded">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              aria-label="Grid view"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              aria-label="List view"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex gap-4">
          {/* Search input */}
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search by name or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Skeleton type filter */}
          <select
            value={skeletonTypeFilter}
            onChange={(e) => setSkeletonTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Types</option>
            <option value="humanoid">Humanoid</option>
            <option value="quadruped">Quadruped</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Results count */}
        <p className="text-sm text-gray-600">
          Showing {filteredClips.length} of {clips.length} clips
        </p>
      </div>

      {/* Clips display */}
      {filteredClips.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <svg
            className="w-12 h-12 text-gray-400 mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="text-gray-600">No clips match your filters</p>
          <button
            onClick={() => {
              setSkeletonTypeFilter('all');
              setSearchQuery('');
            }}
            className="mt-3 text-blue-500 hover:text-blue-600"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
              : 'space-y-2'
          }
        >
          {filteredClips.map((clip) => (
            <MotionClipCard
              key={clip.id}
              clip={clip}
              onSelect={handleSelectClip}
              selected={selectedClipId === clip.id}
            />
          ))}
        </div>
      )}
    </div>
  );
};
