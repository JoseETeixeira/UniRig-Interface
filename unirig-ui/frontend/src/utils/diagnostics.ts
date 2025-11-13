/**
 * Diagnostics and error reporting utilities
 */

export interface DiagnosticInfo {
  timestamp: string;
  userAgent: string;
  viewport: {
    width: number;
    height: number;
  };
  sessionId: string | null;
  errorDetails: {
    code: string;
    message: string;
    stack?: string;
  };
  recentActions: string[];
  systemInfo: {
    platform: string;
    language: string;
    cookiesEnabled: boolean;
    onLine: boolean;
  };
}

/**
 * Collect diagnostic information for error reporting
 */
export function collectDiagnostics(error: any, sessionId: string | null, recentActions: string[] = []): DiagnosticInfo {
  return {
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
    },
    sessionId,
    errorDetails: {
      code: error.code || error.name || 'UNKNOWN',
      message: error.message || String(error),
      stack: error.stack,
    },
    recentActions: recentActions.slice(-10), // Last 10 actions
    systemInfo: {
      platform: navigator.platform,
      language: navigator.language,
      cookiesEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
    },
  };
}

/**
 * Format diagnostics for clipboard or download
 */
export function formatDiagnostics(diagnostics: DiagnosticInfo): string {
  return `UniRig Error Report
Generated: ${diagnostics.timestamp}

Session ID: ${diagnostics.sessionId || 'N/A'}

Error Details:
- Code: ${diagnostics.errorDetails.code}
- Message: ${diagnostics.errorDetails.message}

System Information:
- User Agent: ${diagnostics.userAgent}
- Platform: ${diagnostics.systemInfo.platform}
- Language: ${diagnostics.systemInfo.language}
- Viewport: ${diagnostics.viewport.width}x${diagnostics.viewport.height}
- Online: ${diagnostics.systemInfo.onLine ? 'Yes' : 'No'}

Recent Actions:
${diagnostics.recentActions.map((action, i) => `${i + 1}. ${action}`).join('\n') || 'None recorded'}

Stack Trace:
${diagnostics.errorDetails.stack || 'Not available'}
`;
}

/**
 * Copy diagnostics to clipboard
 */
export async function copyDiagnosticsToClipboard(diagnostics: DiagnosticInfo): Promise<boolean> {
  try {
    const formatted = formatDiagnostics(diagnostics);
    await navigator.clipboard.writeText(formatted);
    return true;
  } catch (error) {
    console.error('Failed to copy diagnostics:', error);
    return false;
  }
}

/**
 * Download diagnostics as a text file
 */
export function downloadDiagnostics(diagnostics: DiagnosticInfo): void {
  const formatted = formatDiagnostics(diagnostics);
  const blob = new Blob([formatted], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `unirig-error-${Date.now()}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Send diagnostics to backend for logging (if endpoint exists)
 */
export async function reportDiagnostics(diagnostics: DiagnosticInfo): Promise<boolean> {
  try {
    const response = await fetch('/api/diagnostics', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(diagnostics),
    });
    return response.ok;
  } catch (error) {
    console.error('Failed to report diagnostics:', error);
    return false;
  }
}
