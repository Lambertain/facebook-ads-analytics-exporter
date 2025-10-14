"""
Database connection and session management for eCademy.

Provides SQLAlchemy engine and session factory for SQLite database.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base

# Database configuration
# Пріоритет: POSTGRES_DATABASE_URL > DATABASE_URL > SQLite (для локальної розробки)
import logging
logger = logging.getLogger(__name__)

postgres_url = os.getenv("POSTGRES_DATABASE_URL")
database_url = os.getenv("DATABASE_URL")

if postgres_url:
    # Використовуємо PostgreSQL з Railway
    DB_PATH = postgres_url
    logger.info(f"Using PostgreSQL database: {postgres_url.split('@')[0]}@***")
    engine = create_engine(
        DB_PATH,
        pool_pre_ping=True,  # Перевірка з'єднання перед використанням
        echo=False,  # Set to True for SQL query logging during development
    )
elif database_url and database_url.startswith("postgresql"):
    # Використовуємо PostgreSQL з DATABASE_URL
    DB_PATH = database_url
    logger.info(f"Using PostgreSQL database from DATABASE_URL: {database_url.split('@')[0]}@***")
    engine = create_engine(
        DB_PATH,
        pool_pre_ping=True,
        echo=False,
    )
else:
    # Fallback до SQLite для локальної розробки
    DB_DIR = os.getenv("DATABASE_DIR", "/app/data" if os.path.exists("/app/data") else ".")
    os.makedirs(DB_DIR, exist_ok=True)  # Ensure directory exists
    DB_PATH = f"sqlite:///{DB_DIR}/ecademy.db"
    logger.info(f"Using SQLite database: {DB_PATH}")
    engine = create_engine(
        DB_PATH,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False,
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
