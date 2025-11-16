"""
FBX Animation Merger Utility.
Merges retargeted animation files into the main model file using FBX SDK.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FBXMergeError(Exception):
    """Custom exception for FBX merge operations."""
    pass


def merge_animation_into_model(
    model_path: str,
    animation_path: str,
    animation_name: Optional[str] = None
) -> None:
    """
    Merge a retargeted animation FBX into the main model file.
    
    This function uses Blender's Python API to:
    1. Load the main model FBX
    2. Import the animation FBX
    3. Transfer the animation to the model's skeleton
    4. Export the combined result back to the original model path
    
    Args:
        model_path: Path to the main rigged model FBX file
        animation_path: Path to the retargeted animation FBX file
        animation_name: Optional name for the animation (defaults to filename)
    
    Raises:
        FBXMergeError: If merge operation fails
        FileNotFoundError: If model or animation file doesn't exist
    
    Example:
        merge_animation_into_model(
            model_path="/results/session-id/job-id_final.fbx",
            animation_path="/results/session-id/job-id_retargeted_motion-001.fbx",
            animation_name="Walking Animation"
        )
    """
    # Validate input files exist
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    if not os.path.exists(animation_path):
        raise FileNotFoundError(f"Animation file not found: {animation_path}")
    
    # Create backup of original model
    backup_path = f"{model_path}.backup"
    try:
        shutil.copy2(model_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    except Exception as e:
        raise FBXMergeError(f"Failed to create backup: {e}")
    
    # Prepare animation name
    if not animation_name:
        animation_name = Path(animation_path).stem
    
    # Create Blender Python script for merging
    script_content = f"""
import bpy
import sys

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import main model
bpy.ops.import_scene.fbx(filepath="{model_path}")
print("✅ Loaded main model")

# Get the armature object
armature_obj = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature_obj = obj
        break

if not armature_obj:
    print("❌ No armature found in main model")
    sys.exit(1)

# Store original animation data
original_action = None
if armature_obj.animation_data and armature_obj.animation_data.action:
    original_action = armature_obj.animation_data.action

# Import animation FBX
bpy.ops.import_scene.fbx(filepath="{animation_path}")
print("✅ Loaded animation FBX")

# Find the imported animation data
imported_action = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE' and obj != armature_obj:
        if obj.animation_data and obj.animation_data.action:
            imported_action = obj.animation_data.action
            # Remove the imported armature (we only need the animation)
            bpy.data.objects.remove(obj, do_unlink=True)
            break

if not imported_action:
    print("❌ No animation found in animation FBX")
    sys.exit(1)

# Rename the imported action
imported_action.name = "{animation_name}"

# Ensure armature has animation data
if not armature_obj.animation_data:
    armature_obj.animation_data_create()

# Add the animation as a new action (don't replace, append)
# For now, we'll set it as the active action
# In future, this could be extended to support multiple actions
armature_obj.animation_data.action = imported_action

print(f"✅ Merged animation: {{imported_action.name}}")

# Export back to original path
bpy.ops.export_scene.fbx(
    filepath="{model_path}",
    use_selection=False,
    bake_anim=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True
)
print("✅ Exported merged model")

sys.exit(0)
"""
    
    # Write Blender script to temp file
    script_path = f"{model_path}.merge_script.py"
    try:
        with open(script_path, 'w') as f:
            f.write(script_content)
    except Exception as e:
        # Restore backup if script creation fails
        if os.path.exists(backup_path):
            shutil.move(backup_path, model_path)
        raise FBXMergeError(f"Failed to create merge script: {e}")
    
    # Execute Blender in background mode
    try:
        logger.info(f"Executing Blender merge script...")
        
        # Try to find Blender executable
        blender_cmd = shutil.which("blender")
        if not blender_cmd:
            # Common Blender installation paths
            possible_paths = [
                "/usr/bin/blender",
                "/usr/local/bin/blender",
                "/opt/blender/blender",
                "C:\\Program Files\\Blender Foundation\\Blender\\blender.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    blender_cmd = path
                    break
        
        if not blender_cmd:
            raise FBXMergeError(
                "Blender not found. Please install Blender and ensure it's in PATH."
            )
        
        # Run Blender in background
        result = subprocess.run(
            [blender_cmd, "--background", "--python", script_path],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        # Log output
        logger.debug(f"Blender stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Blender stderr: {result.stderr}")
        
        # Check if successful
        if result.returncode != 0:
            # Restore backup on failure
            if os.path.exists(backup_path):
                shutil.move(backup_path, model_path)
            raise FBXMergeError(
                f"Blender script failed with exit code {result.returncode}. "
                f"Output: {result.stdout}\nErrors: {result.stderr}"
            )
        
        logger.info(f"✅ Successfully merged animation into {model_path}")
        
    except subprocess.TimeoutExpired:
        # Restore backup on timeout
        if os.path.exists(backup_path):
            shutil.move(backup_path, model_path)
        raise FBXMergeError("Blender merge operation timed out after 30 seconds")
    
    except Exception as e:
        # Restore backup on any error
        if os.path.exists(backup_path):
            shutil.move(backup_path, model_path)
        raise FBXMergeError(f"Failed to execute merge: {e}")
    
    finally:
        # Cleanup
        if os.path.exists(script_path):
            try:
                os.remove(script_path)
            except:
                pass
        
        # Remove backup on success
        if os.path.exists(backup_path) and os.path.exists(model_path):
            try:
                os.remove(backup_path)
                logger.info("Removed backup file")
            except:
                pass  # Backup can remain if cleanup fails
