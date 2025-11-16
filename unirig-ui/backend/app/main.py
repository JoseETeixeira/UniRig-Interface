"""
FastAPI application entry point.
Initializes the API server with middleware, routers, and database.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, upload, jobs, download, sessions, csrf, downloads, motion_clips, retargeting, dataset
from app import diagnostics
from app.db.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limiter import rate_limit_middleware
from app.services.motion_dataset_manager import initialize_motion_dataset_manager
from app.services.dataset_service import dataset_service

logger = logging.getLogger(__name__)


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


# Startup event: Initialize database and motion dataset
@app.on_event("startup")
async def startup_event():
    """
    Initialize the database and motion dataset on application startup.
    Creates tables if they don't exist and starts dataset download if needed.
    """
    # Initialize database
    init_db()
    logger.info("✅ Database initialized")
    
    # Initialize dataset service and verify integrity
    try:
        dataset_service.ensure_cache_directory()
        
        # Check if dataset exists
        if dataset_service.check_dataset_exists():
            logger.info("Motion dataset found in cache, verifying integrity...")
            
            # Verify integrity
            integrity_result = dataset_service.verify_integrity()
            
            if integrity_result["valid"]:
                logger.info("✅ Dataset integrity verified")
                
                # Index clips to database if needed
                dataset_service.index_motion_clips_to_database()
            else:
                logger.warning(f"⚠️ Dataset integrity check failed: {integrity_result.get('reason')}")
                logger.info("Attempting to re-download dataset...")
                
                # Re-download on corruption (Requirement 5.6)
                try:
                    result = dataset_service.download_dataset(force=True)
                    if result["status"] == "completed":
                        logger.info("✅ Dataset re-downloaded successfully")
                        dataset_service.index_motion_clips_to_database()
                    else:
                        logger.error("❌ Dataset re-download failed")
                except Exception as e:
                    logger.error(f"❌ Failed to re-download corrupted dataset: {e}")
        else:
            logger.info("Motion dataset not found - will be downloaded on first admin request")
    
    except Exception as e:
        logger.error(f"Error during dataset initialization: {e}")
        logger.warning("Motion retargeting may be unavailable")
    
    # Legacy motion dataset manager initialization (keeping for compatibility)
    # Initialize motion dataset manager
    cache_dir = os.getenv("MOTION_CACHE_DIR", "/app/motion_cache")
    dataset_url = os.getenv("MOTION_DATASET_URL")
    expected_checksum = os.getenv("MOTION_DATASET_CHECKSUM")
    
    if dataset_url:
        logger.info("Initializing motion dataset manager...")
        manager = initialize_motion_dataset_manager(
            cache_dir=cache_dir,
            dataset_url=dataset_url,
            expected_checksum=expected_checksum
        )
        
        # Start dataset download in background if not cached
        # Note: This runs synchronously on startup, which is intentional
        # to ensure dataset is available before processing requests
        try:
            if not manager.is_dataset_cached():
                logger.info("Motion dataset not cached, starting download...")
                success = manager.ensure_dataset_available()
                if success:
                    logger.info("✅ Motion dataset downloaded and cached successfully")
                    
                    # Index motion clips in database
                    logger.info("Building motion clip index...")
                    from app.db.database import SessionLocal
                    db = SessionLocal()
                    try:
                        index_success = manager.index_motion_clips(db)
                        if index_success:
                            logger.info("✅ Motion clip index built successfully")
                        else:
                            logger.warning("⚠️ Motion clip indexing failed")
                    finally:
                        db.close()
                else:
                    logger.warning("⚠️ Motion dataset download failed - retargeting will be unavailable")
            else:
                logger.info("✅ Motion dataset already cached")
                
                # Check if index needs to be built/rebuilt
                from app.db.database import SessionLocal
                from app.db.models import MotionClip
                db = SessionLocal()
                try:
                    clip_count = db.query(MotionClip).count()
                    if clip_count == 0:
                        logger.info("Motion clip index is empty, building index...")
                        index_success = manager.index_motion_clips(db)
                        if index_success:
                            logger.info("✅ Motion clip index built successfully")
                        else:
                            logger.warning("⚠️ Motion clip indexing failed")
                    else:
                        logger.info(f"✅ Motion clip index found ({clip_count} clips)")
                finally:
                    db.close()
        except Exception as e:
            logger.error(f"Error initializing motion dataset: {e}", exc_info=True)
            logger.warning("⚠️ Motion retargeting will be unavailable")
    else:
        logger.info("MOTION_DATASET_URL not configured - motion retargeting disabled")
    
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
app.include_router(csrf.router, prefix="/api", tags=["CSRF"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(download.router, prefix="/api", tags=["Download"])
app.include_router(downloads.router, tags=["Downloads"])
app.include_router(diagnostics.router, prefix="/api", tags=["Diagnostics"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(motion_clips.router, prefix="/api", tags=["Motion Clips"])
app.include_router(retargeting.router, prefix="/api", tags=["Motion Retargeting"])
app.include_router(dataset.router, prefix="/api", tags=["Dataset Management"])


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
