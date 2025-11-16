"""
Database migration: Create retargeting_jobs table
Migration 003: Add retargeting_jobs table for motion retargeting workflow
"""

import sqlite3
import os


def upgrade():
    """Create retargeting_jobs table"""
    # Get database path from environment variable or use default
    db_path = os.getenv("DATABASE_PATH", "./unirig_ui.db")
    
    # Check if database exists
    if not os.path.exists(db_path):
        # If database doesn't exist, it will be created by init_db()
        print(f"⚠ Database not found at {db_path}")
        print("  Table will be created automatically on application startup")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='retargeting_jobs'
        """)
        
        if cursor.fetchone():
            print("⚠ retargeting_jobs table already exists")
            conn.close()
            return
        
        # Create retargeting_jobs table
        cursor.execute("""
            CREATE TABLE retargeting_jobs (
                id VARCHAR(255) PRIMARY KEY NOT NULL,
                job_id VARCHAR NOT NULL,
                motion_clip_id VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'queued',
                progress INTEGER DEFAULT 0,
                result_path VARCHAR(500),
                error TEXT,
                skeleton_compatibility TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
                FOREIGN KEY (motion_clip_id) REFERENCES motion_clips(id) ON DELETE RESTRICT
            )
        """)
        print("✓ Created retargeting_jobs table")
        
        # Create indexes for efficient queries
        cursor.execute("""
            CREATE INDEX idx_retargeting_job_id ON retargeting_jobs(job_id)
        """)
        print("✓ Created index: idx_retargeting_job_id")
        
        cursor.execute("""
            CREATE INDEX idx_retargeting_status ON retargeting_jobs(status)
        """)
        print("✓ Created index: idx_retargeting_status")
        
        cursor.execute("""
            CREATE INDEX idx_retargeting_job_status ON retargeting_jobs(job_id, status)
        """)
        print("✓ Created index: idx_retargeting_job_status")
        
        cursor.execute("""
            CREATE INDEX ix_retargeting_jobs_id ON retargeting_jobs(id)
        """)
        print("✓ Created index: ix_retargeting_jobs_id")
        
        cursor.execute("""
            CREATE INDEX ix_retargeting_jobs_job_id ON retargeting_jobs(job_id)
        """)
        print("✓ Created index: ix_retargeting_jobs_job_id")
        
        cursor.execute("""
            CREATE INDEX ix_retargeting_jobs_motion_clip_id ON retargeting_jobs(motion_clip_id)
        """)
        print("✓ Created index: ix_retargeting_jobs_motion_clip_id")
        
        cursor.execute("""
            CREATE INDEX ix_retargeting_jobs_status ON retargeting_jobs(status)
        """)
        print("✓ Created index: ix_retargeting_jobs_status")
        
        conn.commit()
        print("✓ Migration 003 completed successfully")
        
    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def downgrade():
    """Drop retargeting_jobs table"""
    db_path = os.getenv("DATABASE_PATH", "./unirig_ui.db")
    
    if not os.path.exists(db_path):
        print(f"⚠ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP TABLE IF EXISTS retargeting_jobs")
        conn.commit()
        print("✓ Dropped retargeting_jobs table")
    except sqlite3.Error as e:
        print(f"✗ Downgrade failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("Running migration 003: Create retargeting_jobs table")
    print("=" * 60)
    upgrade()
    print("=" * 60)
    print("\nTo verify, check that the table exists:")
    print("  sqlite3 unirig_ui.db '.schema retargeting_jobs'")
    print("\nTo rollback:")
    print("  python -c 'from migrations.003_create_retargeting_jobs import downgrade; downgrade()'")
