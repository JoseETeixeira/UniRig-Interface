"""
Celery tasks package for background job processing.
Contains task definitions for skeleton generation, skinning, and merge operations.
"""

from app.tasks.celery_app import celery
from app.tasks.skeleton_task import generate_skeleton
from app.tasks.skinning_task import generate_skinning
from app.tasks.merge_task import merge_rigging

__all__ = ["celery", "generate_skeleton", "generate_skinning", "merge_rigging"]
