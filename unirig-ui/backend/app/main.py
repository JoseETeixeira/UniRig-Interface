"""
FastAPI application entry point.
Initializes the API server with middleware, routers, and database.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, upload, jobs, download, sessions
from app import diagnostics
from app.db.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limiter import rate_limit_middleware


# Create FastAPI application
app = FastAPI(
    title="UniRig UI API",
    description="REST API for UniRig automatic 3D model rigging",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add security middleware (order matters - added in reverse order of execution)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.middleware("http")(rate_limit_middleware)

# CORS configuration for frontend (React on localhost:3000)
# Note: CORS should be after security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"],  # Expose CSRF token header to frontend
)


# Startup event: Initialize database
@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on application startup.
    Creates tables if they don't exist.
    """
    init_db()
    print("✅ FastAPI application started successfully")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown.
    """
    print("🛑 FastAPI application shutting down")


# Include API routers with /api prefix
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(download.router, prefix="/api", tags=["Download"])
app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "UniRig UI API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }
