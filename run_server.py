"""
run_server.py

Phase 7 Server Launcher for Diverge.
Starts the HTTP server and API endpoints on port 8000, serving:
  - Main Dashboard (dashboard.html)
  - Simple Mode Prototype (ui/simple.html)
  - Advanced Mode Prototype (ui/advanced.html)
  - Phase 7 Mode API (/api/simple, /api/advanced, /api/tickers, /api/phylogeny)

Usage:
    python run_server.py [--port 8000]
"""

import sys
from pathlib import Path

# Ensure package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import server

if __name__ == "__main__":
    server.run(port=8000)

