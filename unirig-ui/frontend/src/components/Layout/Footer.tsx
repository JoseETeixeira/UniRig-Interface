import React from 'react';

/**
 * Application footer with version and links
 */
export const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-600">
            <p>
              <strong>UniRig</strong> - Unified Automatic 3D Model Rigging
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Version 1.0.0 | Powered by deep learning
            </p>
          </div>

          <div className="flex items-center gap-6 text-sm">
            <a
              href="https://github.com/VAST-AI-Research/UniRig"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              <span>📚</span>
              <span>Documentation</span>
            </a>
            <a
              href="https://github.com/VAST-AI-Research/UniRig"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              <span>💻</span>
              <span>GitHub</span>
            </a>
            <a
              href="https://github.com/VAST-AI-Research/UniRig/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1"
            >
              <span>🐛</span>
              <span>Report Issue</span>
            </a>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            © 2025 VAST-AI-Research. Licensed under MIT License.
          </p>
        </div>
      </div>
    </footer>
  );
};
