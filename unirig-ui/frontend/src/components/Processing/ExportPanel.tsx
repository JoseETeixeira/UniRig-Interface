import React, { useState } from 'react';
import { Job } from '../../types';

interface ExportPanelProps {
  job: Job | null;
  onExport: (format: 'fbx' | 'glb') => Promise<void>;
  onDownload: (jobId: string, format: string) => Promise<void>;
}

export const ExportPanel: React.FC<ExportPanelProps> = ({
  job,
  onExport,
  onDownload
}) => {
  const [selectedFormat, setSelectedFormat] = useState<'fbx' | 'glb'>('glb');
  const [isExporting, setIsExporting] = useState(false);
  const [downloadTracked, setDownloadTracked] = useState(false);

  const hasFinalFile = job?.results?.final_file;
  const isMerging = job?.status === 'processing' && job?.stage === 'merge';
  const hasSkinning = job?.results?.skin_file;
  const canExport = hasSkinning && !isMerging;

  const handleExport = async () => {
    setIsExporting(true);
    setDownloadTracked(false);
    try {
      await onExport(selectedFormat);
    } catch (error) {
      console.error('Failed to export:', error);
      setIsExporting(false);
    }
  };

  const handleDownload = async () => {
    if (!job?.job_id || !hasFinalFile) return;
    
    try {
      await onDownload(job.job_id, selectedFormat);
      setDownloadTracked(true);
    } catch (error) {
      console.error('Failed to download:', error);
    }
  };

  if (!hasSkinning) {
    return (
      <div className="bg-gray-50 rounded-lg shadow-md p-6 border-2 border-dashed border-gray-300">
        <h2 className="text-2xl font-bold mb-4 text-gray-500">Export Rigged Model</h2>
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <span className="text-4xl mb-4 block">🔒</span>
            <p className="text-gray-600">
              Complete skinning generation to unlock export functionality
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Export Rigged Model</h2>

      {/* Format Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Export Format
        </label>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setSelectedFormat('glb')}
            disabled={isExporting || isMerging}
            className={`
              p-4 border-2 rounded-lg transition-all
              ${selectedFormat === 'glb' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${(isExporting || isMerging) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-2">📦</div>
            <div className="font-semibold">GLB</div>
            <div className="text-xs text-gray-600 mt-1">
              Binary glTF - Best for web and real-time apps
            </div>
          </button>

          <button
            onClick={() => setSelectedFormat('fbx')}
            disabled={isExporting || isMerging}
            className={`
              p-4 border-2 rounded-lg transition-all
              ${selectedFormat === 'fbx' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${(isExporting || isMerging) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="text-2xl mb-2">🎬</div>
            <div className="font-semibold">FBX</div>
            <div className="text-xs text-gray-600 mt-1">
              Autodesk format - Compatible with most 3D software
            </div>
          </button>
        </div>
      </div>

      {/* Export Button */}
      {!hasFinalFile && (
        <div className="mb-6">
          <button
            onClick={handleExport}
            disabled={!canExport || isExporting}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {isExporting ? 'Preparing Export...' : `Export as ${selectedFormat.toUpperCase()}`}
          </button>
        </div>
      )}

      {/* Merge Progress */}
      {isMerging && job?.progress !== undefined && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Merging and Exporting</span>
            <span>{Math.round(job.progress * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-green-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${job.progress * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Merging skeleton and skinning data with original mesh...
          </p>
        </div>
      )}

      {/* Download Section */}
      {hasFinalFile && !isMerging && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-start gap-3 mb-4">
            <span className="text-2xl">✅</span>
            <div className="flex-1">
              <h3 className="font-semibold text-green-800">Export Ready</h3>
              <p className="text-sm text-green-700 mt-1">
                Your rigged model is ready to download in {selectedFormat.toUpperCase()} format.
              </p>
            </div>
          </div>
          
          <button
            onClick={handleDownload}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium flex items-center justify-center gap-2"
          >
            <span>⬇️</span>
            <span>Download {selectedFormat.toUpperCase()}</span>
          </button>

          {downloadTracked && (
            <p className="text-xs text-green-600 mt-2 text-center">
              Download started! Check your downloads folder.
            </p>
          )}
        </div>
      )}

      {/* File Info */}
      {hasFinalFile && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
          <h3 className="font-semibold text-gray-800 mb-2">Export Details</h3>
          <div className="text-sm text-gray-600 space-y-1">
            <div className="flex justify-between">
              <span>Original File:</span>
              <span className="font-mono text-xs">{job?.filename}</span>
            </div>
            <div className="flex justify-between">
              <span>Format:</span>
              <span className="font-semibold">{selectedFormat.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-green-600 font-semibold">✓ Complete</span>
            </div>
          </div>
        </div>
      )}

      {/* Batch Export Hint */}
      {hasFinalFile && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-xs text-blue-700">
            💡 <strong>Tip:</strong> Need both formats? Change the format selection above and export again.
          </p>
        </div>
      )}

      {/* Error Display */}
      {job?.status === 'failed' && job?.error_message && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start gap-3">
            <span className="text-2xl">❌</span>
            <div>
              <h3 className="font-semibold text-red-800">Export Failed</h3>
              <p className="text-sm text-red-700 mt-1">{job.error_message}</p>
              <p className="text-xs text-red-600 mt-2">
                Check that all previous steps completed successfully and try exporting again.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
