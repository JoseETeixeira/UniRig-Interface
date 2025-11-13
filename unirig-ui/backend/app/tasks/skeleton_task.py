"""
Skeleton generation Celery task.
Executes UniRig skeleton prediction using subprocess and tracks progress.
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
from app.utils.errors import SkeletonGenerationError


class SkeletonGenerationTask(Task):
    """
    Custom Celery task for skeleton generation.
    Handles failure callbacks and retry logic.
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task failure.
        Updates job status to FAILED with error message.
        
        Args:
            exc: Exception that caused the failure
            task_id: Celery task ID
            args: Task positional arguments
            kwargs: Task keyword arguments
            einfo: Exception info
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


@celery.task(base=SkeletonGenerationTask, bind=True, name="app.tasks.generate_skeleton")
def generate_skeleton(self, job_id: str, input_file: str, seed: int = 42):
    """
    Generate skeleton structure for a 3D model.
    Executes UniRig's generate_skeleton.sh script via subprocess.
    
    Args:
        self: Celery task instance (bound)
        job_id: Job identifier
        input_file: Path to uploaded 3D model file
        seed: Random seed for skeleton generation (default: 42)
        
    Returns:
        str: Path to generated skeleton FBX file
        
    Raises:
        SkeletonGenerationError: If skeleton generation fails
    """
    db = SessionLocal()
    
    try:
        job_service = JobService(db)
        
        # Get job details
        job = job_service.get_job(job_id)
        
        # Update job status to PROCESSING
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            stage=JobStage.SKELETON,
            progress=0.1
        )
        
        # Prepare output directory
        output_dir = FileService.ensure_results_directory(job.session_id)
        output_file = output_dir / f"{job_id}_skeleton.fbx"
        
        # Build command for skeleton generation
        # Path to UniRig root (3 levels up from app/tasks/)
        unirig_root = Path(__file__).parent.parent.parent.parent / "UniRig"
        
        cmd = [
            "bash",
            str(unirig_root / "launch/inference/generate_skeleton.sh"),
            "--input", input_file,
            "--output", str(output_file),
            "--seed", str(seed)
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
            print(f"[Skeleton] {line.strip()}")
            
            # Update progress based on log output
            if "Loading model" in line or "loading model" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.3)
            elif "Processing mesh" in line or "processing" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.5)
            elif "Generating skeleton" in line or "generating" in line.lower():
                job_service.update_job(job_id=job_id, progress=0.7)
        
        # Wait for process to complete
        process.wait()
        
        # Capture stderr for error reporting
        stderr_output = process.stderr.read()
        if stderr_output:
            stderr_lines.append(stderr_output)
            print(f"[Skeleton STDERR] {stderr_output}")
        
        # Check return code
        if process.returncode != 0:
            error_msg = "\n".join(stderr_lines) if stderr_lines else "Unknown error"
            raise SkeletonGenerationError(details=error_msg)
        
        # Verify output file exists
        if not output_file.exists():
            raise SkeletonGenerationError(
                details=f"Output file not created: {output_file}"
            )
        
        # Update job with success
        job_service.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            stage=JobStage.SKELETON,
            progress=1.0,
            skeleton_file=str(output_file)
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
