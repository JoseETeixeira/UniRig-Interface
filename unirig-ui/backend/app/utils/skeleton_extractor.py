"""
Skeleton extraction utility for rigged 3D models.
Extracts bone hierarchy and transformations from FBX/GLB files for motion retargeting.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import trimesh
import numpy as np

logger = logging.getLogger(__name__)


class SkeletonExtractor:
    """
    Extracts skeleton information from rigged 3D models.
    Supports FBX and GLB formats, with caching for performance.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize skeleton extractor.
        
        Args:
            cache_dir: Directory for caching extracted skeletons. 
                      If None, uses /app/skeleton_cache
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("/app/skeleton_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SkeletonExtractor initialized with cache dir: {self.cache_dir}")
    
    def extract_skeleton(self, model_path: str, use_cache: bool = True) -> Dict:
        """
        Extract skeleton from a rigged 3D model.
        
        Args:
            model_path: Path to FBX or GLB file
            use_cache: Whether to use cached skeleton if available
        
        Returns:
            Dictionary containing skeleton data:
            {
                "bones": [...],  # List of bone data
                "hierarchy": {...},  # Bone parent-child relationships
                "bone_count": int,
                "format": "humanoid" | "quadruped" | "other"
            }
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If file format is not supported
            RuntimeError: If skeleton extraction fails
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Check file format
        file_ext = model_path.suffix.lower()
        if file_ext not in ['.fbx', '.glb', '.gltf']:
            raise ValueError(f"Unsupported file format: {file_ext}. Only FBX and GLB are supported.")
        
        # Check cache
        if use_cache:
            cached_skeleton = self._load_from_cache(model_path)
            if cached_skeleton:
                logger.info(f"Loaded skeleton from cache for {model_path.name}")
                return cached_skeleton
        
        logger.info(f"Extracting skeleton from {model_path.name}")
        
        try:
            # Load model with trimesh
            scene = trimesh.load(str(model_path))
            
            # Extract skeleton data
            skeleton_data = self._extract_skeleton_from_scene(scene, model_path.name)
            
            # Cache the result
            if use_cache:
                self._save_to_cache(model_path, skeleton_data)
            
            return skeleton_data
            
        except Exception as e:
            logger.error(f"Failed to extract skeleton from {model_path.name}: {e}")
            raise RuntimeError(f"Skeleton extraction failed: {str(e)}")
    
    def _extract_skeleton_from_scene(self, scene, filename: str) -> Dict:
        """
        Extract skeleton data from a trimesh scene.
        
        Args:
            scene: Trimesh scene object
            filename: Original filename for logging
        
        Returns:
            Dictionary with skeleton data
        """
        bones = []
        hierarchy = {}
        
        # Handle both Scene and single Trimesh objects
        if isinstance(scene, trimesh.Scene):
            graph = scene.graph
            
            # Extract nodes from scene graph
            for node_name in graph.nodes:
                transform, _ = graph[node_name]
                
                # Check if this is a bone/joint node
                # Bones typically have specific naming patterns or are part of the skeleton
                if self._is_bone_node(node_name):
                    bone_data = {
                        "name": node_name,
                        "transform": transform.tolist() if isinstance(transform, np.ndarray) else transform,
                        "position": self._extract_position(transform),
                        "rotation": self._extract_rotation(transform),
                        "scale": self._extract_scale(transform)
                    }
                    bones.append(bone_data)
                    
                    # Build hierarchy
                    parent = self._find_parent(graph, node_name)
                    if parent:
                        hierarchy[node_name] = parent
        
        else:
            # Single mesh - try to extract from geometry
            logger.warning(f"Single mesh without explicit skeleton in {filename}")
            # For single meshes, we can't reliably extract skeleton
            # Return minimal skeleton data
            bones = [{
                "name": "root",
                "transform": np.eye(4).tolist(),
                "position": [0, 0, 0],
                "rotation": [0, 0, 0, 1],  # quaternion
                "scale": [1, 1, 1]
            }]
            hierarchy = {}
        
        # Detect skeleton type
        skeleton_type = self._detect_skeleton_type(bones)
        
        skeleton_data = {
            "bones": bones,
            "hierarchy": hierarchy,
            "bone_count": len(bones),
            "skeleton_type": skeleton_type,
            "root_bones": self._find_root_bones(hierarchy)
        }
        
        logger.info(f"Extracted {len(bones)} bones from {filename}, type: {skeleton_type}")
        
        return skeleton_data
    
    def _is_bone_node(self, node_name: str) -> bool:
        """
        Determine if a node is likely a bone/joint.
        
        Args:
            node_name: Name of the node
        
        Returns:
            True if node is likely a bone
        """
        bone_keywords = [
            'bone', 'joint', 'jnt', 'skeleton', 'rig',
            'spine', 'hips', 'hip', 'leg', 'arm', 'hand', 'foot',
            'head', 'neck', 'shoulder', 'elbow', 'knee', 'ankle', 'wrist',
            'finger', 'thumb', 'toe', 'tail', 'wing'
        ]
        
        node_lower = node_name.lower()
        return any(keyword in node_lower for keyword in bone_keywords)
    
    def _find_parent(self, graph, node_name: str) -> Optional[str]:
        """
        Find parent node in scene graph.
        
        Args:
            graph: Trimesh scene graph
            node_name: Node to find parent for
        
        Returns:
            Parent node name or None if root
        """
        try:
            # Get parent from graph edges
            for edge in graph.transforms.edge_data:
                if edge[1] == node_name:  # edge is (parent, child, key)
                    return edge[0]
        except:
            pass
        return None
    
    def _detect_skeleton_type(self, bones: List[Dict]) -> str:
        """
        Detect skeleton type based on bone names.
        
        Args:
            bones: List of bone dictionaries
        
        Returns:
            'humanoid', 'quadruped', or 'other'
        """
        bone_names = [bone['name'].lower() for bone in bones]
        bone_names_str = ' '.join(bone_names)
        
        # Humanoid indicators
        humanoid_keywords = ['spine', 'hips', 'shoulder', 'arm', 'hand', 'leg', 'foot', 'head']
        humanoid_count = sum(1 for kw in humanoid_keywords if kw in bone_names_str)
        
        # Quadruped indicators
        quadruped_keywords = ['tail', 'paw', 'frontleg', 'hindleg', 'hock']
        quadruped_count = sum(1 for kw in quadruped_keywords if kw in bone_names_str)
        
        if humanoid_count >= 4:
            return 'humanoid'
        elif quadruped_count >= 2:
            return 'quadruped'
        else:
            return 'other'
    
    def _find_root_bones(self, hierarchy: Dict) -> List[str]:
        """
        Find root bones (bones without parents).
        
        Args:
            hierarchy: Dictionary mapping child -> parent
        
        Returns:
            List of root bone names
        """
        all_bones = set(hierarchy.keys()) | set(hierarchy.values())
        children = set(hierarchy.keys())
        roots = all_bones - children
        return list(roots)
    
    def _extract_position(self, transform) -> List[float]:
        """Extract position from 4x4 transform matrix."""
        if isinstance(transform, np.ndarray) and transform.shape == (4, 4):
            return transform[:3, 3].tolist()
        return [0, 0, 0]
    
    def _extract_rotation(self, transform) -> List[float]:
        """Extract rotation as quaternion from 4x4 transform matrix."""
        if isinstance(transform, np.ndarray) and transform.shape == (4, 4):
            # Convert rotation matrix to quaternion
            # This is a simplified extraction - for production, use proper quaternion conversion
            rotation_matrix = transform[:3, :3]
            # Return as identity quaternion for now
            return [0, 0, 0, 1]  # [x, y, z, w]
        return [0, 0, 0, 1]
    
    def _extract_scale(self, transform) -> List[float]:
        """Extract scale from 4x4 transform matrix."""
        if isinstance(transform, np.ndarray) and transform.shape == (4, 4):
            scale_x = np.linalg.norm(transform[:3, 0])
            scale_y = np.linalg.norm(transform[:3, 1])
            scale_z = np.linalg.norm(transform[:3, 2])
            return [float(scale_x), float(scale_y), float(scale_z)]
        return [1, 1, 1]
    
    def export_to_bvh(self, skeleton_data: Dict, output_path: str) -> str:
        """
        Export skeleton to BVH format for motion retargeting.
        
        Args:
            skeleton_data: Skeleton data from extract_skeleton()
            output_path: Path for output BVH file
        
        Returns:
            Path to exported BVH file
        
        Raises:
            ValueError: If skeleton data is invalid
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Exporting skeleton to BVH: {output_path}")
        
        # Generate BVH content
        bvh_content = self._generate_bvh_content(skeleton_data)
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(bvh_content)
        
        logger.info(f"Skeleton exported to {output_path}")
        return str(output_path)
    
    def _generate_bvh_content(self, skeleton_data: Dict) -> str:
        """
        Generate BVH format content from skeleton data.
        
        Args:
            skeleton_data: Skeleton data dictionary
        
        Returns:
            BVH format string
        """
        bones = skeleton_data['bones']
        hierarchy = skeleton_data['hierarchy']
        root_bones = skeleton_data.get('root_bones', [])
        
        # BVH header
        bvh_lines = ["HIERARCHY"]
        
        # Build hierarchy recursively
        def build_bone_hierarchy(bone_name: str, indent: int = 0):
            indent_str = "  " * indent
            bone = next((b for b in bones if b['name'] == bone_name), None)
            
            if not bone:
                return
            
            # Determine if root or child
            is_root = bone_name in root_bones
            bone_type = "ROOT" if is_root else "JOINT"
            
            bvh_lines.append(f"{indent_str}{bone_type} {bone_name}")
            bvh_lines.append(f"{indent_str}{{")
            
            # Offset (position relative to parent)
            pos = bone.get('position', [0, 0, 0])
            bvh_lines.append(f"{indent_str}  OFFSET {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}")
            
            # Channels
            if is_root:
                bvh_lines.append(f"{indent_str}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation")
            else:
                bvh_lines.append(f"{indent_str}  CHANNELS 3 Zrotation Xrotation Yrotation")
            
            # Find children
            children = [child for child, parent in hierarchy.items() if parent == bone_name]
            
            if children:
                for child in children:
                    build_bone_hierarchy(child, indent + 1)
            else:
                # End site (leaf bone)
                bvh_lines.append(f"{indent_str}  End Site")
                bvh_lines.append(f"{indent_str}  {{")
                bvh_lines.append(f"{indent_str}    OFFSET 0.0 0.0 0.0")
                bvh_lines.append(f"{indent_str}  }}")
            
            bvh_lines.append(f"{indent_str}}}")
        
        # Build hierarchy starting from root bones
        if root_bones:
            for root in root_bones:
                build_bone_hierarchy(root)
        else:
            # No hierarchy, use first bone as root
            if bones:
                build_bone_hierarchy(bones[0]['name'])
        
        # Motion section (empty T-pose)
        bvh_lines.append("MOTION")
        bvh_lines.append("Frames: 1")
        bvh_lines.append("Frame Time: 0.033333")
        
        # Generate neutral pose (all zeros)
        num_channels = len(root_bones) * 6 + (len(bones) - len(root_bones)) * 3
        bvh_lines.append(" ".join(["0.0"] * num_channels))
        
        return "\n".join(bvh_lines)
    
    def _get_cache_key(self, model_path: Path) -> str:
        """
        Generate cache key based on file path and modification time.
        
        Args:
            model_path: Path to model file
        
        Returns:
            Cache key (MD5 hash)
        """
        stat = model_path.stat()
        key_string = f"{model_path.absolute()}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_from_cache(self, model_path: Path) -> Optional[Dict]:
        """
        Load skeleton data from cache.
        
        Args:
            model_path: Path to model file
        
        Returns:
            Cached skeleton data or None if not cached
        """
        cache_key = self._get_cache_key(model_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cached skeleton: {e}")
                return None
        
        return None
    
    def _save_to_cache(self, model_path: Path, skeleton_data: Dict):
        """
        Save skeleton data to cache.
        
        Args:
            model_path: Path to model file
            skeleton_data: Skeleton data to cache
        """
        cache_key = self._get_cache_key(model_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(skeleton_data, f, indent=2)
            logger.info(f"Saved skeleton to cache: {cache_file.name}")
        except Exception as e:
            logger.warning(f"Failed to save skeleton to cache: {e}")
    
    def clear_cache(self):
        """Clear all cached skeleton data."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info(f"Cleared skeleton cache: {self.cache_dir}")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_info(self) -> Dict:
        """
        Get information about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(self.cache_dir),
            "cached_skeletons": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
