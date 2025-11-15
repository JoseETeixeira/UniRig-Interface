import React from 'react';

interface ViewerControlsProps {
  wireframeMode: boolean;
  onWireframeToggle: () => void;
  lightingIntensity: number;
  onLightingChange: (intensity: number) => void;
  backgroundColor: string;
  onBackgroundChange: (color: string) => void;
}

const BACKGROUND_PRESETS = [
  { name: 'Dark Gray', color: '#1f2937' },
  { name: 'Black', color: '#000000' },
  { name: 'White', color: '#ffffff' },
  { name: 'Light Gray', color: '#e5e7eb' },
  { name: 'Blue', color: '#1e40af' },
  { name: 'Purple', color: '#7c3aed' },
];

/**
 * Viewer controls panel for wireframe mode, lighting, and background color
 * 
 * Features:
 * - Wireframe mode toggle
 * - Lighting intensity slider (0.1x - 2.0x)
 * - Background color picker with presets
 * - Collapsible panel design
 */
export const ViewerControls: React.FC<ViewerControlsProps> = ({
  wireframeMode,
  onWireframeToggle,
  lightingIntensity,
  onLightingChange,
  backgroundColor,
  onBackgroundChange,
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="absolute bottom-4 left-4 bg-gray-800 rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-700 transition-colors"
      >
        <span className="text-white text-sm font-medium flex items-center gap-2">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
            />
          </svg>
          Viewer Controls
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Controls Panel */}
      {isExpanded && (
        <div className="p-4 space-y-4 border-t border-gray-700">
          {/* Wireframe Toggle */}
          <div className="space-y-2">
            <label className="text-white text-sm font-medium flex items-center gap-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z"
                />
              </svg>
              Wireframe Mode
            </label>
            <button
              onClick={onWireframeToggle}
              className={`w-full px-3 py-2 rounded text-sm transition-colors duration-200 flex items-center justify-center gap-2 ${
                wireframeMode
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
            >
              {wireframeMode ? 'On' : 'Off'}
            </button>
          </div>

          {/* Lighting Intensity Slider */}
          <div className="space-y-2">
            <label className="text-white text-sm font-medium flex items-center justify-between">
              <span className="flex items-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
                Lighting Intensity
              </span>
              <span className="text-gray-400 text-xs">{lightingIntensity.toFixed(1)}x</span>
            </label>
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-xs">0.1x</span>
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.1"
                value={lightingIntensity}
                onChange={(e) => onLightingChange(parseFloat(e.target.value))}
                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <span className="text-gray-400 text-xs">2.0x</span>
            </div>
          </div>

          {/* Background Color Picker */}
          <div className="space-y-2">
            <label className="text-white text-sm font-medium flex items-center gap-2">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                />
              </svg>
              Background Color
            </label>
            <div className="grid grid-cols-3 gap-2">
              {BACKGROUND_PRESETS.map((preset) => (
                <button
                  key={preset.color}
                  onClick={() => onBackgroundChange(preset.color)}
                  className={`h-10 rounded border-2 transition-all ${
                    backgroundColor === preset.color
                      ? 'border-blue-500 scale-95'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                  style={{ backgroundColor: preset.color }}
                  title={preset.name}
                >
                  {backgroundColor === preset.color && (
                    <svg
                      className="w-4 h-4 mx-auto text-white drop-shadow"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
