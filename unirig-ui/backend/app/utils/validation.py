"""
Validation utilities for file uploads and data validation.
Provides helper functions for validating file formats, sizes, and content.
"""

from pathlib import Path
from typing import Set


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Lowercase file extension including the dot (e.g., ".obj", ".fbx")
        
    Example:
        >>> get_file_extension("model.glb")
        ".glb"
        >>> get_file_extension("character.FBX")
        ".fbx"
    """
    return Path(filename).suffix.lower()


def is_valid_file_extension(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Check if file extension is in the allowed set.
    
    Args:
        filename: Name of the file to validate
        allowed_extensions: Set of allowed extensions (e.g., {".obj", ".fbx"})
        
    Returns:
        True if extension is valid, False otherwise
        
    Example:
        >>> allowed = {".obj", ".fbx", ".glb", ".vrm"}
        >>> is_valid_file_extension("model.glb", allowed)
        True
        >>> is_valid_file_extension("texture.png", allowed)
        False
    """
    ext = get_file_extension(filename)
    return ext in allowed_extensions


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Check if file size is within allowed limit.
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if file size is valid, False otherwise
        
    Example:
        >>> max_100mb = 100 * 1024 * 1024
        >>> validate_file_size(50 * 1024 * 1024, max_100mb)
        True
        >>> validate_file_size(150 * 1024 * 1024, max_100mb)
        False
    """
    return file_size <= max_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "2.5 MB", "1.2 GB")
        
    Example:
        >>> format_file_size(1024)
        "1.0 KB"
        >>> format_file_size(2 * 1024 * 1024)
        "2.0 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing potentially dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem operations
        
    Example:
        >>> sanitize_filename("my/../model.obj")
        "my__model.obj"
        >>> sanitize_filename("file:with:colons.fbx")
        "file_with_colons.fbx"
    """
    # Replace dangerous characters with underscores
    dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Ensure we still have a filename
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized


def is_safe_path(base_dir: str, target_path: str) -> bool:
    """
    Check if target_path is safely contained within base_dir.
    Prevents path traversal attacks.
    
    Args:
        base_dir: Base directory path
        target_path: Target file path to validate
        
    Returns:
        True if path is safe, False otherwise
        
    Example:
        >>> is_safe_path("/uploads/session1", "/uploads/session1/model.obj")
        True
        >>> is_safe_path("/uploads/session1", "/etc/passwd")
        False
    """
    try:
        base = Path(base_dir).resolve()
        target = Path(target_path).resolve()
        
        # Check if target is relative to base
        target.relative_to(base)
        return True
    except (ValueError, RuntimeError):
        return False
