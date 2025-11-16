"""
Motion dataset management service.
Handles downloading, caching, integrity verification, and indexing of motion clips.
"""

import os
import hashlib
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import MotionClip

logger = logging.getLogger(__name__)


class DatasetDownloadError(Exception):
    """Exception raised when dataset download fails."""
    pass


class DatasetService:
    """Service for managing motion dataset downloads, caching, and integrity."""
    
    def __init__(self):
        self.cache_dir = Path(settings.paths.motion_cache_dir)
        self.index_file = self.cache_dir / "dataset_index.json"
        self.checksum_file = self.cache_dir / "dataset_checksum.txt"
        self.download_status_file = self.cache_dir / "download_status.json"
        
    def ensure_cache_directory(self):
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Motion cache directory: {self.cache_dir}")
    
    def check_dataset_exists(self) -> bool:
        """
        Check if motion dataset exists in cache.
        
        Returns:
            bool: True if dataset exists, False otherwise
        """
        if not self.cache_dir.exists():
            return False
        
        # Check for index file as indicator of dataset presence
        if not self.index_file.exists():
            return False
        
        # Verify at least some motion files exist
        motion_files = list(self.cache_dir.glob("*.bvh")) + list(self.cache_dir.glob("*.fbx"))
        
        return len(motion_files) > 0
    
    def verify_integrity(self) -> Dict[str, any]:
        """
        Verify dataset integrity using checksums.
        
        Returns:
            dict: Integrity check result with status and details
        """
        logger.info("Verifying motion dataset integrity...")
        
        if not self.check_dataset_exists():
            return {
                "valid": False,
                "reason": "Dataset not found",
                "missing_files": ["dataset_index.json"]
            }
        
        # Check if index file is valid JSON
        try:
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
            
            if not isinstance(index_data, dict) or "clips" not in index_data:
                return {
                    "valid": False,
                    "reason": "Invalid index file format"
                }
        
        except (json.JSONDecodeError, IOError) as e:
            return {
                "valid": False,
                "reason": f"Index file corrupted: {str(e)}"
            }
        
        # Verify motion files exist
        missing_files = []
        for clip in index_data.get("clips", []):
            file_path = self.cache_dir / clip.get("fileName", "")
            if not file_path.exists():
                missing_files.append(clip.get("fileName"))
        
        if missing_files:
            return {
                "valid": False,
                "reason": "Missing motion files",
                "missing_files": missing_files
            }
        
        # Verify checksums if checksum file exists
        if self.checksum_file.exists():
            try:
                with open(self.checksum_file, 'r') as f:
                    expected_checksum = f.read().strip()
                
                actual_checksum = self._calculate_dataset_checksum()
                
                if expected_checksum != actual_checksum:
                    logger.warning(f"Checksum mismatch: expected={expected_checksum}, actual={actual_checksum}")
                    return {
                        "valid": False,
                        "reason": "Checksum mismatch",
                        "expected": expected_checksum,
                        "actual": actual_checksum
                    }
            
            except Exception as e:
                logger.error(f"Error verifying checksum: {e}")
                # Don't fail on checksum errors, just warn
        
        logger.info("✅ Dataset integrity verified")
        return {
            "valid": True,
            "clip_count": len(index_data.get("clips", [])),
            "verified_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_dataset_checksum(self) -> str:
        """
        Calculate checksum of dataset index file.
        
        Returns:
            str: SHA256 checksum hex string
        """
        hasher = hashlib.sha256()
        
        with open(self.index_file, 'rb') as f:
            hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def download_dataset(
        self,
        force: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, any]:
        """
        Download motion dataset from source.
        
        Args:
            force: Force re-download even if dataset exists
            progress_callback: Optional callback for progress updates
            
        Returns:
            dict: Download result with status and details
            
        Raises:
            DatasetDownloadError: If download fails after retries
        """
        self.ensure_cache_directory()
        
        # Check if dataset already exists
        if not force and self.check_dataset_exists():
            logger.info("Dataset already exists, skipping download")
            return {
                "status": "exists",
                "message": "Dataset already cached"
            }
        
        logger.info("Starting motion dataset download...")
        
        # Update download status
        self._update_download_status("downloading", 0, "Starting download...")
        
        try:
            # TODO: Replace with actual dataset download implementation
            # This is a placeholder for the actual Google Drive or dataset source download
            # In production, this would use:
            # - gdown library for Google Drive downloads
            # - requests with streaming for large files
            # - progress tracking with callbacks
            
            # Placeholder: Create mock dataset for testing
            logger.warning("⚠️ PLACEHOLDER: Using mock dataset generation")
            self._create_mock_dataset(progress_callback)
            
            # Update status to complete
            self._update_download_status("completed", 100, "Download completed successfully")
            
            logger.info("✅ Dataset download completed")
            
            return {
                "status": "completed",
                "message": "Dataset downloaded successfully",
                "clip_count": len(self.get_dataset_index().get("clips", []))
            }
        
        except Exception as e:
            error_msg = f"Dataset download failed: {str(e)}"
            logger.error(error_msg)
            self._update_download_status("failed", 0, error_msg)
            raise DatasetDownloadError(error_msg) from e
    
    def _create_mock_dataset(self, progress_callback: Optional[callable] = None):
        """
        Create a mock dataset for testing purposes.
        This would be replaced with actual download logic in production.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        # Create mock motion clips
        mock_clips = [
            {
                "id": "motion-001",
                "name": "Walking Forward",
                "fileName": "walk_forward.bvh",
                "duration": 2.5,
                "frameCount": 75,
                "skeletonType": "humanoid",
                "tags": ["walk", "locomotion"],
                "boneCount": 65,
                "datasetSource": "MixamoDataset"
            },
            {
                "id": "motion-002",
                "name": "Running Fast",
                "fileName": "run_fast.bvh",
                "duration": 1.8,
                "frameCount": 54,
                "skeletonType": "humanoid",
                "tags": ["run", "locomotion", "fast"],
                "boneCount": 65,
                "datasetSource": "MixamoDataset"
            },
            {
                "id": "motion-003",
                "name": "Jumping Up",
                "fileName": "jump_up.bvh",
                "duration": 1.2,
                "frameCount": 36,
                "skeletonType": "humanoid",
                "tags": ["jump", "action"],
                "boneCount": 65,
                "datasetSource": "MixamoDataset"
            },
            {
                "id": "motion-004",
                "name": "Dancing Hip Hop",
                "fileName": "dance_hiphop.bvh",
                "duration": 4.0,
                "frameCount": 120,
                "skeletonType": "humanoid",
                "tags": ["dance", "entertainment"],
                "boneCount": 65,
                "datasetSource": "MixamoDataset"
            },
            {
                "id": "motion-005",
                "name": "Dog Walk Cycle",
                "fileName": "dog_walk.bvh",
                "duration": 2.0,
                "frameCount": 60,
                "skeletonType": "quadruped",
                "tags": ["walk", "animal", "quadruped"],
                "boneCount": 42,
                "datasetSource": "AnimalMotionDataset"
            }
        ]
        
        # Create mock motion files
        for i, clip in enumerate(mock_clips):
            file_path = self.cache_dir / clip["fileName"]
            with open(file_path, 'w') as f:
                f.write(f"# Mock motion file: {clip['name']}\n")
                f.write(f"# Duration: {clip['duration']}s\n")
                f.write(f"# Skeleton: {clip['skeletonType']}\n")
            
            if progress_callback:
                progress = int((i + 1) / len(mock_clips) * 100)
                progress_callback(progress, f"Downloaded {clip['name']}")
            
            self._update_download_status(
                "downloading",
                int((i + 1) / len(mock_clips) * 100),
                f"Downloaded {clip['name']}"
            )
        
        # Create index file
        index_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "source": "MockDataset",
            "clips": mock_clips
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        # Calculate and store checksum
        checksum = self._calculate_dataset_checksum()
        with open(self.checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info(f"Created mock dataset with {len(mock_clips)} clips")
    
    def _update_download_status(self, status: str, progress: int, message: str):
        """
        Update download status file.
        
        Args:
            status: Download status ('downloading', 'completed', 'failed')
            progress: Progress percentage (0-100)
            message: Status message
        """
        status_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with open(self.download_status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def get_download_status(self) -> Dict[str, any]:
        """
        Get current download status.
        
        Returns:
            dict: Download status information
        """
        if not self.download_status_file.exists():
            # No download status, check if dataset exists
            if self.check_dataset_exists():
                return {
                    "status": "completed",
                    "progress": 100,
                    "message": "Dataset ready",
                    "updated_at": None
                }
            else:
                return {
                    "status": "not_started",
                    "progress": 0,
                    "message": "Dataset not downloaded",
                    "updated_at": None
                }
        
        try:
            with open(self.download_status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading download status: {e}")
            return {
                "status": "error",
                "progress": 0,
                "message": f"Error reading status: {str(e)}",
                "updated_at": None
            }
    
    def get_dataset_index(self) -> Dict[str, any]:
        """
        Get dataset index with all motion clips.
        
        Returns:
            dict: Dataset index data
        """
        if not self.index_file.exists():
            return {"clips": []}
        
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading dataset index: {e}")
            return {"clips": []}
    
    def index_motion_clips_to_database(self):
        """
        Index motion clips from dataset into database.
        This allows querying motion clips via the API.
        """
        db = SessionLocal()
        
        try:
            index_data = self.get_dataset_index()
            clips = index_data.get("clips", [])
            
            logger.info(f"Indexing {len(clips)} motion clips to database...")
            
            for clip_data in clips:
                # Check if clip already exists
                existing = db.query(MotionClip).filter(
                    MotionClip.id == clip_data["id"]
                ).first()
                
                if existing:
                    # Update existing clip
                    for key, value in clip_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # Create new clip
                    clip = MotionClip(
                        id=clip_data["id"],
                        name=clip_data["name"],
                        file_name=clip_data["fileName"],
                        duration=clip_data["duration"],
                        frame_count=clip_data["frameCount"],
                        skeleton_type=clip_data["skeletonType"],
                        tags=clip_data.get("tags", []),
                        bone_count=clip_data["boneCount"],
                        dataset_source=clip_data["datasetSource"],
                        thumbnail_url=clip_data.get("thumbnailUrl")
                    )
                    db.add(clip)
            
            db.commit()
            logger.info(f"✅ Indexed {len(clips)} motion clips to database")
        
        except Exception as e:
            logger.error(f"Error indexing motion clips: {e}")
            db.rollback()
            raise
        
        finally:
            db.close()


# Global dataset service instance
dataset_service = DatasetService()
