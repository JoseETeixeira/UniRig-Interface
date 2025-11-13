/**
 * Error handling utilities for user-friendly error messages and troubleshooting
 */

export interface ErrorDetails {
  code: string;
  message: string;
  details?: string;
  suggestion?: string;
  documentation?: string;
  timestamp?: string;
}

export interface ParsedError {
  userMessage: string;
  technicalMessage: string;
  troubleshooting: string[];
  documentationUrl?: string;
  errorCode: string;
  severity: 'error' | 'warning' | 'info';
}

/**
 * Error code categories and their user-friendly messages
 */
const ERROR_MESSAGES: Record<string, { message: string; troubleshooting: string[]; docs?: string }> = {
  // Upload errors
  'INVALID_FILE_FORMAT': {
    message: 'This file format is not supported',
    troubleshooting: [
      'Supported formats are: .obj, .fbx, .glb, .vrm',
      'Convert your file using Blender or another 3D tool',
      'Make sure the file extension is correct',
    ],
    docs: 'https://github.com/VAST-AI-Research/UniRig#supported-formats',
  },
  'FILE_TOO_LARGE': {
    message: 'The file is too large to process',
    troubleshooting: [
      'Maximum file size is 100MB',
      'Try reducing polygon count in your 3D editor',
      'Compress textures or remove them before upload',
      'Split large models into smaller parts',
    ],
  },
  'UPLOAD_FAILED': {
    message: 'Failed to upload the file',
    troubleshooting: [
      'Check your internet connection',
      'Try uploading again',
      'If the problem persists, try a different browser',
      'Clear your browser cache and cookies',
    ],
  },

  // Processing errors
  'INVALID_MESH_TOPOLOGY': {
    message: 'The model has invalid geometry',
    troubleshooting: [
      'Mesh must be a single closed surface (watertight)',
      'Remove duplicate vertices in your 3D editor',
      'Fix non-manifold edges and holes',
      'Ensure all faces have correct normals',
      'Try using Blender\'s "Clean Up" mesh tools',
    ],
    docs: 'https://github.com/VAST-AI-Research/UniRig#mesh-requirements',
  },
  'SKELETON_GENERATION_FAILED': {
    message: 'Failed to generate skeleton',
    troubleshooting: [
      'Try using a different random seed',
      'Check that your model has clear limb structure',
      'Simplify the model if it\'s too complex',
      'Ensure the model is in a T-pose or A-pose',
    ],
  },
  'SKINNING_GENERATION_FAILED': {
    message: 'Failed to generate skinning weights',
    troubleshooting: [
      'Make sure the skeleton was approved',
      'Try regenerating the skeleton with a different seed',
      'Reduce the iteration count and try again',
      'Check that the mesh has good topology',
    ],
  },
  'GPU_OUT_OF_MEMORY': {
    message: 'Not enough GPU memory to process this model',
    troubleshooting: [
      'Try a simpler model with fewer polygons',
      'Close other GPU-intensive applications',
      'Restart the server to free up memory',
      'Contact administrator for GPU upgrade',
    ],
  },
  'PROCESSING_TIMEOUT': {
    message: 'Processing took too long and was cancelled',
    troubleshooting: [
      'The model may be too complex',
      'Try simplifying the geometry',
      'Contact administrator to increase timeout limit',
    ],
  },

  // Export errors
  'MERGE_FAILED': {
    message: 'Failed to merge skeleton and skinning',
    troubleshooting: [
      'Make sure both skeleton and skinning completed',
      'Try regenerating the skinning weights',
      'Check that the original model file still exists',
    ],
  },
  'EXPORT_FAILED': {
    message: 'Failed to export the rigged model',
    troubleshooting: [
      'Try a different export format (FBX or GLB)',
      'Make sure there\'s enough disk space',
      'Check the browser console for details',
    ],
  },

  // Network errors
  'NETWORK_ERROR': {
    message: 'Network connection error',
    troubleshooting: [
      'Check your internet connection',
      'The server may be temporarily unavailable',
      'Try again in a few moments',
      'Contact administrator if the issue persists',
    ],
  },
  'SERVER_ERROR': {
    message: 'Server encountered an error',
    troubleshooting: [
      'This is likely a temporary issue',
      'Try again in a few moments',
      'If the problem persists, report it to the administrator',
      'Check the server logs for more details',
    ],
  },

  // Session errors
  'SESSION_EXPIRED': {
    message: 'Your session has expired',
    troubleshooting: [
      'Sessions expire after 24 hours of inactivity',
      'Refresh the page to start a new session',
      'Your uploaded files may have been deleted',
    ],
  },
  'UNAUTHORIZED': {
    message: 'Access denied',
    troubleshooting: [
      'Your session may have expired',
      'Refresh the page and try again',
      'Contact administrator if you need access',
    ],
  },

  // Job errors
  'JOB_NOT_FOUND': {
    message: 'Job not found',
    troubleshooting: [
      'The job may have been deleted',
      'Your session may have expired',
      'Refresh the page to see current jobs',
    ],
  },
  'JOB_CANCELLED': {
    message: 'Job was cancelled',
    troubleshooting: [
      'You or another user cancelled this job',
      'Start a new job by uploading another model',
    ],
  },

  // CUDA/GPU errors
  'CUDA_ERROR': {
    message: 'GPU processing error',
    troubleshooting: [
      'The GPU may be unavailable or overloaded',
      'Check CUDA installation with nvidia-smi',
      'Restart the server to reset GPU state',
      'Contact administrator for GPU diagnostics',
    ],
    docs: 'https://github.com/VAST-AI-Research/UniRig#gpu-requirements',
  },

  // Generic fallback
  'UNKNOWN_ERROR': {
    message: 'An unexpected error occurred',
    troubleshooting: [
      'Try refreshing the page',
      'Check the browser console for details',
      'Report this error if it persists',
    ],
  },
};

/**
 * Parse an error object into user-friendly format
 */
export function parseError(error: any): ParsedError {
  // Handle API error responses
  if (error.response?.data?.error) {
    const apiError = error.response.data.error;
    const errorCode = apiError.code || 'UNKNOWN_ERROR';
    const errorInfo = ERROR_MESSAGES[errorCode] || ERROR_MESSAGES['UNKNOWN_ERROR'];

    return {
      userMessage: errorInfo.message,
      technicalMessage: apiError.message || error.message,
      troubleshooting: errorInfo.troubleshooting,
      documentationUrl: errorInfo.docs,
      errorCode,
      severity: getSeverity(errorCode),
    };
  }

  // Handle network errors
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    const errorInfo = ERROR_MESSAGES['PROCESSING_TIMEOUT'];
    return {
      userMessage: errorInfo.message,
      technicalMessage: error.message,
      troubleshooting: errorInfo.troubleshooting,
      errorCode: 'PROCESSING_TIMEOUT',
      severity: 'warning',
    };
  }

  if (error.code === 'ERR_NETWORK' || !error.response) {
    const errorInfo = ERROR_MESSAGES['NETWORK_ERROR'];
    return {
      userMessage: errorInfo.message,
      technicalMessage: error.message,
      troubleshooting: errorInfo.troubleshooting,
      errorCode: 'NETWORK_ERROR',
      severity: 'error',
    };
  }

  // Handle HTTP status codes
  if (error.response?.status) {
    const status = error.response.status;
    if (status === 401 || status === 403) {
      const errorInfo = ERROR_MESSAGES['UNAUTHORIZED'];
      return {
        userMessage: errorInfo.message,
        technicalMessage: `HTTP ${status}`,
        troubleshooting: errorInfo.troubleshooting,
        errorCode: 'UNAUTHORIZED',
        severity: 'warning',
      };
    }
    if (status >= 500) {
      const errorInfo = ERROR_MESSAGES['SERVER_ERROR'];
      return {
        userMessage: errorInfo.message,
        technicalMessage: `HTTP ${status}`,
        troubleshooting: errorInfo.troubleshooting,
        errorCode: 'SERVER_ERROR',
        severity: 'error',
      };
    }
  }

  // Fallback to unknown error
  const errorInfo = ERROR_MESSAGES['UNKNOWN_ERROR'];
  return {
    userMessage: errorInfo.message,
    technicalMessage: error.message || 'No error details available',
    troubleshooting: errorInfo.troubleshooting,
    errorCode: 'UNKNOWN_ERROR',
    severity: 'error',
  };
}

/**
 * Determine error severity based on error code
 */
function getSeverity(errorCode: string): 'error' | 'warning' | 'info' {
  const warnings = ['SESSION_EXPIRED', 'JOB_CANCELLED', 'PROCESSING_TIMEOUT'];
  const info: string[] = [];

  if (warnings.includes(errorCode)) return 'warning';
  if (info.includes(errorCode)) return 'info';
  return 'error';
}

/**
 * Format error for display
 */
export function formatErrorMessage(error: ParsedError): string {
  return `${error.userMessage}\n\nTroubleshooting:\n${error.troubleshooting.map((tip, i) => `${i + 1}. ${tip}`).join('\n')}`;
}

/**
 * Get a short error summary for notifications
 */
export function getErrorSummary(error: ParsedError): string {
  return `${error.userMessage}. ${error.troubleshooting[0] || 'Please try again.'}`;
}
