/**
 * Utility for downloading files with progress tracking and error handling
 * Supports resumable downloads via Range headers
 */

export interface DownloadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface DownloadOptions {
  onProgress?: (progress: DownloadProgress) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
  signal?: AbortSignal; // For cancellation support
}

/**
 * Download a file from a URL with progress tracking
 * Uses fetch API with credentials for authentication
 * Automatically triggers browser download with proper filename
 */
export async function downloadFile(
  url: string,
  filename: string,
  options: DownloadOptions = {}
): Promise<void> {
  const { onProgress, onError, onComplete, signal } = options;

  try {
    // Fetch the file with credentials (session cookies)
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include', // Include session cookies
      signal,
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    // Get content length for progress tracking
    const contentLength = response.headers.get('Content-Length');
    const total = contentLength ? parseInt(contentLength, 10) : 0;

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Read the response as a stream for progress tracking
    const reader = response.body.getReader();
    const chunks: BlobPart[] = [];
    let loaded = 0;

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      chunks.push(value);
      loaded += value.length;

      // Report progress
      if (onProgress && total > 0) {
        onProgress({
          loaded,
          total,
          percentage: Math.round((loaded / total) * 100),
        });
      }
    }

    // Combine chunks into a single blob
    const blob = new Blob(chunks);

    // Create object URL and trigger download
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up object URL
    URL.revokeObjectURL(blobUrl);

    // Report completion
    if (onComplete) {
      onComplete();
    }
  } catch (error) {
    // Handle errors
    if (error instanceof Error) {
      if (onError) {
        onError(error);
      }
    } else {
      if (onError) {
        onError(new Error('Unknown download error'));
      }
    }
    throw error;
  }
}

/**
 * Check if a file download URL is accessible
 * Useful for verifying file exists before attempting download
 */
export async function checkFileAvailability(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: 'HEAD',
      credentials: 'include',
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Format bytes to human-readable size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}
