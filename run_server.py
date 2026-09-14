"""
run_server.py

Diverge API Server Launcher.
Starts the FastAPI application via Uvicorn on port 8000.

Usage:
    python run_server.py [--port 8000] [--reload]
"""

import argparse
import sys
from pathlib import Path

# Ensure package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Diverge API Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
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

