"""
base.py

Database connection and session handling for Diverge.
Supports PostgreSQL (via DATABASE_URL environment variable) with seamless
SQLite fallback for local execution and offline testing.
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "data" / "diverge_raw.db"

# Database URL from environment or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
