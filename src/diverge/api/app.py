"""
app.py

Main FastAPI application for the Diverge API.
Mounts all routers and configures CORS, title, and version per the frozen openapi.json contract.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, auth, tickers

app = FastAPI(
    title="Diverge API",
    version="1.0.0",
    description=(
        "Frozen HTTP API contract for Diverge financial narrative intelligence, "
        "sentiment tracking, multi-index calculation, integrity scoring, "
        "and reasoning trace explainability."
    ),
)

# Explicit CORS origins (disallowing wildcard when credentials/auth tokens are involved)
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # React / Next.js dev server
    "http://127.0.0.1:3000",
    "https://diverge.ai",     # Production domain
    "https://app.diverge.ai", # Production app subdomain
]

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
