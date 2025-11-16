"""
Motion Dataset Manager Service

Manages downloading, caching, and integrity validation of the preprocessed motion dataset
for Deep Motion Editing retargeting operations.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
Design: Component 6 - MotionDatasetManager
"""

import os
import hashlib
import time
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MotionDatasetManager:
    """
    Manages the preprocessed motion dataset for motion retargeting.
    
    Responsibilities:
    - Download dataset from Google Drive on first use
    - Verify dataset integrity with checksums
    - Manage cache directory in Docker volume
    - Provide download progress logging
    - Handle download failures with retry logic
    """
    
    def __init__(
        self,
        cache_dir: str = "/app/motion_cache",
        dataset_url: Optional[str] = None,
        expected_checksum: Optional[str] = None,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0
    ):
        """
        Initialize Motion Dataset Manager.
        
        Args:
            cache_dir: Directory for cached dataset (Docker volume)
            dataset_url: Google Drive or direct URL for dataset download
            expected_checksum: SHA256 checksum for integrity verification
            max_retries: Maximum download retry attempts (default: 3)
            retry_backoff_factor: Exponential backoff multiplier (default: 2.0)
        """
        self.cache_dir = Path(cache_dir)
        self.dataset_url = dataset_url
        self.expected_checksum = expected_checksum
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        
        # Dataset file tracking
        self.dataset_archive = self.cache_dir / "motion_dataset.tar.gz"
        self.dataset_extracted_marker = self.cache_dir / ".dataset_extracted"
        self.checksum_file = self.cache_dir / "motion_dataset.sha256"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MotionDatasetManager initialized with cache_dir={cache_dir}")
    
    def is_dataset_cached(self) -> bool:
        """
        Check if dataset is already cached and extracted.
        
        Returns:
            True if dataset exists and is extracted, False otherwise
        """
        # Check for extraction marker and at least one dataset file
        if not self.dataset_extracted_marker.exists():
            return False
        
        # Check if cache directory has content (beyond marker files)
        dataset_files = [
            f for f in self.cache_dir.iterdir()
            if f.is_file() and not f.name.startswith('.')
            and f.name not in ['motion_dataset.tar.gz', 'motion_dataset.sha256']
        ]
        
        has_content = len(dataset_files) > 0 or any(self.cache_dir.iterdir())
        
        if has_content:
            logger.info("Motion dataset found in cache")
        else:
            logger.info("Motion dataset cache is empty")
        
        return has_content
    
    def download_dataset(self) -> bool:
        """
        Download motion dataset from configured URL with retry logic.
        
        Implements:
        - Progress logging
        - Exponential backoff retry (3 attempts)
        - Chunk-based streaming download
        
        Returns:
            True if download successful, False otherwise
        """
        if not self.dataset_url:
            logger.error("Dataset URL not configured. Set MOTION_DATASET_URL environment variable.")
            return False
        
        logger.info(f"Starting dataset download from {self.dataset_url}")
        
        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Download attempt {attempt}/{self.max_retries}")
                
                # Send HEAD request to get file size
                head_response = session.head(self.dataset_url, allow_redirects=True, timeout=30)
                total_size = int(head_response.headers.get('content-length', 0))
                
                if total_size > 0:
                    logger.info(f"Dataset size: {total_size / (1024**3):.2f} GB")
                
                # Stream download with progress logging
                response = session.get(self.dataset_url, stream=True, timeout=60)
                response.raise_for_status()
                
                downloaded_size = 0
                chunk_size = 8192  # 8 KB chunks
                last_log_time = time.time()
                log_interval = 10  # Log progress every 10 seconds
                
                with open(self.dataset_archive, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            # Log progress at intervals
                            current_time = time.time()
                            if current_time - last_log_time >= log_interval:
                                if total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    logger.info(f"Download progress: {progress:.1f}% "
                                              f"({downloaded_size / (1024**2):.1f} MB / "
                                              f"{total_size / (1024**2):.1f} MB)")
                                else:
                                    logger.info(f"Downloaded: {downloaded_size / (1024**2):.1f} MB")
                                last_log_time = current_time
                
                logger.info(f"Dataset download completed: {downloaded_size / (1024**2):.1f} MB")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Download attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    # Calculate backoff delay: backoff_factor * (2 ^ (attempt - 1))
                    delay = self.retry_backoff_factor * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("All download attempts exhausted")
                    return False
            
            except Exception as e:
                logger.error(f"Unexpected error during download: {str(e)}", exc_info=True)
                return False
        
        return False
    
    def verify_checksum(self) -> bool:
        """
        Verify dataset archive integrity using SHA256 checksum.
        
        Returns:
            True if checksum matches or no checksum provided, False otherwise
        """
        if not self.expected_checksum:
            logger.warning("No checksum provided, skipping verification")
            return True
        
        if not self.dataset_archive.exists():
            logger.error("Dataset archive not found for checksum verification")
            return False
        
        logger.info("Verifying dataset checksum...")
        
        try:
            sha256_hash = hashlib.sha256()
            
            with open(self.dataset_archive, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            
            if calculated_checksum == self.expected_checksum:
                logger.info("Checksum verification passed ✓")
                # Save checksum to file
                self.checksum_file.write_text(calculated_checksum)
                return True
            else:
                logger.error(f"Checksum mismatch! Expected: {self.expected_checksum}, "
                           f"Got: {calculated_checksum}")
                return False
                
        except Exception as e:
            logger.error(f"Checksum verification failed: {str(e)}", exc_info=True)
            return False
    
    def extract_dataset(self) -> bool:
        """
        Extract dataset archive to cache directory.
        
        Returns:
            True if extraction successful, False otherwise
        """
        if not self.dataset_archive.exists():
            logger.error("Dataset archive not found for extraction")
            return False
        
        logger.info("Extracting dataset archive...")
        
        try:
            import tarfile
            
            with tarfile.open(self.dataset_archive, 'r:gz') as tar:
                # Extract all files
                tar.extractall(path=self.cache_dir)
            
            # Create extraction marker
            self.dataset_extracted_marker.touch()
            
            logger.info("Dataset extraction completed")
            
            # Optional: Remove archive to save space
            # self.dataset_archive.unlink()
            # logger.info("Archive removed to save disk space")
            
            return True
            
        except Exception as e:
            logger.error(f"Dataset extraction failed: {str(e)}", exc_info=True)
            return False
    
    def ensure_dataset_available(self) -> bool:
        """
        Ensure motion dataset is available in cache.
        
        Main entry point that:
        1. Checks if dataset is already cached
        2. Downloads if not present
        3. Verifies integrity with checksum
        4. Extracts archive
        
        Returns:
            True if dataset is available (cached or downloaded), False otherwise
        """
        # Check if dataset already exists
        if self.is_dataset_cached():
            logger.info("Motion dataset is already available in cache")
            return True
        
        logger.info("Motion dataset not found in cache, starting download...")
        
        # Download dataset
        if not self.download_dataset():
            logger.error("Failed to download motion dataset")
            return False
        
        # Verify checksum
        if not self.verify_checksum():
            logger.error("Dataset checksum verification failed")
            # Clean up corrupted download
            if self.dataset_archive.exists():
                self.dataset_archive.unlink()
            return False
        
        # Extract dataset
        if not self.extract_dataset():
            logger.error("Failed to extract motion dataset")
            return False
        
        logger.info("Motion dataset successfully downloaded and cached")
        return True
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached dataset.
        
        Returns:
            Dictionary with cache status and metadata
        """
        info = {
            "cache_dir": str(self.cache_dir),
            "is_cached": self.is_dataset_cached(),
            "archive_exists": self.dataset_archive.exists(),
            "extracted": self.dataset_extracted_marker.exists(),
        }
        
        # Add file count if cached
        if info["is_cached"]:
            dataset_files = list(self.cache_dir.rglob("*"))
            info["file_count"] = len([f for f in dataset_files if f.is_file()])
            info["total_size_mb"] = sum(
                f.stat().st_size for f in dataset_files if f.is_file()
            ) / (1024**2)
        
        return info
    
    def clear_cache(self) -> bool:
        """
        Clear cached dataset (for maintenance or re-download).
        
        Returns:
            True if cache cleared successfully
        """
        logger.warning("Clearing motion dataset cache...")
        
        try:
            import shutil
            
            # Remove all files in cache directory
            for item in self.cache_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            logger.info("Motion dataset cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}", exc_info=True)
            return False
    
    def index_motion_clips(self, db: Session) -> bool:
        """
        Parse motion dataset files and create database index.
        
        Extracts metadata from motion files (BVH/FBX) and stores in database.
        
        Args:
            db: SQLAlchemy database session
            
        Returns:
            True if indexing successful, False otherwise
        """
        if not self.is_dataset_cached():
            logger.error("Cannot index: dataset not cached")
            return False
        
        logger.info("Starting motion dataset indexing...")
        
        try:
            from app.db.models import MotionClip
            
            # Find all motion files in cache directory
            motion_files = []
            for ext in ['*.bvh', '*.fbx', '*.BVH', '*.FBX']:
                motion_files.extend(self.cache_dir.rglob(ext))
            
            if not motion_files:
                logger.warning("No motion files found in dataset")
                return False
            
            logger.info(f"Found {len(motion_files)} motion files to index")
            
            indexed_count = 0
            for motion_file in motion_files:
                try:
                    # Check if already indexed
                    existing = db.query(MotionClip).filter_by(
                        file_name=motion_file.name
                    ).first()
                    
                    if existing:
                        logger.debug(f"Skipping already indexed: {motion_file.name}")
                        continue
                    
                    # Extract metadata from file
                    metadata = self._extract_motion_metadata(motion_file)
                    
                    if not metadata:
                        logger.warning(f"Could not extract metadata from {motion_file.name}")
                        continue
                    
                    # Create database entry
                    motion_clip = MotionClip(
                        id=str(uuid.uuid4()),
                        name=metadata['name'],
                        file_name=motion_file.name,
                        duration=metadata['duration'],
                        frame_count=metadata['frame_count'],
                        skeleton_type=metadata['skeleton_type'],
                        tags=metadata['tags'],
                        bone_count=metadata['bone_count'],
                        dataset_source=metadata.get('dataset_source', 'default')
                    )
                    
                    db.add(motion_clip)
                    indexed_count += 1
                    
                    if indexed_count % 100 == 0:
                        logger.info(f"Indexed {indexed_count} motion clips...")
                        db.commit()  # Commit in batches
                
                except Exception as e:
                    logger.error(f"Error indexing {motion_file.name}: {e}")
                    continue
            
            # Final commit
            db.commit()
            logger.info(f"✅ Successfully indexed {indexed_count} motion clips")
            return True
            
        except Exception as e:
            logger.error(f"Motion indexing failed: {str(e)}", exc_info=True)
            db.rollback()
            return False
    
    def _extract_motion_metadata(self, motion_file: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from a motion file (BVH or FBX).
        
        Args:
            motion_file: Path to motion file
            
        Returns:
            Dictionary with metadata or None if extraction fails
        """
        try:
            file_ext = motion_file.suffix.lower()
            
            if file_ext == '.bvh':
                return self._extract_bvh_metadata(motion_file)
            elif file_ext == '.fbx':
                return self._extract_fbx_metadata(motion_file)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None
                
        except Exception as e:
            logger.error(f"Metadata extraction failed for {motion_file.name}: {e}")
            return None
    
    def _extract_bvh_metadata(self, bvh_file: Path) -> Dict[str, Any]:
        """
        Extract metadata from BVH motion capture file.
        
        BVH format structure:
        - HIERARCHY section: Defines skeleton structure
        - MOTION section: Contains frame data
        
        Args:
            bvh_file: Path to BVH file
            
        Returns:
            Dictionary with extracted metadata
        """
        try:
            with open(bvh_file, 'r') as f:
                content = f.read()
            
            # Parse BVH structure
            bones = []
            frame_time = 0.033333  # Default 30 FPS
            frame_count = 0
            
            lines = content.split('\n')
            in_hierarchy = False
            in_motion = False
            
            for line in lines:
                line = line.strip()
                
                # Detect sections
                if line.startswith('HIERARCHY'):
                    in_hierarchy = True
                elif line.startswith('MOTION'):
                    in_hierarchy = False
                    in_motion = True
                
                # Parse bone names
                if in_hierarchy and (line.startswith('ROOT') or line.startswith('JOINT')):
                    parts = line.split()
                    if len(parts) >= 2:
                        bones.append(parts[1])
                
                # Parse motion data
                if in_motion:
                    if line.startswith('Frames:'):
                        frame_count = int(line.split(':')[1].strip())
                    elif line.startswith('Frame Time:'):
                        frame_time = float(line.split(':')[1].strip())
            
            # Calculate duration
            duration = frame_count * frame_time
            
            # Detect skeleton type from bone names
            skeleton_type = self._detect_skeleton_type(bones)
            
            # Generate tags from filename and skeleton type
            tags = self._generate_tags(bvh_file.stem, skeleton_type)
            
            # Clean name from filename
            name = self._clean_motion_name(bvh_file.stem)
            
            return {
                'name': name,
                'duration': duration,
                'frame_count': frame_count,
                'skeleton_type': skeleton_type,
                'tags': tags,
                'bone_count': len(bones),
                'dataset_source': 'bvh'
            }
            
        except Exception as e:
            logger.error(f"BVH parsing error for {bvh_file.name}: {e}")
            return None
    
    def _extract_fbx_metadata(self, fbx_file: Path) -> Dict[str, Any]:
        """
        Extract metadata from FBX file.
        
        Note: FBX parsing requires specialized libraries. This is a placeholder
        that returns basic metadata. Full implementation would use FBX SDK or trimesh.
        
        Args:
            fbx_file: Path to FBX file
            
        Returns:
            Dictionary with extracted metadata
        """
        try:
            # Placeholder: FBX metadata extraction
            # In production, use FBX SDK or parse with trimesh/bpy
            
            # For now, use filename heuristics and default values
            name = self._clean_motion_name(fbx_file.stem)
            
            # Estimate based on file size (rough heuristic)
            file_size_kb = fbx_file.stat().st_size / 1024
            estimated_frames = int(file_size_kb / 10)  # Very rough estimate
            frame_rate = 30
            duration = estimated_frames / frame_rate
            
            # Detect from filename
            skeleton_type = self._detect_skeleton_type_from_name(name)
            tags = self._generate_tags(name, skeleton_type)
            
            return {
                'name': name,
                'duration': max(duration, 1.0),  # At least 1 second
                'frame_count': max(estimated_frames, 30),
                'skeleton_type': skeleton_type,
                'tags': tags,
                'bone_count': 65 if skeleton_type == 'humanoid' else 20,
                'dataset_source': 'fbx'
            }
            
        except Exception as e:
            logger.error(f"FBX parsing error for {fbx_file.name}: {e}")
            return None
    
    def _detect_skeleton_type(self, bones: List[str]) -> str:
        """
        Detect skeleton type from bone names.
        
        Args:
            bones: List of bone names
            
        Returns:
            'humanoid', 'quadruped', or 'other'
        """
        bone_names_lower = [b.lower() for b in bones]
        
        # Humanoid indicators
        humanoid_markers = [
            'hips', 'spine', 'head', 'shoulder', 'arm', 'hand', 'leg', 'foot'
        ]
        humanoid_count = sum(
            1 for marker in humanoid_markers
            if any(marker in bone for bone in bone_names_lower)
        )
        
        # Quadruped indicators
        quadruped_markers = [
            'tail', 'paw', 'frontleg', 'hindleg', 'neck'
        ]
        quadruped_count = sum(
            1 for marker in quadruped_markers
            if any(marker in bone for bone in bone_names_lower)
        )
        
        # Determine type
        if humanoid_count >= 4:
            return 'humanoid'
        elif quadruped_count >= 2:
            return 'quadruped'
        else:
            return 'other'
    
    def _detect_skeleton_type_from_name(self, name: str) -> str:
        """
        Detect skeleton type from filename heuristics.
        
        Args:
            name: Motion file name
            
        Returns:
            'humanoid', 'quadruped', or 'other'
        """
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['human', 'person', 'character', 'walk', 'run', 'jump']):
            return 'humanoid'
        elif any(keyword in name_lower for keyword in ['dog', 'cat', 'horse', 'animal', 'quad']):
            return 'quadruped'
        else:
            return 'humanoid'  # Default to humanoid
    
    def _generate_tags(self, filename: str, skeleton_type: str) -> List[str]:
        """
        Generate tags from filename and skeleton type.
        
        Args:
            filename: Motion file name
            skeleton_type: Detected skeleton type
            
        Returns:
            List of tag strings
        """
        tags = [skeleton_type]
        filename_lower = filename.lower()
        
        # Common motion type keywords
        motion_keywords = {
            'walk': 'locomotion',
            'run': 'locomotion',
            'jog': 'locomotion',
            'sprint': 'locomotion',
            'jump': 'aerial',
            'leap': 'aerial',
            'fly': 'aerial',
            'dance': 'performance',
            'wave': 'gesture',
            'point': 'gesture',
            'sit': 'idle',
            'stand': 'idle',
            'idle': 'idle',
            'crouch': 'combat',
            'attack': 'combat',
            'defend': 'combat',
            'climb': 'traversal',
            'crawl': 'traversal'
        }
        
        for keyword, category in motion_keywords.items():
            if keyword in filename_lower:
                tags.append(keyword)
                if category not in tags:
                    tags.append(category)
        
        return tags
    
    def _clean_motion_name(self, filename: str) -> str:
        """
        Clean and format motion name from filename.
        
        Args:
            filename: Original filename (without extension)
            
        Returns:
            Cleaned, human-readable name
        """
        # Remove common prefixes/suffixes
        name = filename.replace('_', ' ').replace('-', ' ')
        
        # Remove numbers at end
        import re
        name = re.sub(r'\d+$', '', name).strip()
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name if name else filename


# Global instance (initialized in backend startup)
motion_dataset_manager: Optional[MotionDatasetManager] = None


def get_motion_dataset_manager() -> Optional[MotionDatasetManager]:
    """Get the global motion dataset manager instance."""
    return motion_dataset_manager


def initialize_motion_dataset_manager(
    cache_dir: str,
    dataset_url: Optional[str],
    expected_checksum: Optional[str] = None
) -> MotionDatasetManager:
    """
    Initialize the global motion dataset manager.
    
    Args:
        cache_dir: Cache directory path
        dataset_url: Dataset download URL
        expected_checksum: Optional SHA256 checksum for verification
        
    Returns:
        Initialized MotionDatasetManager instance
    """
    global motion_dataset_manager
    
    motion_dataset_manager = MotionDatasetManager(
        cache_dir=cache_dir,
        dataset_url=dataset_url,
        expected_checksum=expected_checksum
    )
    
    return motion_dataset_manager
