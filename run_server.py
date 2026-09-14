"""
run_server.py

Diverge API Server Launcher.
Starts the FastAPI application via Uvicorn on port 8000.

Usage:
    python run_server.py [--port 8000] [--reload]
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn


def main():
    default_port = int(os.getenv("PORT", "8000"))
    default_host = os.getenv("HOST", "0.0.0.0")

    parser = argparse.ArgumentParser(description="Diverge API Server")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to bind (default: {default_port})")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host to bind (default: {default_host})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print(f"Starting Diverge API on {args.host}:{args.port}")
    uvicorn.run(
        "diverge.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

