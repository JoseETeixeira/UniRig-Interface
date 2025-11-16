"""
Motion retargeting Celery task using Deep Motion Editing framework.
Handles transferring motion clips from the preprocessed dataset to rigged models.
"""

import os
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery
from app.db.database import SessionLocal
from app.db.models import RetargetingJob, Job, MotionClip
from app.utils.skeleton_extractor import SkeletonExtractor
from app.config import settings


class RetargetingTaskError(Exception):
    """Custom exception for retargeting task errors."""
    pass


class RetargetingTask(Task):
    """
    Custom Celery task for motion retargeting.
    Handles failure callbacks and progress tracking.
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task failure.
        Updates RetargetingJob status to FAILED with error message.
        
        Args:
            exc: Exception that caused the failure
            task_id: Celery task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        retargeting_job_id = kwargs.get("retargeting_job_id")
        if retargeting_job_id:
            db = SessionLocal()
            try:
                retargeting_job = db.query(RetargetingJob).filter(
                    RetargetingJob.id == retargeting_job_id
                ).first()
                
                if retargeting_job:
                    error_message = str(exc)
                    
                    # Special handling for GPU errors
                    if "CUDA out of memory" in error_message or "GPU" in error_message:
                        error_message = "GPU memory error: Unable to process retargeting. Please try with a simpler motion or contact support."
                    
                    retargeting_job.status = "failed"
                    retargeting_job.error = error_message
                    retargeting_job.completed_at = datetime.utcnow()
                    db.commit()
                    
                    print(f"❌ Retargeting job {retargeting_job_id} failed: {error_message}")
            except Exception as e:
                print(f"❌ Error updating failed retargeting job {retargeting_job_id}: {e}")
                db.rollback()
            finally:
                db.close()


@celery.task(
    base=RetargetingTask,
    bind=True,
    name="app.tasks.retarget_motion",
    queue="dme-retargeting",
    soft_time_limit=90,  # 90 seconds soft limit per design
    time_limit=120,  # 120 seconds hard limit
    max_retries=2,
    default_retry_delay=60
)
def retarget_motion_task(
    self,
    retargeting_job_id: str,
    job_id: str,
    motion_clip_id: str
) -> Dict[str, str]:
    """
    Execute motion retargeting using Deep Motion Editing framework.
    
    This task:
    1. Loads source motion clip from dataset (progress: 20%)
    2. Loads target skeleton from rigged model (progress: 40%)
    3. Invokes DME retargeting algorithm (progress: 50-80%)
    4. Saves retargeted animation to results directory (progress: 90%)
    5. Updates job status to completed (progress: 100%)
    
    Args:
        self: Celery task instance (bound)
        retargeting_job_id: RetargetingJob identifier
        job_id: Parent Job identifier (rigged model)
        motion_clip_id: MotionClip identifier from dataset
        
    Returns:
        dict: Result with output file path
        
    Raises:
        RetargetingTaskError: If retargeting fails
        SoftTimeLimitExceeded: If task exceeds 90 second timeout
    """
    db = SessionLocal()
    start_time = time.time()
    
    try:
        # Fetch retargeting job
        retargeting_job = db.query(RetargetingJob).filter(
            RetargetingJob.id == retargeting_job_id
        ).first()
        
        if not retargeting_job:
            raise RetargetingTaskError(f"RetargetingJob {retargeting_job_id} not found")
        
        # Update status to processing
        retargeting_job.status = "processing"
        retargeting_job.progress = 0
        db.commit()
        
        print(f"🎬 Starting motion retargeting: job={job_id}, motion={motion_clip_id}")
        
        # Step 1: Load motion clip metadata (20% progress)
        retargeting_job.progress = 20
        db.commit()
        
        motion_clip = db.query(MotionClip).filter(
            MotionClip.id == motion_clip_id
        ).first()
        
        if not motion_clip:
            raise RetargetingTaskError(f"Motion clip {motion_clip_id} not found")
        
        motion_file_path = Path(settings.motion_cache_dir) / motion_clip.file_name
        if not motion_file_path.exists():
            raise RetargetingTaskError(f"Motion file not found: {motion_file_path}")
        
        print(f"✅ Loaded motion clip: {motion_clip.name} ({motion_clip.duration}s)")
        
        # Step 2: Load target skeleton from rigged model (40% progress)
        retargeting_job.progress = 40
        db.commit()
        
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job or job.status != "completed":
            raise RetargetingTaskError(f"Job {job_id} not found or not completed")
        
        # Get the final rigged file
        if not job.final_file or not os.path.exists(job.final_file):
            raise RetargetingTaskError(f"Rigged model file not found: {job.final_file}")
        
        target_skeleton_path = job.final_file
        
        print(f"✅ Loaded target skeleton from: {target_skeleton_path}")
        
        # Step 3: Prepare output path
        output_dir = Path(job.final_file).parent
        output_filename = f"{job_id}_retargeted_{motion_clip_id}.fbx"
        output_path = output_dir / output_filename
        
        # Step 4: Invoke Deep Motion Editing retargeting (50-80% progress)
        retargeting_job.progress = 50
        db.commit()
        
        print(f"🔄 Invoking DME retargeting algorithm...")
        
        # Build command for DME retargeting
        # Note: This is a placeholder for actual DME integration
        # The real implementation would call the DME Python API or subprocess
        result = _execute_dme_retargeting(
            source_motion=str(motion_file_path),
            target_skeleton=str(target_skeleton_path),
            output_file=str(output_path),
            progress_callback=lambda progress: _update_progress(
                db, retargeting_job_id, 50 + int(progress * 0.3)
            )
        )
        
        # Step 5: Verify output and finalize (90% progress)
        retargeting_job.progress = 90
        db.commit()
        
        if not output_path.exists():
            raise RetargetingTaskError(f"DME did not produce output file: {output_path}")
        
        print(f"✅ Retargeted animation saved to: {output_path}")
        
        # Step 6: Update job to completed (100% progress)
        retargeting_job.status = "completed"
        retargeting_job.progress = 100
        retargeting_job.result_path = str(output_path)
        retargeting_job.completed_at = datetime.utcnow()
        retargeting_job.error = None
        db.commit()
        
        elapsed_time = time.time() - start_time
        print(f"✅ Motion retargeting completed in {elapsed_time:.2f}s")
        
        return {
            "status": "completed",
            "result_path": str(output_path),
            "processing_time": elapsed_time
        }
    
    except SoftTimeLimitExceeded:
        # Handle timeout
        print(f"⏱️ Retargeting job {retargeting_job_id} exceeded 90 second timeout")
        retargeting_job = db.query(RetargetingJob).filter(
            RetargetingJob.id == retargeting_job_id
        ).first()
        if retargeting_job:
            retargeting_job.status = "failed"
            retargeting_job.error = "Processing timeout: Motion retargeting exceeded 90 second limit. Try with a simpler motion."
            retargeting_job.completed_at = datetime.utcnow()
            db.commit()
        raise
    
    except Exception as e:
        # Log detailed error for debugging
        error_msg = f"Motion retargeting failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Re-raise to trigger failure callback
        raise RetargetingTaskError(error_msg) from e
    
    finally:
        db.close()


def _update_progress(db: Session, retargeting_job_id: str, progress: int):
    """
    Update retargeting job progress in database.
    
    Args:
        db: Database session
        retargeting_job_id: RetargetingJob identifier
        progress: Progress percentage (0-100)
    """
    try:
        retargeting_job = db.query(RetargetingJob).filter(
            RetargetingJob.id == retargeting_job_id
        ).first()
        
        if retargeting_job:
            retargeting_job.progress = progress
            db.commit()
    except Exception as e:
        print(f"⚠️ Failed to update progress for {retargeting_job_id}: {e}")
        db.rollback()


def _execute_dme_retargeting(
    source_motion: str,
    target_skeleton: str,
    output_file: str,
    progress_callback=None
) -> Dict:
    """
    Execute Deep Motion Editing retargeting algorithm.
    
    This is a placeholder implementation. The actual implementation would:
    1. Load the DME model
    2. Parse source motion and target skeleton
    3. Perform bone mapping and motion transfer
    4. Export retargeted animation
    
    Args:
        source_motion: Path to source motion file
        target_skeleton: Path to target skeleton/rigged model
        output_file: Path to save retargeted animation
        progress_callback: Optional callback for progress updates
        
    Returns:
        dict: Retargeting result metadata
        
    Raises:
        RetargetingTaskError: If retargeting fails
    """
    try:
        # TODO: Replace with actual DME Python API calls
        # For now, this is a placeholder that would be replaced with:
        #
        # from deep_motion_editing import DMERetargeter
        # retargeter = DMERetargeter(model_path="/app/dme/models")
        # result = retargeter.retarget(
        #     source_motion=source_motion,
        #     target_skeleton=target_skeleton,
        #     output_file=output_file,
        #     device="cuda" if torch.cuda.is_available() else "cpu"
        # )
        
        # Simulated progress updates
        if progress_callback:
            progress_callback(0.0)   # Starting
            time.sleep(0.1)
            progress_callback(0.33)  # Bone mapping
            time.sleep(0.1)
            progress_callback(0.66)  # Motion transfer
            time.sleep(0.1)
            progress_callback(1.0)   # Complete
        
        # For testing purposes, create a placeholder output file
        # In production, this would be replaced by actual DME processing
        print("⚠️ PLACEHOLDER: DME integration not yet complete")
        print(f"   Source: {source_motion}")
        print(f"   Target: {target_skeleton}")
        print(f"   Output: {output_file}")
        
        # Create placeholder output for testing
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("# Placeholder retargeted animation\n")
            f.write(f"# Source: {source_motion}\n")
            f.write(f"# Target: {target_skeleton}\n")
        
        return {
            "success": True,
            "bone_mapping": {
                "matched_bones": 50,
                "source_bones": 55,
                "target_bones": 52
            }
        }
    
    except subprocess.CalledProcessError as e:
        raise RetargetingTaskError(
            f"DME process failed with exit code {e.returncode}: {e.stderr}"
        )
    except FileNotFoundError as e:
        raise RetargetingTaskError(f"DME executable or file not found: {e}")
    except Exception as e:
        raise RetargetingTaskError(f"Unexpected DME error: {e}")
