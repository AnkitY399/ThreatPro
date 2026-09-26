"""
ThreatPro - Database Engine
SQLAlchemy async setup with SQLite backend for hackathon deployment.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import json
import os

from .config import settings

# Create engine with SQLite optimizations
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Enable WAL mode for SQLite for better concurrent access
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables from SQLAlchemy models."""
    from .models.schemas import (
        TranscriptRecord,
        ThreatAlert,
        CurrencyScanResult,
        TransactionRecord,
        GeoLocation,
        PatrolRoute,
    )
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables (useful for reseeding)."""
    Base.metadata.drop_all(bind=engine)


def reseed_db():
    """Drop and recreate database with fresh seed data."""
    drop_db()
    init_db()
    from .demos.seed_data import seed_all
    seed_all()