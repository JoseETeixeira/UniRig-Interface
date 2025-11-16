# Database Migrations

This directory contains database migration scripts for schema changes.

## Available Migrations

### 002_add_metadata_columns.py
Adds metadata columns to the jobs table:
- `vertex_count` (INTEGER)
- `bone_count` (INTEGER)
- `file_format` (VARCHAR)

### 003_create_retargeting_jobs.py
Creates the `retargeting_jobs` table for motion retargeting workflow:
- Tracks motion retargeting operations
- Links rigged models (jobs) with motion clips
- Stores retargeting status, progress, and results
- Includes skeleton compatibility information

## Running Migrations

### Automatic (Recommended)
The application automatically creates all tables on startup via `init_db()` in `database.py`. No manual migration needed for new deployments.

### Manual Migration
If you need to run migrations on an existing database:

```bash
# Navigate to backend directory
cd unirig-ui/backend

# Run specific migration
python -m app.db.migrations.003_create_retargeting_jobs

# Or run directly
python app/db/migrations/003_create_retargeting_jobs.py
```

## Verifying Schema

Check table structure:
```bash
sqlite3 unirig_ui.db '.schema retargeting_jobs'
```

List all tables:
```bash
sqlite3 unirig_ui.db '.tables'
```

## Rollback

To rollback a migration (drops the table):
```python
from app.db.migrations.003_create_retargeting_jobs import downgrade
downgrade()
```

**Warning:** Rollback will delete all data in the retargeting_jobs table.

## Creating New Migrations

1. Create a new file: `00X_description.py`
2. Implement `upgrade()` and `downgrade()` functions
3. Follow the pattern in existing migrations
4. Test both upgrade and downgrade paths
5. Document the migration in this README

## Schema Design Notes

### retargeting_jobs Table

**Purpose:** Tracks motion retargeting operations where animations from the motion dataset are transferred to rigged models.

**Columns:**
- `id`: UUID primary key
- `job_id`: Foreign key to jobs table (parent rigging job)
- `motion_clip_id`: Foreign key to motion_clips table (source animation)
- `status`: Current status (queued/processing/completed/failed)
- `progress`: Progress percentage (0-100)
- `result_path`: Path to retargeted animation file
- `error`: Error message if retargeting failed
- `skeleton_compatibility`: JSON object with compatibility details
- `created_at`: Timestamp when retargeting was requested
- `completed_at`: Timestamp when retargeting finished

**Indexes:**
- `idx_retargeting_job_id`: Fast lookup by parent job
- `idx_retargeting_status`: Fast filtering by status
- `idx_retargeting_job_status`: Composite index for job + status queries
- Additional indexes on primary key and foreign keys

**Relationships:**
- Belongs to Job (CASCADE delete - remove retargeting jobs when parent job deleted)
- References MotionClip (RESTRICT delete - prevent deleting clips with active retargeting jobs)
