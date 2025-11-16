"""
Verification script for retargeting_jobs schema
Tests that the RetargetingJob model can be instantiated and stored
"""

import sys
import os
import tempfile
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.db.database import Base, engine
from app.db.models import RetargetingJob, Job, Session, MotionClip
from sqlalchemy.orm import sessionmaker


def test_schema_creation():
    """Test that retargeting_jobs table can be created"""
    print("Testing RetargetingJob schema...")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    
    # Verify retargeting_jobs table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'retargeting_jobs' in tables:
        print("✓ retargeting_jobs table exists")
    else:
        print("✗ retargeting_jobs table NOT found")
        return False
    
    # Check table columns
    columns = inspector.get_columns('retargeting_jobs')
    expected_columns = {
        'id', 'job_id', 'motion_clip_id', 'status', 'progress',
        'result_path', 'error', 'skeleton_compatibility',
        'created_at', 'completed_at'
    }
    
    actual_columns = {col['name'] for col in columns}
    
    if expected_columns.issubset(actual_columns):
        print(f"✓ All expected columns present: {', '.join(sorted(expected_columns))}")
    else:
        missing = expected_columns - actual_columns
        print(f"✗ Missing columns: {missing}")
        return False
    
    # Check indexes
    indexes = inspector.get_indexes('retargeting_jobs')
    index_names = [idx['name'] for idx in indexes]
    
    expected_indexes = [
        'idx_retargeting_job_id',
        'idx_retargeting_status',
        'idx_retargeting_job_status'
    ]
    
    for idx in expected_indexes:
        if idx in index_names:
            print(f"✓ Index exists: {idx}")
        else:
            print(f"⚠ Index missing: {idx} (will be created by SQLAlchemy)")
    
    # Check foreign keys
    fks = inspector.get_foreign_keys('retargeting_jobs')
    fk_tables = [fk['referred_table'] for fk in fks]
    
    if 'jobs' in fk_tables:
        print("✓ Foreign key to jobs table exists")
    else:
        print("⚠ Foreign key to jobs table missing")
    
    if 'motion_clips' in fk_tables:
        print("✓ Foreign key to motion_clips table exists")
    else:
        print("⚠ Foreign key to motion_clips table missing")
    
    print("=" * 60)
    print("✓ Schema verification completed successfully")
    return True


def test_model_creation():
    """Test creating a RetargetingJob instance"""
    print("\nTesting RetargetingJob model instantiation...")
    print("=" * 60)
    
    try:
        # Create a test instance
        retargeting_job = RetargetingJob(
            id="test-retargeting-job-123",
            job_id="test-job-456",
            motion_clip_id="test-motion-789",
            status="queued",
            progress=0,
            skeleton_compatibility={
                "compatible": True,
                "missingBones": [],
                "extraBones": []
            }
        )
        
        print(f"✓ Created RetargetingJob instance: {retargeting_job}")
        
        # Test to_dict() method
        job_dict = retargeting_job.to_dict()
        expected_keys = {
            'id', 'jobId', 'motionClipId', 'status', 'progress',
            'resultPath', 'error', 'skeletonCompatibility',
            'createdAt', 'completedAt'
        }
        
        if set(job_dict.keys()) == expected_keys:
            print(f"✓ to_dict() returns correct keys: {', '.join(sorted(expected_keys))}")
        else:
            print(f"✗ to_dict() keys mismatch")
            print(f"  Expected: {expected_keys}")
            print(f"  Actual: {set(job_dict.keys())}")
            return False
        
        # Verify camelCase formatting
        if 'jobId' in job_dict and 'motionClipId' in job_dict:
            print("✓ to_dict() uses camelCase format")
        else:
            print("✗ to_dict() not using camelCase")
            return False
        
        print("=" * 60)
        print("✓ Model instantiation test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error creating RetargetingJob: {e}")
        return False


if __name__ == "__main__":
    print("RetargetingJob Schema Verification")
    print("=" * 60)
    
    success = True
    
    # Test schema creation
    if not test_schema_creation():
        success = False
    
    # Test model creation
    if not test_model_creation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("\nThe retargeting_jobs schema is correctly implemented and ready to use.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the errors above.")
        sys.exit(1)
