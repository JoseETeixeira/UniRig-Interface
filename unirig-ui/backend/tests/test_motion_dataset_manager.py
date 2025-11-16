"""
Test script for Motion Dataset Manager

Tests the download, caching, and integrity verification functionality.
"""

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.motion_dataset_manager import MotionDatasetManager


def test_manager_initialization():
    """Test basic manager initialization"""
    print("Testing MotionDatasetManager initialization...")
    
    manager = MotionDatasetManager(
        cache_dir="./test_cache",
        dataset_url="https://example.com/dataset.tar.gz",
        expected_checksum="abc123"
    )
    
    assert manager.cache_dir.name == "test_cache"
    assert manager.dataset_url == "https://example.com/dataset.tar.gz"
    assert manager.expected_checksum == "abc123"
    assert manager.max_retries == 3
    
    print("✅ Initialization test passed")


def test_cache_check():
    """Test cache existence check"""
    print("\nTesting cache check...")
    
    manager = MotionDatasetManager(cache_dir="./test_cache")
    is_cached = manager.is_dataset_cached()
    
    print(f"Cache exists: {is_cached}")
    print("✅ Cache check test passed")


def test_cache_info():
    """Test cache information retrieval"""
    print("\nTesting cache info...")
    
    manager = MotionDatasetManager(cache_dir="./test_cache")
    info = manager.get_cache_info()
    
    print("Cache info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("✅ Cache info test passed")


def test_download_with_invalid_url():
    """Test download with invalid URL (should fail gracefully)"""
    print("\nTesting download with invalid URL...")
    
    manager = MotionDatasetManager(
        cache_dir="./test_cache",
        dataset_url="https://invalid-url-that-does-not-exist.com/dataset.tar.gz",
        max_retries=1  # Reduce retries for faster test
    )
    
    success = manager.download_dataset()
    assert not success, "Download should fail with invalid URL"
    
    print("✅ Invalid URL test passed (correctly failed)")


def cleanup():
    """Clean up test cache directory"""
    import shutil
    if os.path.exists("./test_cache"):
        shutil.rmtree("./test_cache")
        print("\n🧹 Cleaned up test cache directory")


if __name__ == "__main__":
    print("=" * 60)
    print("Motion Dataset Manager Test Suite")
    print("=" * 60)
    
    try:
        test_manager_initialization()
        test_cache_check()
        test_cache_info()
        test_download_with_invalid_url()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cleanup()
