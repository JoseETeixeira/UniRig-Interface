"""
Health check endpoint.
Provides API health status and system information.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    gpu_available: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns API status and system capabilities.
    
    Returns:
        HealthResponse: Status information
        
    Example:
        GET /api/health
        {
            "status": "healthy",
            "version": "1.0.0",
            "gpu_available": true
        }
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        gpu_available=settings.system.gpu_available
    )
