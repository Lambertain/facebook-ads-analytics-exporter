"""
Database connection and session management for eCademy.

Provides SQLAlchemy engine and session factory for SQLite database.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base

# Database file location
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./ecademy.db")

# Create engine with SQLite-specific configuration
engine = create_engine(
    DB_PATH,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for SQL query logging during development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    """
    Context manager for database sessions.

    Usage:
        with get_db() as db:
            db.query(PipelineRun).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Dependency for FastAPI endpoints.

    Usage:
        @app.get("/api/runs")
        def get_runs(db: Session = Depends(get_db_session)):
            return db.query(PipelineRun).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
