"""
API routers for UniRig UI backend.
Contains all REST API endpoint implementations.
"""

from app.api import health, upload, jobs, download

__all__ = ["health", "upload", "jobs", "download"]
