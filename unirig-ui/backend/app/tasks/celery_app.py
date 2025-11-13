"""
Celery application configuration.
Configures Celery with Redis broker and result backend.
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings


# Create Celery application
celery = Celery(
    "unirig_tasks",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend
)

# Celery configuration
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory management)
    task_acks_late=True,  # Acknowledge task after completion (retry on failure)
    task_reject_on_worker_lost=True,
    # Retry configuration
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max 10 minutes between retries
    task_retry_jitter=True,  # Add randomness to backoff
)

# Celery Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0),  # Run every hour at minute 0
    },
    'check-disk-space': {
        'task': 'tasks.check_disk_space',
        'schedule': crontab(minute=30),  # Run every hour at minute 30
    },
}

# Auto-discover tasks from app.tasks module
celery.autodiscover_tasks(["app.tasks"])

print("✅ Celery configured successfully with Beat schedule")

