"""
Disk space monitoring service for triggering emergency cleanup
"""
import os
import shutil
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DiskMonitor:
    """Monitor disk space and trigger alerts"""
    
    # Thresholds in GB
    EMERGENCY_THRESHOLD_GB = 5
    WARNING_THRESHOLD_GB = 10
    
    @staticmethod
    def get_disk_usage(path: str = "/") -> Dict[str, float]:
        """
        Get disk usage statistics for a given path
        
        Returns:
            Dict with total, used, free, and percent values in GB
        """
        try:
            stat = shutil.disk_usage(path)
            return {
                "total_gb": stat.total / (1024 ** 3),
                "used_gb": stat.used / (1024 ** 3),
                "free_gb": stat.free / (1024 ** 3),
                "percent_used": (stat.used / stat.total) * 100
            }
        except Exception as e:
            logger.error(f"Failed to get disk usage for {path}: {e}")
            return {
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percent_used": 0
            }
    
    @classmethod
    def is_low_disk_space(cls, path: str = "/") -> bool:
        """Check if disk space is below emergency threshold"""
        usage = cls.get_disk_usage(path)
        return usage["free_gb"] < cls.EMERGENCY_THRESHOLD_GB
    
    @classmethod
    def needs_warning(cls, path: str = "/") -> bool:
        """Check if disk space is below warning threshold"""
        usage = cls.get_disk_usage(path)
        return usage["free_gb"] < cls.WARNING_THRESHOLD_GB
    
    @classmethod
    def get_directory_size(cls, path: str) -> float:
        """
        Calculate total size of a directory in GB
        
        Args:
            path: Directory path
            
        Returns:
            Size in GB
        """
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total += os.path.getsize(filepath)
        except Exception as e:
            logger.error(f"Failed to calculate directory size for {path}: {e}")
        
        return total / (1024 ** 3)
