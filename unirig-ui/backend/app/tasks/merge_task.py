"""
Merge Celery task.
Merges skeleton, skinning, and original mesh into final rigged model.
"""

import subprocess
import os
from pathlib import Path
from celery import Task
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery
from app.db.database import SessionLocal
from app.services.job_service import JobService
from app.services.file_service import FileService
from app.models.job import JobStatus, JobStage
from app.utils.errors import MergeError


class MergeTask(Task):
    """
    Custom Celery task for merging rigging results.
    Handles failure callbacks and retry logic.
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task failure.
        Updates job status to FAILED with error message.
        """
        job_id = kwargs.get("job_id")
        if job_id:
            db = SessionLocal()
            try:
                job_service = JobService(db)
                job_service.update_job(
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    error_message=str(exc)
                )
            finally:
                db.close()


@celery.task(base=MergeTask, bind=True, name="app.tasks.merge_rigging")
def merge_rigging(self, job_id: str, skeleton_file: str, skin_file: str, original_file: str):
    """
    Merge skeleton and skinning with original mesh.
    Executes UniRig's merge.sh script via subprocess.
    
    Args:
        self: Celery task instance (bound)
        job_id: Job identifier
        skeleton_file: Path to skeleton FBX file
        skin_file: Path to skinning FBX file
        original_file: Path to original uploaded model
        
    Returns:
        str: Path to final merged GLB file
        
    Raises:
        MergeError: If merge operation fails
    """
    db = SessionLocal()
    
    try:
        job_service = JobService(db)
        
        # Get job details
        job = job_service.get_job(job_id)
        
        # Validate all input files exist
        for file_path, name in [
            (skeleton_file, "skeleton"),
            (skin_file, "skinning"),
            (original_file, "original")
        ]:
            if not file_path or not Path(file_path).exists():
                raise MergeError(details=f"{name.capitalize()} file not found: {file_path}")
        
        # Update job status to PROCESSING
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.MERGE,
            progress=0.1
        )
        
        # Prepare output directory
        output_dir = FileService.ensure_results_directory(job.session_id)
        output_file = output_dir / f"{job_id}_rigged.glb"
        
        # Build command for merge operation
        unirig_root = Path(__file__).parent.parent.parent.parent / "UniRig"
        
        cmd = [
            "bash",
            str(unirig_root / "launch/inference/merge.sh"),
            "--skeleton", skeleton_file,
            "--skin", skin_file,
            "--source", original_file,
            "--output", str(output_file)
        ]
        
        # Execute subprocess with progress tracking
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(unirig_root)
        )
        
        # Monitor progress by parsing stdout
        stderr_lines = []
        for line in process.stdout:
            print(f"[Merge] {line.strip()}")
            
            # Update progress based on log output
            if "Loading" in line or "loading" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.3)
            elif "Merging" in line or "merging" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.6)
            elif "Exporting" in line or "exporting" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.9)
        
        # Wait for process to complete
        process.wait()
        
        # Capture stderr for error reporting
        stderr_output = process.stderr.read()
        if stderr_output:
            stderr_lines.append(stderr_output)
            print(f"[Merge STDERR] {stderr_output}")
        
        # Check return code
        if process.returncode != 0:
            error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
            raise MergeError(details=error_msg)
        
        # Verify output file exists
        if not output_file.exists():
            raise MergeError(
                details=f"Output file not created: {output_file}"
            )
        
        # Update job with success
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            stage=JobStage.MERGE,
            progress=1.0,
            final_file=str(output_file)
        )
        
        return str(output_file)
        
    except Exception as e:
        # Update job with failure
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error_message=str(e)
        )
        raise
        
    finally:
        db.close()
