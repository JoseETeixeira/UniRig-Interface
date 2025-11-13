import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useUpload } from '../../hooks';
import type { UploadResponse } from '../../types';

const ALLOWED_FORMATS = ['.obj', '.fbx', '.glb', '.vrm'];
const MAX_SIZE = 100 * 1024 * 1024; // 100MB

interface UploadZoneProps {
  onUploadComplete?: (response: UploadResponse) => void;
  onUploadError?: (error: string) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onUploadComplete,
  onUploadError,
}) => {
  const { upload, uploading, progress, error } = useUpload();
  const [validationError, setValidationError] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[], rejectedFiles: any[]) => {
      setValidationError(null);

      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors?.[0]?.code === 'file-too-large') {
          setValidationError(
            `File size exceeds 100MB limit. Large files may take longer to process.`
          );
        } else if (rejection.errors?.[0]?.code === 'file-invalid-type') {
          setValidationError(
            `Unsupported file format. Supported formats: ${ALLOWED_FORMATS.join(', ')}`
          );
          if (onUploadError) {
            onUploadError(
              `Unsupported file format. Supported formats: ${ALLOWED_FORMATS.join(', ')}`
            );
          }
          return;
        }
      }

      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];

      // Warning for large files
      if (file.size > MAX_SIZE) {
        const confirmUpload = window.confirm(
          `This file is ${(file.size / 1024 / 1024).toFixed(2)}MB, which exceeds the recommended 100MB limit. Processing may take longer. Continue?`
        );
        if (!confirmUpload) return;
      }

      // Perform upload
      const response = await upload(file);

      if (response && onUploadComplete) {
        onUploadComplete(response);
      } else if (error && onUploadError) {
        onUploadError(error);
      }
    },
    [upload, error, onUploadComplete, onUploadError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'model/gltf-binary': ['.glb'],
      'model/fbx': ['.fbx'],
      'model/obj': ['.obj'],
      'model/vrm': ['.vrm'],
    },
    maxSize: MAX_SIZE * 2, // Allow up to 200MB but show warning
    multiple: false,
    disabled: uploading,
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${
            isDragActive
              ? 'border-blue-500 bg-blue-50 scale-[1.02]'
              : 'border-gray-300 hover:border-gray-400'
          }
          ${uploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />

        {uploading ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <svg
                className="animate-spin h-12 w-12 text-blue-500"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            </div>
            <p className="text-lg font-medium text-gray-700">
              Uploading... {Math.round(progress)}%
            </p>
            <div className="w-full max-w-md mx-auto bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-center">
              <svg
                className="h-16 w-16 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <div>
              <p className="text-lg font-medium text-gray-700">
                {isDragActive
                  ? 'Drop your 3D model here'
                  : 'Drag & drop a 3D model, or click to select'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Supported formats: {ALLOWED_FORMATS.join(', ')}
              </p>
              <p className="text-sm text-gray-500">
                Maximum file size: 100MB (recommended)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error Messages */}
      {(error || validationError) && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <svg
              className="h-5 w-5 text-red-400 mt-0.5 mr-2 flex-shrink-0"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Upload Error
              </h3>
              <p className="text-sm text-red-700 mt-1">
                {error || validationError}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
