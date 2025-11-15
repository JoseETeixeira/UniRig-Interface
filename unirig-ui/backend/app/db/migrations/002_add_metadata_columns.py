"""
Database migration: Add metadata columns to jobs table
Migration 002: Add vertex_count, bone_count, file_format columns
"""

from sqlalchemy import Integer, String, Column
from app.db.database import engine
from app.db.models import Base
import sqlite3


def upgrade():
    """Add metadata columns to jobs table"""
    conn = sqlite3.connect('data/unirig.db')
    cursor = conn.cursor()
    
    try:
        # Add vertex_count column
        cursor.execute('ALTER TABLE jobs ADD COLUMN vertex_count INTEGER')
        print("✓ Added vertex_count column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠ vertex_count column already exists")
        else:
            raise
    
    try:
        # Add bone_count column
        cursor.execute('ALTER TABLE jobs ADD COLUMN bone_count INTEGER')
        print("✓ Added bone_count column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠ bone_count column already exists")
        else:
            raise
    
    try:
        # Add file_format column
        cursor.execute('ALTER TABLE jobs ADD COLUMN file_format VARCHAR(10)')
        print("✓ Added file_format column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠ file_format column already exists")
        else:
            raise
    
    conn.commit()
    conn.close()
    print("✓ Migration 002 completed successfully")


def downgrade():
    """Remove metadata columns from jobs table"""
    # SQLite doesn't support DROP COLUMN directly
    # Would require creating new table and copying data
    print("⚠ Downgrade not implemented for SQLite")
    print("  To revert: recreate database or manually drop columns")


if __name__ == "__main__":
    print("Running migration 002: Add metadata columns")
    upgrade()
