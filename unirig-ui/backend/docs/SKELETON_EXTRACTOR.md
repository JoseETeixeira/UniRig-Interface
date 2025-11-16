# Skeleton Extractor Utility

## Overview

The `SkeletonExtractor` utility extracts bone hierarchy and transformation data from rigged 3D models (FBX/GLB formats) for use in motion retargeting workflows. It provides caching to improve performance and exports skeletons in BVH format compatible with the Deep Motion Editing framework.

## Features

- **Format Support**: Extracts skeletons from FBX and GLB rigged models
- **Bone Detection**: Automatically identifies bones in the model hierarchy
- **Skeleton Classification**: Detects skeleton type (humanoid, quadruped, other)
- **BVH Export**: Exports skeletons in standard BVH format for motion retargeting
- **Caching**: File-based caching with automatic invalidation on file changes
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Installation

The skeleton extractor requires the `trimesh` library:

```bash
pip install trimesh
```

## Basic Usage

### Initialize the Extractor

```python
from app.utils import SkeletonExtractor

# Use default cache directory (/app/skeleton_cache)
extractor = SkeletonExtractor()

# Or specify custom cache directory
extractor = SkeletonExtractor(cache_dir="/custom/cache/path")
```

### Extract Skeleton from Model

```python
# Extract skeleton (uses cache if available)
skeleton_data = extractor.extract_skeleton("/path/to/model.fbx")

# Force re-extraction (bypass cache)
skeleton_data = extractor.extract_skeleton("/path/to/model.fbx", use_cache=False)

# Skeleton data structure:
# {
#     "bones": [...],           # List of bone dictionaries
#     "hierarchy": {...},        # Parent-child relationships
#     "bone_count": 65,          # Number of bones
#     "skeleton_type": "humanoid", # Detected type
#     "root_bones": ["Hips"]     # Root bone names
# }
```

### Export to BVH Format

```python
# Export skeleton to BVH file
bvh_path = extractor.export_to_bvh(
    skeleton_data,
    "/path/to/output/skeleton.bvh"
)
print(f"Exported to: {bvh_path}")
```

## Advanced Usage

### Cache Management

```python
# Get cache statistics
cache_info = extractor.get_cache_info()
print(f"Cached skeletons: {cache_info['cached_skeletons']}")
print(f"Cache size: {cache_info['total_size_mb']} MB")

# Clear all cached data
extractor.clear_cache()
```

### Skeleton Data Structure

Each bone in the extracted skeleton contains:

```python
{
    "name": "Hips",                     # Bone name
    "transform": [[...], [...], ...],   # 4x4 transformation matrix
    "position": [0, 0, 0],              # Translation
    "rotation": [0, 0, 0, 1],           # Quaternion rotation
    "scale": [1, 1, 1]                  # Scale factors
}
```

The hierarchy maps child bones to their parents:

```python
{
    "Spine": "Hips",           # Spine's parent is Hips
    "LeftArm": "Spine",        # LeftArm's parent is Spine
    "RightArm": "Spine"        # RightArm's parent is Spine
}
```

## Integration with Motion Retargeting

### Use in Retargeting Service

```python
from app.utils import SkeletonExtractor
from app.db.database import get_db
from app.db.models import Job

extractor = SkeletonExtractor()

def prepare_skeleton_for_retargeting(job_id: str):
    """Extract skeleton from completed rigging job."""
    db = next(get_db())
    
    # Get job details
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job or job.status != "completed":
        raise ValueError("Job not completed")
    
    # Extract skeleton from rigged model
    model_path = job.final_file  # Path to rigged FBX/GLB
    skeleton_data = extractor.extract_skeleton(model_path)
    
    # Export to BVH for Deep Motion Editing
    bvh_path = f"/tmp/skeletons/{job_id}_skeleton.bvh"
    extractor.export_to_bvh(skeleton_data, bvh_path)
    
    return {
        "skeleton_path": bvh_path,
        "skeleton_type": skeleton_data["skeleton_type"],
        "bone_count": skeleton_data["bone_count"]
    }
```

### Use in Celery Worker

```python
from celery import Task
from app.utils import SkeletonExtractor

class RetargetingTask(Task):
    def __init__(self):
        self.extractor = SkeletonExtractor()
    
    def run(self, job_id, motion_clip_id):
        # Extract target skeleton
        skeleton_data = self.extractor.extract_skeleton(
            f"/app/results/{job_id}_rigged.fbx"
        )
        
        # Export to BVH
        bvh_path = f"/tmp/{job_id}_skeleton.bvh"
        self.extractor.export_to_bvh(skeleton_data, bvh_path)
        
        # Pass to Deep Motion Editing framework
        # ... retargeting logic ...
```

## Skeleton Type Detection

The extractor automatically classifies skeletons:

- **humanoid**: Contains typical humanoid bones (hips, spine, arms, legs, head)
- **quadruped**: Contains quadruped-specific bones (tail, paws, front/hind legs)
- **other**: Unrecognized or custom skeleton structure

```python
skeleton_data = extractor.extract_skeleton(model_path)

if skeleton_data["skeleton_type"] == "humanoid":
    print("This is a humanoid character")
    # Use humanoid motion clips
elif skeleton_data["skeleton_type"] == "quadruped":
    print("This is a quadruped character")
    # Use quadruped motion clips
else:
    print("Custom skeleton - compatibility check required")
```

## Error Handling

```python
from app.utils import SkeletonExtractor

extractor = SkeletonExtractor()

try:
    skeleton_data = extractor.extract_skeleton(model_path)
except FileNotFoundError as e:
    print(f"Model file not found: {e}")
except ValueError as e:
    print(f"Unsupported file format: {e}")
except RuntimeError as e:
    print(f"Extraction failed: {e}")
```

## Performance Considerations

### Caching Behavior

- Cache keys are based on file path, modification time, and size
- Cache is automatically invalidated when the source file changes
- First extraction is slower (parsing required), subsequent extractions are instant
- Cache files are stored as JSON for easy inspection

### Optimization Tips

1. **Use caching for production**: Always use `use_cache=True` (default)
2. **Clear old cache periodically**: Run `clear_cache()` to free disk space
3. **Batch processing**: Reuse the same `SkeletonExtractor` instance
4. **Monitor cache size**: Use `get_cache_info()` to track cache growth

## BVH Format Details

The exported BVH file contains:

- **HIERARCHY section**: Bone structure with offsets and channels
- **MOTION section**: T-pose frame data (neutral position)
- **Standard channels**: 6DOF for root (position + rotation), 3DOF for joints (rotation only)

Example BVH structure:

```
HIERARCHY
ROOT Hips
{
  OFFSET 0.0 0.0 0.0
  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
  JOINT Spine
  {
    OFFSET 0.0 1.0 0.0
    CHANNELS 3 Zrotation Xrotation Yrotation
    End Site
    {
      OFFSET 0.0 0.0 0.0
    }
  }
}
MOTION
Frames: 1
Frame Time: 0.033333
0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0
```

## Testing

The skeleton extractor includes comprehensive unit tests:

```bash
# Run all skeleton extractor tests
pytest tests/test_skeleton_extractor.py

# Run with coverage
pytest tests/test_skeleton_extractor.py --cov=app.utils.skeleton_extractor

# Run specific test class
pytest tests/test_skeleton_extractor.py::TestBoneDetection
```

## Troubleshooting

### No bones detected

- **Cause**: Model has no recognizable bone structure
- **Solution**: Check that model is rigged (not just a static mesh)

### Wrong skeleton type detected

- **Cause**: Bone naming doesn't match expected patterns
- **Solution**: Verify bone names contain standard keywords (spine, arm, leg, etc.)

### Cache not working

- **Cause**: File permissions or disk space issues
- **Solution**: Check cache directory permissions and available disk space

### BVH export fails

- **Cause**: Invalid skeleton data or circular hierarchy
- **Solution**: Validate skeleton data structure before export

## API Reference

### SkeletonExtractor Class

#### Methods

- `__init__(cache_dir: Optional[str] = None)`
  - Initialize extractor with optional custom cache directory

- `extract_skeleton(model_path: str, use_cache: bool = True) -> Dict`
  - Extract skeleton from FBX/GLB model
  - Returns dictionary with bones, hierarchy, and metadata

- `export_to_bvh(skeleton_data: Dict, output_path: str) -> str`
  - Export skeleton to BVH format
  - Returns path to exported file

- `clear_cache()`
  - Delete all cached skeleton data

- `get_cache_info() -> Dict`
  - Get cache statistics (count, size)

## Future Enhancements

Planned improvements:

- [ ] Support for additional formats (COLLADA, USD)
- [ ] Improved quaternion conversion for accurate rotations
- [ ] Bone mapping suggestions for retargeting
- [ ] Visualization of extracted skeletons
- [ ] Parallel batch processing
- [ ] Automatic skeleton repair for malformed hierarchies
