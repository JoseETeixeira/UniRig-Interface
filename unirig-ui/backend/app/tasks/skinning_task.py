"""
Skinning generation Celery task.
Executes UniRig skinning weight prediction using subprocess.
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
from app.utils.errors import SkinningGenerationError


class SkinningGenerationTask(Task):
    """
    Custom Celery task for skinning generation.
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


@celery.task(base=SkinningGenerationTask, bind=True, name="app.tasks.generate_skinning")
def generate_skinning(self, job_id: str, skeleton_file: str):
    """
    Generate skinning weights for a skeleton.
    Executes UniRig's generate_skin.sh script via subprocess.
    
    Args:
        self: Celery task instance (bound)
        job_id: Job identifier
        skeleton_file: Path to generated skeleton FBX file
        
    Returns:
        str: Path to generated skinning FBX file
        
    Raises:
        SkinningGenerationError: If skinning generation fails
    """
    db = SessionLocal()
    
    try:
        job_service = JobService(db)
        
        # Get job details
        job = job_service.get_job(job_id)
        
        # Validate skeleton file exists
        if not skeleton_file or not Path(skeleton_file).exists():
            raise SkinningGenerationError(
                details=f"Skeleton file not found: {skeleton_file}"
            )
        
        # Update job status to PROCESSING
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.SKINNING,
            progress=0.1
        )
        
        # Prepare output directory
        output_dir = FileService.ensure_results_directory(job.session_id)
        output_file = output_dir / f"{job_id}_skin.fbx"
        
        # Build command for skinning generation
        # UniRig is mounted at /app/UniRig in the worker container
        unirig_root = Path("/app/UniRig")
        
        cmd = [
            "bash",
            str(unirig_root / "launch/inference/generate_skin.sh"),
            "--input", skeleton_file,
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
            print(f"[Skinning] {line.strip()}")
            
            # Update progress based on log output
            if "Loading" in line or "loading" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.3)
            elif "Computing" in line or "computing" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.5)
            elif "Generating" in line or "generating" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.7)
            elif "Saving" in line or "saving" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.9)
        
        # Wait for process to complete
        process.wait()
        
        # Capture stderr for error reporting
        stderr_output = process.stderr.read()
        if stderr_output:
            stderr_lines.append(stderr_output)
            print(f"[Skinning STDERR] {stderr_output}")
        
        # Check return code
        if process.returncode != 0:
            error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
            raise SkinningGenerationError(details=error_msg)
        
        # Verify output file exists
        if not output_file.exists():
            raise SkinningGenerationError(
                details=f"Output file not created: {output_file}"
            )
        
        # Update job with success
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            stage=JobStage.SKINNING,
            progress=1.0,
            skin_file=str(output_file)
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
