"""
Database models for eCademy application.

Uses SQLAlchemy with SQLite for storing run history and logs.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

Base = declarative_base()


class PipelineRun(Base):
    """Model for storing pipeline execution history."""

    __tablename__ = "pipeline_runs"
    __table_args__ = (
        # Composite index for efficient filtering by status and time
        {'sqlite_autoincrement': True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running", index=True)  # running, success, error

    # Pipeline parameters
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    sheet_id = Column(String(100), nullable=True)
    storage_backend = Column(String(20), nullable=True)  # sheets, excel

    # Results summary
    insights_count = Column(Integer, default=0)
    students_count = Column(Integer, default=0)
    teachers_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Relationships
    logs = relationship("RunLog", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PipelineRun(id={self.id}, job_id={self.job_id}, status={self.status})>"


class RunLog(Base):
    """Model for storing individual log messages from pipeline runs."""

    __tablename__ = "run_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    level = Column(String(10), nullable=False, default="info")  # info, warning, error
    message = Column(Text, nullable=False)

    # Relationships
    run = relationship("PipelineRun", back_populates="logs")

    def __repr__(self):
        return f"<RunLog(id={self.id}, run_id={self.run_id}, level={self.level})>"


class CampaignAnalysisHistory(Base):
    """Model for tracking campaign analysis history for date tracking."""

    __tablename__ = "campaign_analysis_history"
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(50), nullable=False, index=True)
    period = Column(String(50), nullable=False, index=True)  # "2025-01-01 - 2025-01-31"
    first_analysis_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    last_analysis_date = Column(String(10), nullable=True)  # YYYY-MM-DD або NULL
    analysis_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CampaignAnalysisHistory(campaign_id={self.campaign_id}, period={self.period}, count={self.analysis_count})>"


class SearchHistory(Base):
    """Model for storing search results from all 3 tabs (ADS, STUDENTS, TEACHERS)."""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    tab_type = Column(String(20), nullable=False, index=True)  # 'ads', 'students', 'teachers'
    results_count = Column(Integer, default=0, nullable=False)
    results_json = Column(Text, nullable=True)  # JSON string with results
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, period={self.start_date} - {self.end_date}, tab={self.tab_type}, count={self.results_count})>"
