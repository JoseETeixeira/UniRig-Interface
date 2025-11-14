"""
Database connection and initialization for SQLite.
Provides SQLAlchemy engine, session factory, and database initialization.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

# SQLite database file location (use env var if available, otherwise default)
DATABASE_PATH = os.getenv("DATABASE_PATH", "./unirig_ui.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
    echo=False  # Set to True for SQL query logging during development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def init_db():
    """
    Initialize the database.
    Creates all tables defined in SQLAlchemy models if they don't exist.
    Should be called on application startup.
    """
    from app.db import models  # Import models to register them with Base
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db() -> Session:
    """
    Dependency function to get database session.
    Use with FastAPI's Depends() to inject database sessions into endpoints.
    
    Yields:
        Database session
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
