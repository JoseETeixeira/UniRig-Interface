import { useState, useCallback } from 'react';
import { uploadFile } from '../services/api';
import { useSession } from './useSession';
import type { UploadResponse } from '../types';

interface UseUploadReturn {
  upload: (file: File) => Promise<UploadResponse | null>;
  uploading: boolean;
  progress: number;
  error: string | null;
}

/**
 * Custom hook for file upload with progress tracking
 */
export const useUpload = (): UseUploadReturn => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useSession();

  const upload = useCallback(
    async (file: File): Promise<UploadResponse | null> => {
      try {
        setUploading(true);
        setProgress(0);
        setError(null);

        const response = await uploadFile(file, sessionId || undefined, (p) => {
          setProgress(p);
        });

        return response;
      } catch (err: any) {
        const errorMessage = err.message || 'Upload failed';
        setError(errorMessage);
        return null;
      } finally {
        setUploading(false);
      }
    },
    [sessionId]
  );

  return {
    upload,
    uploading,
    progress,
    error,
  };
};
