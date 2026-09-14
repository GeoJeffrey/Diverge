"""
app.py

Main FastAPI application for the Diverge API.
Mounts all routers and configures CORS, title, and version per the frozen openapi.json contract.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command

from .routers import health, auth, tickers
from ..db.base import Base, engine
from ..db import models  # Ensure all SQLAlchemy models are registered

logger = logging.getLogger("diverge.api")


def run_db_migrations() -> None:
    """Execute Alembic migrations up to head automatically on startup, falling back to create_all."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    ini_path = project_root / "alembic.ini"
    migrations_dir = project_root / "migrations"

    if ini_path.exists() and migrations_dir.exists():
        try:
            alembic_cfg = Config(str(ini_path))
            alembic_cfg.set_main_option("script_location", str(migrations_dir))
            logger.info("Running automatic Alembic migrations on startup...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Alembic migrations applied successfully.")
            return
        except Exception as exc:
            logger.warning(f"Alembic migration failed on startup ({exc}), attempting Base.metadata.create_all fallback...")

    # Fallback to direct table creation if Alembic config is unreachable
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created or verified via Base.metadata.create_all().")
    except Exception as exc:
        logger.error(f"Failed to verify/create database schema on startup: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is up-to-date
    run_db_migrations()
    yield


app = FastAPI(
    title="Diverge API",
    version="1.0.0",
    description=(
        "Frozen HTTP API contract for Diverge financial narrative intelligence, "
        "sentiment tracking, multi-index calculation, integrity scoring, "
        "and reasoning trace explainability."
    ),
    lifespan=lifespan,
)

# Explicit CORS origins (disallowing wildcard when credentials/auth tokens are involved)
DEFAULT_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # React / Next.js dev server
    "http://127.0.0.1:3000",
    "https://diverge.ai",     # Production domain
    "https://app.diverge.ai", # Production app subdomain
]

env_cors = os.getenv("ALLOWED_ORIGINS") or os.getenv("CORS_ORIGINS")
if env_cors:
    extra_origins = [o.strip() for o in env_cors.split(",") if o.strip()]
    ALLOWED_ORIGINS = list(dict.fromkeys(DEFAULT_ORIGINS + extra_origins))
else:
    ALLOWED_ORIGINS = DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(tickers.router)


@app.get("/", include_in_schema=False)
def root_index():
    """Root entrypoint linking to interactive documentation."""
    return {
        "name": "Diverge API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health",
        "dashboard_ui": "http://localhost:5173",
    }


def custom_openapi():
    """Guarantee exact zero-drift alignment with the frozen openapi.json specification."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "openapi.json"
    if openapi_path.exists():
        with open(openapi_path, "r", encoding="utf-8") as f:
            app.openapi_schema = json.load(f)
            return app.openapi_schema
    return super(FastAPI, app).openapi()


import json
from pathlib import Path
app.openapi = custom_openapi
