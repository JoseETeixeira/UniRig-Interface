import React, { useState } from 'react';
import { Button } from './Button';
import { ParsedError } from '../../utils/errorHandlers';
import { collectDiagnostics, copyDiagnosticsToClipboard, downloadDiagnostics } from '../../utils/diagnostics';

interface ErrorDisplayProps {
  error: ParsedError;
  sessionId: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

/**
 * Display error with troubleshooting and diagnostic tools
 */
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  sessionId,
  onRetry,
  onDismiss,
  className = '',
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const getSeverityStyles = () => {
    switch (error.severity) {
      case 'error':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          icon: 'text-red-500',
          text: 'text-red-800',
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          icon: 'text-yellow-500',
          text: 'text-yellow-800',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          icon: 'text-blue-500',
          text: 'text-blue-800',
        };
    }
  };

  const styles = getSeverityStyles();

  const handleCopyError = async () => {
    const diagnostics = collectDiagnostics(
      { code: error.errorCode, message: error.technicalMessage },
      sessionId
    );
    const success = await copyDiagnosticsToClipboard(diagnostics);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadError = () => {
    const diagnostics = collectDiagnostics(
      { code: error.errorCode, message: error.technicalMessage },
      sessionId
    );
    downloadDiagnostics(diagnostics);
  };

  return (
    <div className={`${styles.bg} ${styles.border} border-l-4 rounded-lg p-4 ${className}`}>
      <div className="flex items-start gap-3">
        {/* Error Icon */}
        <div className={`${styles.icon} flex-shrink-0 mt-1`}>
          {error.severity === 'error' && (
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          )}
          {error.severity === 'warning' && (
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          )}
          {error.severity === 'info' && (
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </div>

        {/* Error Content */}
        <div className="flex-1 min-w-0">
          <h3 className={`${styles.text} font-semibold text-sm mb-2`}>
            {error.userMessage}
          </h3>

          {/* Troubleshooting Tips */}
          <div className={`${styles.text} text-sm mb-3`}>
            <p className="font-medium mb-1">How to fix this:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              {error.troubleshooting.map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>

          {/* Documentation Link */}
          {error.documentationUrl && (
            <a
              href={error.documentationUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`${styles.text} text-sm underline hover:no-underline inline-flex items-center gap-1 mb-3`}
            >
              <span>📚</span>
              <span>View documentation</span>
            </a>
          )}

          {/* Technical Details (Expandable) */}
          <div className="mb-3">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className={`${styles.text} text-sm font-medium underline hover:no-underline`}
            >
              {showDetails ? '▼' : '▶'} Technical details
            </button>
            {showDetails && (
              <div className="mt-2 p-3 bg-white bg-opacity-50 rounded border border-gray-300">
                <p className="text-xs font-mono text-gray-700 break-all">
                  <strong>Error Code:</strong> {error.errorCode}
                </p>
                <p className="text-xs font-mono text-gray-700 break-all mt-1">
                  <strong>Message:</strong> {error.technicalMessage}
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {onRetry && (
              <Button variant="primary" size="sm" onClick={onRetry}>
                Try Again
              </Button>
            )}
            {onDismiss && (
              <Button variant="secondary" size="sm" onClick={onDismiss}>
                Dismiss
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCopyError}
              className="text-xs"
            >
              {copied ? '✓ Copied' : '📋 Copy Error Details'}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownloadError}
              className="text-xs"
            >
              💾 Download Report
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
