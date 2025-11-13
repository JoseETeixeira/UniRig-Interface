"""
Unit tests for FileService - file validation, MIME checking, storage management.
"""

import pytest
from pathlib import Path
from fastapi import UploadFile
from io import BytesIO

from app.services.file_service import FileService
from app.utils.errors import InvalidFormatError, FileSizeExceededError, SecurityError


class TestFileValidation:
    """Test file validation logic."""
    
    def test_validate_valid_obj_file(self, mock_obj_file):
        """Test validation passes for valid OBJ file."""
        with open(mock_obj_file, "rb") as f:
            upload_file = UploadFile(
                filename="test_model.obj",
                file=f
            )
            assert FileService.validate_file(upload_file) is True
    
    def test_validate_invalid_extension(self):
        """Test validation rejects invalid file extensions."""
        content = BytesIO(b"malicious content")
        upload_file = UploadFile(
            filename="malicious.exe",
            file=content
        )
        with pytest.raises(InvalidFormatError) as exc_info:
            FileService.validate_file(upload_file)
        assert "Invalid file format" in str(exc_info.value)
    
    def test_validate_no_extension(self):
        """Test validation rejects files without extension."""
        content = BytesIO(b"some content")
        upload_file = UploadFile(
            filename="noextension",
            file=content
        )
        with pytest.raises(InvalidFormatError):
            FileService.validate_file(upload_file)
    
    def test_validate_case_insensitive_extension(self):
        """Test validation handles uppercase extensions."""
        content = BytesIO(b"v 0 0 0\nf 1 2 3")
        upload_file = UploadFile(
            filename="MODEL.OBJ",
            file=content
        )
        assert FileService.validate_file(upload_file) is True


class TestFileSizeValidation:
    """Test file size validation."""
    
    def test_validate_file_within_size_limit(self, mock_obj_file):
        """Test validation passes for files within size limit."""
        with open(mock_obj_file, "rb") as f:
            upload_file = UploadFile(
                filename="test_model.obj",
                file=f
            )
            assert FileService.validate_file(upload_file) is True
    
    def test_validate_file_exceeds_size_limit(self, mock_large_file):
        """Test validation rejects files exceeding size limit."""
        with open(mock_large_file, "rb") as f:
            upload_file = UploadFile(
                filename="large_file.obj",
                file=f
            )
            with pytest.raises(FileSizeExceededError) as exc_info:
                FileService.validate_file(upload_file)
            assert "exceeds maximum allowed size" in str(exc_info.value)


class TestMIMEValidation:
    """Test MIME type validation."""
    
    def test_validate_mime_type_valid(self, mock_obj_file):
        """Test MIME validation passes for valid content."""
        result = FileService.validate_mime_type(mock_obj_file)
        assert result is True
    
    def test_validate_mime_type_invalid(self, mock_invalid_file):
        """Test MIME validation rejects invalid content."""
        with pytest.raises(SecurityError) as exc_info:
            FileService.validate_mime_type(mock_invalid_file)
        assert "MIME type validation failed" in str(exc_info.value)


class TestMalwareScanning:
    """Test malware detection."""
    
    def test_scan_clean_file(self, mock_obj_file):
        """Test scanning passes for clean files."""
        result = FileService.scan_for_malicious_content(mock_obj_file)
        assert result is True
    
    def test_scan_suspicious_file(self, mock_invalid_file):
        """Test scanning detects suspicious patterns."""
        # The mock file has DOS header which should be flagged
        with pytest.raises(SecurityError):
            FileService.scan_for_malicious_content(mock_invalid_file)


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""
    
    def test_sanitize_filename_safe(self):
        """Test safe filenames pass sanitization."""
        safe_name = "model_v2.obj"
        result = FileService.sanitize_filename(safe_name)
        assert result == safe_name
    
    def test_sanitize_filename_with_path_traversal(self):
        """Test path traversal attempts are blocked."""
        malicious_name = "../../etc/passwd"
        with pytest.raises(SecurityError) as exc_info:
            FileService.sanitize_filename(malicious_name)
        assert "Path traversal" in str(exc_info.value)
    
    def test_sanitize_filename_with_null_bytes(self):
        """Test null byte injection is blocked."""
        malicious_name = "model.obj\x00.exe"
        with pytest.raises(SecurityError):
            FileService.sanitize_filename(malicious_name)


class TestFileStorage:
    """Test file storage operations."""
    
    @pytest.mark.asyncio
    async def test_save_upload_file(self, temp_upload_dir, mock_obj_file):
        """Test file saving creates correct file."""
        session_id = "test-session-123"
        
        with open(mock_obj_file, "rb") as f:
            upload_file = UploadFile(
                filename="test_model.obj",
                file=f
            )
            
            saved_path = await FileService.save_upload_file(
                upload_file,
                session_id,
                temp_upload_dir
            )
        
        assert saved_path.exists()
        assert saved_path.name == "test_model.obj"
        assert session_id in str(saved_path)
    
    @pytest.mark.asyncio
    async def test_save_upload_file_creates_directory(self, temp_upload_dir, mock_obj_file):
        """Test file saving creates session directory if needed."""
        session_id = "new-session-456"
        
        with open(mock_obj_file, "rb") as f:
            upload_file = UploadFile(
                filename="model.obj",
                file=f
            )
            
            saved_path = await FileService.save_upload_file(
                upload_file,
                session_id,
                temp_upload_dir
            )
        
        assert saved_path.parent.exists()
        assert saved_path.exists()


class TestFilePermissions:
    """Test file permission restrictions."""
    
    @pytest.mark.asyncio
    async def test_saved_file_has_restricted_permissions(self, temp_upload_dir, mock_obj_file):
        """Test saved files have chmod 600 (owner read/write only)."""
        session_id = "test-session-789"
        
        with open(mock_obj_file, "rb") as f:
            upload_file = UploadFile(
                filename="secure_model.obj",
                file=f
            )
            
            saved_path = await FileService.save_upload_file(
                upload_file,
                session_id,
                temp_upload_dir
            )
        
        # Check file permissions (0o600 = rw-------)
        import stat
        file_stat = saved_path.stat()
        mode = stat.S_IMODE(file_stat.st_mode)
        assert mode == 0o600
