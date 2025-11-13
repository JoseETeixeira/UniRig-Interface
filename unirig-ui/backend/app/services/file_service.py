"""
File service for handling file uploads, validation, and storage management.
Manages session-specific file directories and cleanup operations.
"""

import os
import uuid
import shutil
import magic
import subprocess
from pathlib import Path
from typing import Tuple, Set
from fastapi import UploadFile

from app.config import settings
from app.utils.errors import InvalidFormatError, FileSizeExceededError, SecurityError
from app.utils.validation import is_valid_file_extension, get_file_extension


# Constants
ALLOWED_EXTENSIONS = {".obj", ".fbx", ".glb", ".vrm"}
ALLOWED_MIME_TYPES = {
    "model/obj",
    "model/gltf-binary",
    "application/octet-stream",  # FBX files
    "model/vrm",
    "model/gltf+json",
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
CHUNK_SIZE = 8192  # 8KB chunks for async file writing


class FileService:
    """
    Service class for file operations.
    Handles file validation, upload storage, and cleanup.
    """
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """
        Validate uploaded file extension and basic checks.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            True if file is valid
            
        Raises:
            InvalidFormatError: If file extension is not supported
        """
        ext = get_file_extension(file.filename)
        
        if not is_valid_file_extension(file.filename, ALLOWED_EXTENSIONS):
            raise InvalidFormatError(ext)
        
        return True
    
    @staticmethod
    def validate_mime_type(file_path: str) -> bool:
        """
        Validate MIME type of uploaded file using python-magic.
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            True if MIME type is allowed
            
        Raises:
            SecurityError: If MIME type is not allowed or file is executable
        """
        try:
            mime = magic.Magic(mime=True)
            file_mime_type = mime.from_file(file_path)
            
            # Reject executable files
            if 'executable' in file_mime_type or 'script' in file_mime_type:
                raise SecurityError(f"Executable files are not allowed: {file_mime_type}")
            
            # Check against allowed MIME types (relaxed for binary formats)
            # Accept if it's a generic binary or matches known 3D formats
            if file_mime_type not in ALLOWED_MIME_TYPES and not file_mime_type.startswith('application/'):
                raise SecurityError(f"File type not allowed: {file_mime_type}")
            
            return True
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"MIME type validation failed: {str(e)}")
    
    @staticmethod
    def scan_for_malicious_content(file_path: str) -> bool:
        """
        Scan file for malicious content patterns.
        Checks for embedded scripts, null bytes, and suspicious patterns.
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            True if file is safe
            
        Raises:
            SecurityError: If malicious content is detected
        """
        try:
            # Check for null bytes (path traversal attack)
            if '\0' in file_path:
                raise SecurityError("Null byte detected in filename")
            
            # Read first few KB to check for scripts/executables
            with open(file_path, 'rb') as f:
                header = f.read(4096)
                
                # Check for common executable signatures
                executable_signatures = [
                    b'\x7fELF',  # Linux ELF
                    b'MZ',  # Windows PE
                    b'#!',  # Shell script
                    b'<?php',  # PHP script
                    b'<script',  # JavaScript
                ]
                
                for sig in executable_signatures:
                    if sig in header:
                        raise SecurityError(f"Executable signature detected")
            
            return True
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Malicious content scan failed: {str(e)}")
    
    @staticmethod
    async def save_upload(file: UploadFile, session_id: str) -> Tuple[str, str, int]:
        """
        Save uploaded file to session-specific directory with security checks.
        Writes file in 8KB chunks for memory efficiency.
        
        Args:
            file: FastAPI UploadFile object
            session_id: Session identifier for directory isolation
            
        Returns:
            Tuple of (file_path, original_filename, file_size)
            
        Raises:
            SecurityError: If security validation fails
            FileSizeExceededError: If file exceeds size limit
            
        Example:
            file_path, filename, size = await FileService.save_upload(file, session_id)
        """
        # Validate extension first
        FileService.validate_file(file)
        
        # Prevent path traversal in session_id and filename
        safe_session_id = os.path.basename(session_id)
        safe_original_filename = os.path.basename(file.filename)
        
        # Create session-specific upload directory
        upload_dir = Path(settings.paths.upload_dir) / safe_session_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate safe filename with UUID prefix to prevent collisions
        safe_filename = f"{uuid.uuid4()}_{safe_original_filename}"
        file_path = upload_dir / safe_filename
        
        # Write file in chunks (8KB) for async operation
        file_size = 0
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE):
                buffer.write(chunk)
                file_size += len(chunk)
        
        # Validate file size after upload
        if file_size > MAX_FILE_SIZE:
            # Remove the file if it exceeds limit
            os.remove(file_path)
            raise FileSizeExceededError(file_size, MAX_FILE_SIZE)
        
        # Set restrictive file permissions (owner read/write only)
        os.chmod(file_path, 0o600)
        
        # Security validations after file is written
        try:
            FileService.validate_mime_type(str(file_path))
            FileService.scan_for_malicious_content(str(file_path))
        except SecurityError:
            # Remove file if security validation fails
            os.remove(file_path)
            raise
        
        return str(file_path), file.filename, file_size
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Absolute path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return os.path.getsize(file_path)
    
    @staticmethod
    def delete_session_files(session_id: str) -> None:
        """
        Delete all files associated with a session.
        Removes both upload and results directories for the session.
        
        Args:
            session_id: Session identifier
            
        Note:
            This operation is irreversible. Use with caution.
        """
        upload_dir = Path(settings.paths.upload_dir) / session_id
        results_dir = Path(settings.paths.results_dir) / session_id
        
        # Remove upload directory
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        
        # Remove results directory
        if results_dir.exists():
            shutil.rmtree(results_dir)
    
    @staticmethod
    def ensure_results_directory(session_id: str) -> Path:
        """
        Ensure results directory exists for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Path to the results directory
        """
        results_dir = Path(settings.paths.results_dir) / session_id
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
