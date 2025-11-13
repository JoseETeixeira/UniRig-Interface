"""
Celery tasks for model checkpoint download and verification
"""
import os
import hashlib
import requests
from pathlib import Path
from celery import shared_task
from celery.utils.log import get_task_logger
from typing import Optional, Tuple

logger = get_task_logger(__name__)


@shared_task(name="tasks.download_model_checkpoint", bind=True, max_retries=3)
def download_model_checkpoint(
    self,
    url: str,
    destination: str,
    expected_checksum: Optional[str] = None,
    checksum_algorithm: str = "sha256"
):
    """
    Download a model checkpoint with retry logic and checksum verification
    
    Args:
        url: URL to download from
        destination: Local file path to save to
        expected_checksum: Expected checksum (hex string)
        checksum_algorithm: Hash algorithm ('sha256', 'md5', etc.)
        
    Returns:
        Dictionary with download results
    """
    logger.info(f"Downloading model checkpoint from {url}")
    logger.info(f"Destination: {destination}")
    
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download with progress logging
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 50MB
                    if downloaded % (50 * 1024 * 1024) == 0:
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download completed: {downloaded / (1024**2):.2f}MB")
        
        # Verify checksum if provided
        if expected_checksum:
            logger.info(f"Verifying checksum ({checksum_algorithm})")
            computed_checksum = compute_file_checksum(destination, checksum_algorithm)
            
            if computed_checksum.lower() != expected_checksum.lower():
                error_msg = f"Checksum mismatch! Expected {expected_checksum}, got {computed_checksum}"
                logger.error(error_msg)
                # Delete corrupted file
                os.remove(destination)
                raise ValueError(error_msg)
            
            logger.info("Checksum verification passed")
        
        return {
            "success": True,
            "destination": destination,
            "size_mb": downloaded / (1024**2),
            "checksum": computed_checksum if expected_checksum else None
        }
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        
        # Retry with exponential backoff (2^retry_count seconds)
        try:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1}/3)")
            self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for download")
            return {
                "success": False,
                "error": f"Max retries exceeded: {str(e)}"
            }


def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute checksum of a file
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm ('sha256', 'md5', etc.)
        
    Returns:
        Hex string of checksum
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


@shared_task(name="tasks.verify_model_checkpoint")
def verify_model_checkpoint(filepath: str, expected_checksum: str, algorithm: str = "sha256"):
    """
    Verify an existing model checkpoint
    
    Args:
        filepath: Path to model file
        expected_checksum: Expected checksum (hex string)
        algorithm: Hash algorithm
        
    Returns:
        Dictionary with verification results
    """
    logger.info(f"Verifying model checkpoint: {filepath}")
    
    try:
        if not os.path.exists(filepath):
            return {
                "success": False,
                "error": "File does not exist"
            }
        
        computed = compute_file_checksum(filepath, algorithm)
        matches = computed.lower() == expected_checksum.lower()
        
        if matches:
            logger.info("Checksum verification passed")
        else:
            logger.error(f"Checksum mismatch! Expected {expected_checksum}, got {computed}")
        
        return {
            "success": matches,
            "computed_checksum": computed,
            "expected_checksum": expected_checksum,
            "filepath": filepath
        }
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
