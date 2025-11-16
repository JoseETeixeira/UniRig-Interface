/**
 * Error Boundary for ModelViewer component
 * Catches and handles React errors gracefully with user-friendly feedback
 */

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  modelUrl?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error categories with user-friendly messages and troubleshooting steps
 */
const ERROR_CATEGORIES = {
  WEBGL_NOT_SUPPORTED: {
    title: 'WebGL Not Supported',
    message: 'Your browser does not support WebGL, which is required for 3D visualization.',
    suggestions: [
      'Try updating your browser to the latest version',
      'Enable hardware acceleration in your browser settings',
      'Try a different browser (Chrome, Firefox, or Edge recommended)',
      'Check if your graphics drivers are up to date',
    ],
    icon: '🖥️',
  },
  MODEL_LOAD_FAILED: {
    title: 'Failed to Load Model',
    message: 'The 3D model could not be loaded. This may be due to a corrupted file or network issue.',
    suggestions: [
      'Check your internet connection',
      'Try refreshing the page',
      'Re-upload the model if the issue persists',
      'Verify the file format is supported (FBX or GLB)',
    ],
    icon: '📦',
  },
  MEMORY_ERROR: {
    title: 'Memory Limit Exceeded',
    message: 'The model is too large to render in your browser.',
    suggestions: [
      'Try closing other browser tabs to free up memory',
      'Use the "Load Simplified" option for large models',
      'Download the model and view it in a desktop 3D application',
    ],
    icon: '💾',
  },
  RENDERING_ERROR: {
    title: 'Rendering Error',
    message: 'An error occurred while rendering the 3D scene.',
    suggestions: [
      'Try refreshing the page',
      'Clear your browser cache',
      'Check if your graphics drivers are up to date',
      'Try using a different browser',
    ],
    icon: '⚠️',
  },
  UNKNOWN_ERROR: {
    title: 'Unexpected Error',
    message: 'An unexpected error occurred while displaying the 3D model.',
    suggestions: [
      'Try refreshing the page',
      'Check your internet connection',
      'If the problem persists, please contact support',
    ],
    icon: '❌',
  },
};

/**
 * Categorize error based on error message and stack
 */
function categorizeError(error: Error): keyof typeof ERROR_CATEGORIES {
  const errorMessage = error.message.toLowerCase();
  const errorStack = error.stack?.toLowerCase() || '';

  if (
    errorMessage.includes('webgl') ||
    errorMessage.includes('context') ||
    errorStack.includes('webgl')
  ) {
    return 'WEBGL_NOT_SUPPORTED';
  }

  if (
    errorMessage.includes('load') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('network') ||
    errorMessage.includes('404') ||
    errorMessage.includes('parse')
  ) {
    return 'MODEL_LOAD_FAILED';
  }

  if (
    errorMessage.includes('memory') ||
    errorMessage.includes('heap') ||
    errorMessage.includes('out of memory')
  ) {
    return 'MEMORY_ERROR';
  }

  if (
    errorMessage.includes('render') ||
    errorMessage.includes('shader') ||
    errorMessage.includes('texture')
  ) {
    return 'RENDERING_ERROR';
  }

  return 'UNKNOWN_ERROR';
}

/**
 * ErrorBoundary component for ModelViewer
 * Provides graceful error handling with user-friendly messages
 */
export class ViewerErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console (can be extended to send to monitoring service)
    console.error('ModelViewer Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Component Stack:', errorInfo.componentStack);

    // TODO: Send to monitoring service (e.g., Sentry, LogRocket)
    // Example: logErrorToService(error, errorInfo);

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Get error category and details
      const errorCategory = categorizeError(this.state.error);
      const errorDetails = ERROR_CATEGORIES[errorCategory];

      return (
        <div className="w-full h-full min-h-[500px] bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center p-6">
          <div className="max-w-2xl text-center">
            {/* Error Icon */}
            <div className="text-6xl mb-4">{errorDetails.icon}</div>

            {/* Error Title */}
            <h2 className="text-2xl font-bold text-red-400 mb-3">
              {errorDetails.title}
            </h2>

            {/* Error Message */}
            <p className="text-gray-300 mb-6 text-base">
              {errorDetails.message}
            </p>

            {/* Troubleshooting Suggestions */}
            <div className="bg-gray-800 rounded-lg p-5 mb-6 text-left">
              <h3 className="text-sm font-semibold text-gray-400 mb-3 uppercase">
                Troubleshooting Steps
              </h3>
              <ul className="space-y-2">
                {errorDetails.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start space-x-2 text-sm text-gray-300">
                    <span className="text-blue-400 mt-0.5">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-center space-x-3">
              <button
                onClick={this.handleReset}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
              >
                Try Again
              </button>

              {this.props.modelUrl && (
                <a
                  href={this.props.modelUrl}
                  download
                  className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
                >
                  Download Model
                </a>
              )}
            </div>

            {/* Technical Details (Collapsible) */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-6 text-left">
                <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-400">
                  Technical Details
                </summary>
                <div className="mt-3 p-4 bg-gray-800 rounded text-xs text-gray-400 font-mono overflow-auto max-h-40">
                  <p className="mb-2">
                    <strong>Error:</strong> {this.state.error.message}
                  </p>
                  {this.state.error.stack && (
                    <pre className="whitespace-pre-wrap break-all">
                      {this.state.error.stack}
                    </pre>
                  )}
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
