"""
Unit tests for skeleton extraction utility.
Tests skeleton extraction, BVH export, caching, and error handling.
"""

import pytest
import tempfile
import json
from pathlib import Path
import numpy as np

from app.utils.skeleton_extractor import SkeletonExtractor


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def skeleton_extractor(temp_cache_dir):
    """Create skeleton extractor with temporary cache."""
    return SkeletonExtractor(cache_dir=temp_cache_dir)


@pytest.fixture
def mock_skeleton_data():
    """Create mock skeleton data for testing."""
    return {
        "bones": [
            {
                "name": "Hips",
                "transform": np.eye(4).tolist(),
                "position": [0, 0, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            },
            {
                "name": "Spine",
                "transform": np.eye(4).tolist(),
                "position": [0, 1, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            },
            {
                "name": "LeftShoulder",
                "transform": np.eye(4).tolist(),
                "position": [-0.5, 1.5, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            },
            {
                "name": "RightShoulder",
                "transform": np.eye(4).tolist(),
                "position": [0.5, 1.5, 0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1]
            }
        ],
        "hierarchy": {
            "Spine": "Hips",
            "LeftShoulder": "Spine",
            "RightShoulder": "Spine"
        },
        "bone_count": 4,
        "skeleton_type": "humanoid",
        "root_bones": ["Hips"]
    }


class TestSkeletonExtractorInitialization:
    """Test skeleton extractor initialization."""
    
    def test_initialization_default_cache(self):
        """Test initialization with default cache directory."""
        extractor = SkeletonExtractor()
        assert extractor.cache_dir == Path("/app/skeleton_cache")
    
    def test_initialization_custom_cache(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        extractor = SkeletonExtractor(cache_dir=temp_cache_dir)
        assert str(extractor.cache_dir) == temp_cache_dir
        assert extractor.cache_dir.exists()


class TestSkeletonExtraction:
    """Test skeleton extraction functionality."""
    
    def test_extract_nonexistent_file(self, skeleton_extractor):
        """Test extraction with nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            skeleton_extractor.extract_skeleton("/nonexistent/model.fbx")
    
    def test_extract_unsupported_format(self, skeleton_extractor, tmp_path):
        """Test extraction with unsupported format raises ValueError."""
        unsupported_file = tmp_path / "model.obj"
        unsupported_file.write_text("mock content")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            skeleton_extractor.extract_skeleton(str(unsupported_file))
    
    def test_extract_supported_formats(self, skeleton_extractor):
        """Test that FBX and GLB formats are recognized."""
        # These will fail at loading stage, but should pass format check
        with tempfile.NamedTemporaryFile(suffix=".fbx") as f:
            with pytest.raises(RuntimeError, match="Skeleton extraction failed"):
                skeleton_extractor.extract_skeleton(f.name)
        
        with tempfile.NamedTemporaryFile(suffix=".glb") as f:
            with pytest.raises(RuntimeError, match="Skeleton extraction failed"):
                skeleton_extractor.extract_skeleton(f.name)


class TestBoneDetection:
    """Test bone detection and classification."""
    
    def test_is_bone_node_positive(self, skeleton_extractor):
        """Test bone node detection with valid bone names."""
        assert skeleton_extractor._is_bone_node("Hips")
        assert skeleton_extractor._is_bone_node("LeftArm")
        assert skeleton_extractor._is_bone_node("RightLeg")
        assert skeleton_extractor._is_bone_node("Spine1")
        assert skeleton_extractor._is_bone_node("joint_shoulder")
    
    def test_is_bone_node_negative(self, skeleton_extractor):
        """Test bone node detection with non-bone names."""
        assert not skeleton_extractor._is_bone_node("Mesh")
        assert not skeleton_extractor._is_bone_node("Camera")
        assert not skeleton_extractor._is_bone_node("Light")
        assert not skeleton_extractor._is_bone_node("Material")
    
    def test_detect_humanoid_skeleton(self, skeleton_extractor):
        """Test humanoid skeleton detection."""
        bones = [
            {"name": "Hips"},
            {"name": "Spine"},
            {"name": "LeftShoulder"},
            {"name": "RightShoulder"},
            {"name": "LeftArm"},
            {"name": "RightLeg"}
        ]
        assert skeleton_extractor._detect_skeleton_type(bones) == "humanoid"
    
    def test_detect_quadruped_skeleton(self, skeleton_extractor):
        """Test quadruped skeleton detection."""
        bones = [
            {"name": "Root"},
            {"name": "Tail"},
            {"name": "FrontLeftPaw"},
            {"name": "HindRightLeg"}
        ]
        assert skeleton_extractor._detect_skeleton_type(bones) == "quadruped"
    
    def test_detect_other_skeleton(self, skeleton_extractor):
        """Test detection of unclassified skeleton."""
        bones = [
            {"name": "Node1"},
            {"name": "Node2"},
            {"name": "Mechanism"}
        ]
        assert skeleton_extractor._detect_skeleton_type(bones) == "other"


class TestHierarchy:
    """Test hierarchy processing."""
    
    def test_find_root_bones(self, skeleton_extractor):
        """Test finding root bones in hierarchy."""
        hierarchy = {
            "Child1": "Parent",
            "Child2": "Parent",
            "GrandChild": "Child1"
        }
        roots = skeleton_extractor._find_root_bones(hierarchy)
        assert "Parent" in roots
        assert len(roots) == 1
    
    def test_find_multiple_roots(self, skeleton_extractor):
        """Test finding multiple root bones."""
        hierarchy = {
            "Child1": "Root1",
            "Child2": "Root2"
        }
        roots = skeleton_extractor._find_root_bones(hierarchy)
        assert "Root1" in roots
        assert "Root2" in roots
        assert len(roots) == 2


class TestTransformExtraction:
    """Test transform matrix extraction."""
    
    def test_extract_position(self, skeleton_extractor):
        """Test position extraction from transform matrix."""
        transform = np.eye(4)
        transform[:3, 3] = [1.0, 2.0, 3.0]
        position = skeleton_extractor._extract_position(transform)
        assert position == [1.0, 2.0, 3.0]
    
    def test_extract_position_invalid(self, skeleton_extractor):
        """Test position extraction with invalid transform."""
        position = skeleton_extractor._extract_position("invalid")
        assert position == [0, 0, 0]
    
    def test_extract_scale(self, skeleton_extractor):
        """Test scale extraction from transform matrix."""
        transform = np.eye(4)
        transform[:3, 0] *= 2.0  # scale X
        transform[:3, 1] *= 3.0  # scale Y
        transform[:3, 2] *= 4.0  # scale Z
        scale = skeleton_extractor._extract_scale(transform)
        assert scale == pytest.approx([2.0, 3.0, 4.0])
    
    def test_extract_rotation(self, skeleton_extractor):
        """Test rotation extraction from transform matrix."""
        transform = np.eye(4)
        rotation = skeleton_extractor._extract_rotation(transform)
        assert len(rotation) == 4  # quaternion
        assert rotation == [0, 0, 0, 1]  # identity


class TestBVHExport:
    """Test BVH format export."""
    
    def test_export_to_bvh(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test exporting skeleton to BVH format."""
        output_file = tmp_path / "skeleton.bvh"
        result_path = skeleton_extractor.export_to_bvh(
            mock_skeleton_data,
            str(output_file)
        )
        
        assert Path(result_path).exists()
        assert output_file.exists()
        
        # Verify BVH content structure
        content = output_file.read_text()
        assert "HIERARCHY" in content
        assert "ROOT Hips" in content
        assert "JOINT Spine" in content
        assert "MOTION" in content
        assert "Frames:" in content
        assert "Frame Time:" in content
    
    def test_bvh_hierarchy_structure(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test BVH hierarchy contains correct bones."""
        output_file = tmp_path / "skeleton.bvh"
        skeleton_extractor.export_to_bvh(mock_skeleton_data, str(output_file))
        
        content = output_file.read_text()
        assert "Hips" in content
        assert "Spine" in content
        assert "LeftShoulder" in content
        assert "RightShoulder" in content
    
    def test_bvh_channels(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test BVH contains proper channel definitions."""
        output_file = tmp_path / "skeleton.bvh"
        skeleton_extractor.export_to_bvh(mock_skeleton_data, str(output_file))
        
        content = output_file.read_text()
        # Root should have 6 channels (position + rotation)
        assert "CHANNELS 6" in content
        # Joints should have 3 channels (rotation only)
        assert "CHANNELS 3" in content


class TestCaching:
    """Test skeleton caching functionality."""
    
    def test_cache_key_generation(self, skeleton_extractor, tmp_path):
        """Test cache key generation is consistent."""
        test_file = tmp_path / "model.fbx"
        test_file.write_text("mock content")
        
        key1 = skeleton_extractor._get_cache_key(test_file)
        key2 = skeleton_extractor._get_cache_key(test_file)
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
    
    def test_cache_key_changes_on_modification(self, skeleton_extractor, tmp_path):
        """Test cache key changes when file is modified."""
        import time
        
        test_file = tmp_path / "model.fbx"
        test_file.write_text("mock content")
        key1 = skeleton_extractor._get_cache_key(test_file)
        
        time.sleep(0.1)  # Ensure different mtime
        test_file.write_text("modified content")
        key2 = skeleton_extractor._get_cache_key(test_file)
        
        assert key1 != key2
    
    def test_save_and_load_cache(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test saving and loading skeleton from cache."""
        test_file = tmp_path / "model.fbx"
        test_file.write_text("mock content")
        
        # Save to cache
        skeleton_extractor._save_to_cache(test_file, mock_skeleton_data)
        
        # Load from cache
        loaded_data = skeleton_extractor._load_from_cache(test_file)
        
        assert loaded_data is not None
        assert loaded_data["bone_count"] == mock_skeleton_data["bone_count"]
        assert loaded_data["skeleton_type"] == mock_skeleton_data["skeleton_type"]
    
    def test_cache_miss(self, skeleton_extractor, tmp_path):
        """Test cache miss returns None."""
        test_file = tmp_path / "nonexistent.fbx"
        test_file.write_text("mock")
        
        loaded_data = skeleton_extractor._load_from_cache(test_file)
        assert loaded_data is None
    
    def test_clear_cache(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test clearing all cached skeletons."""
        test_file = tmp_path / "model.fbx"
        test_file.write_text("mock content")
        
        # Save to cache
        skeleton_extractor._save_to_cache(test_file, mock_skeleton_data)
        assert skeleton_extractor._load_from_cache(test_file) is not None
        
        # Clear cache
        skeleton_extractor.clear_cache()
        
        # Verify cache is empty
        assert skeleton_extractor._load_from_cache(test_file) is None
    
    def test_get_cache_info(self, skeleton_extractor, mock_skeleton_data, tmp_path):
        """Test getting cache statistics."""
        test_file = tmp_path / "model.fbx"
        test_file.write_text("mock content")
        
        # Initially empty
        info = skeleton_extractor.get_cache_info()
        assert info["cached_skeletons"] == 0
        
        # Add cached skeleton
        skeleton_extractor._save_to_cache(test_file, mock_skeleton_data)
        
        # Check updated info
        info = skeleton_extractor.get_cache_info()
        assert info["cached_skeletons"] == 1
        assert info["total_size_bytes"] > 0
        assert "cache_dir" in info


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_bone_list(self, skeleton_extractor):
        """Test handling of skeleton with no bones."""
        skeleton_data = {
            "bones": [],
            "hierarchy": {},
            "bone_count": 0,
            "skeleton_type": "other",
            "root_bones": []
        }
        
        # Should not raise exception
        skeleton_type = skeleton_extractor._detect_skeleton_type([])
        assert skeleton_type == "other"
    
    def test_malformed_hierarchy(self, skeleton_extractor):
        """Test handling of malformed hierarchy data."""
        # Circular reference
        hierarchy = {
            "A": "B",
            "B": "A"
        }
        
        # Should not crash
        roots = skeleton_extractor._find_root_bones(hierarchy)
        assert isinstance(roots, list)
