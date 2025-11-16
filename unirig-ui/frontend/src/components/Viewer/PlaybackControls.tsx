import React from 'react';

interface PlaybackControlsProps {
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onSeek: (time: number) => void;
  playbackSpeed?: number;
  onSpeedChange?: (speed: number) => void;
  isLooping?: boolean;
  onLoopToggle?: (loop: boolean) => void;
}

/**
 * Animation playback controls component
 * Provides play/pause/stop buttons, timeline scrubber, speed control, and time/frame display
 */
export const PlaybackControls: React.FC<PlaybackControlsProps> = ({
  isPlaying,
  currentTime,
  duration,
  onPlay,
  onPause,
  onStop,
  onSeek,
  playbackSpeed = 1.0,
  onSpeedChange,
  isLooping = true,
  onLoopToggle,
}) => {
  const handleScrubberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    onSeek(newTime);
  };

  const handleSpeedChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSpeed = parseFloat(e.target.value);
    onSpeedChange?.(newSpeed);
  };

  const handleLoopToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    onLoopToggle?.(e.target.checked);
  };

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate current frame (assuming 30 FPS)
  const currentFrame = Math.floor(currentTime * 30);
  const totalFrames = Math.floor(duration * 30);

  return (
    <div className="flex flex-col gap-3 p-3 bg-gray-800 rounded-lg">
      {/* Control Buttons */}
      <div className="flex items-center gap-2">
        {!isPlaying ? (
          <button
            onClick={onPlay}
            className="flex items-center justify-center w-10 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            title="Play"
            aria-label="Play animation"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
            </svg>
          </button>
        ) : (
          <button
            onClick={onPause}
            className="flex items-center justify-center w-10 h-10 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            title="Pause"
            aria-label="Pause animation"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z" />
            </svg>
          </button>
        )}

        <button
          onClick={onStop}
          className="flex items-center justify-center w-10 h-10 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
          title="Stop"
          aria-label="Stop animation"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M5.25 3A2.25 2.25 0 003 5.25v9.5A2.25 2.25 0 005.25 17h9.5A2.25 2.25 0 0017 14.75v-9.5A2.25 2.25 0 0014.75 3h-9.5z" />
          </svg>
        </button>

        {/* Speed Control */}
        {onSpeedChange && (
          <div className="flex items-center gap-2 ml-2">
            <label htmlFor="speed-select" className="text-xs text-gray-400">
              Speed:
            </label>
            <select
              id="speed-select"
              value={playbackSpeed}
              onChange={handleSpeedChange}
              className="bg-gray-700 text-white text-sm rounded px-2 py-1 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Playback speed"
            >
              <option value="0.25">0.25x</option>
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1.0">1.0x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x</option>
            </select>
          </div>
        )}

        {/* Loop Toggle */}
        {onLoopToggle && (
          <div className="flex items-center gap-2 ml-2">
            <label htmlFor="loop-toggle" className="flex items-center gap-1 text-xs text-gray-400 cursor-pointer">
              <input
                id="loop-toggle"
                type="checkbox"
                checked={isLooping}
                onChange={handleLoopToggle}
                className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
              />
              Loop
            </label>
          </div>
        )}

        {/* Time Display */}
        <div className="flex-1 flex items-center justify-between text-sm text-gray-300 ml-3">
          <span className="font-mono">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
          <span className="font-mono text-gray-400">
            Frame {currentFrame} / {totalFrames}
          </span>
        </div>
      </div>

      {/* Timeline Scrubber */}
      <div className="flex items-center gap-3">
        <input
          type="range"
          min="0"
          max={duration}
          step="0.01"
          value={currentTime}
          onChange={handleScrubberChange}
          className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer 
                     [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 
                     [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full 
                     [&::-webkit-slider-thumb]:bg-blue-500 [&::-webkit-slider-thumb]:cursor-pointer
                     [&::-webkit-slider-thumb]:hover:bg-blue-600
                     [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 
                     [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-blue-500 
                     [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer
                     [&::-moz-range-thumb]:hover:bg-blue-600"
          aria-label="Timeline scrubber"
        />
      </div>
    </div>
  );
};
