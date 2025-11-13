"""
Diagnostics and error reporting endpoint
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ErrorDetails(BaseModel):
    code: str
    message: str
    stack: Optional[str] = None


class SystemInfo(BaseModel):
    platform: str
    language: str
    cookiesEnabled: bool
    onLine: bool


class Viewport(BaseModel):
    width: int
    height: int


class DiagnosticReport(BaseModel):
    timestamp: str
    userAgent: str
    viewport: Viewport
    sessionId: Optional[str]
    errorDetails: ErrorDetails
    recentActions: List[str]
    systemInfo: SystemInfo


@router.post('/diagnostics')
async def report_diagnostics(report: DiagnosticReport):
    """
    Receive and log diagnostic information from frontend
    
    Saves error reports to disk for debugging and analysis.
    """
    try:
        # Log to console
        logger.error('Frontend error report received:')
        logger.error(f"Session: {report.sessionId or 'N/A'}")
        logger.error(f"Error Code: {report.errorDetails.code}")
        logger.error(f"Error Message: {report.errorDetails.message}")
        logger.error(f"User Agent: {report.userAgent}")
        logger.error(f"Recent Actions: {report.recentActions}")
        
        # Save to diagnostics log file if configured
        log_dir = os.environ.get('DIAGNOSTICS_LOG_DIR', '/tmp/unirig-diagnostics')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = report.sessionId or 'unknown'
        log_file = os.path.join(log_dir, f'error_{timestamp}_{session_id}.txt')
        
        with open(log_file, 'w') as f:
            f.write('UniRig Error Report\n')
            f.write('=' * 80 + '\n\n')
            f.write(f"Timestamp: {report.timestamp}\n")
            f.write(f"Session ID: {session_id}\n\n")
            
            f.write('Error Details:\n')
            f.write('-' * 80 + '\n')
            f.write(f"Code: {report.errorDetails.code}\n")
            f.write(f"Message: {report.errorDetails.message}\n")
            if report.errorDetails.stack:
                f.write(f"\nStack Trace:\n{report.errorDetails.stack}\n")
            
            f.write('\nSystem Information:\n')
            f.write('-' * 80 + '\n')
            f.write(f"User Agent: {report.userAgent}\n")
            f.write(f"Platform: {report.systemInfo.platform}\n")
            f.write(f"Language: {report.systemInfo.language}\n")
            f.write(f"Cookies Enabled: {report.systemInfo.cookiesEnabled}\n")
            f.write(f"Online: {report.systemInfo.onLine}\n")
            f.write(f"Viewport: {report.viewport.width}x{report.viewport.height}\n")
            
            f.write('\nRecent Actions:\n')
            f.write('-' * 80 + '\n')
            if report.recentActions:
                for i, action in enumerate(report.recentActions, 1):
                    f.write(f"{i}. {action}\n")
            else:
                f.write('None recorded\n')
        
        logger.info(f'Diagnostics saved to: {log_file}')
        
        return {
            'success': True,
            'message': 'Diagnostics received',
            'log_file': log_file
        }
        
    except Exception as e:
        logger.error(f'Failed to process diagnostics: {str(e)}')
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Failed to process diagnostics',
                'details': str(e)
            }
        )
