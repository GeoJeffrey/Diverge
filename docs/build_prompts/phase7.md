# Phase 7 — Output Modes

Built the final user-facing layer over Phases 1-6 data (read-only, no new computation):
- **simple_mode.py**: `get_simple_view(ticker, window)` → verdict label, why sentence, trust label.
- **advanced_mode.py**: `get_advanced_view(ticker, window)` → full indices dict + coordination + phylogeny context + traces.
- **mode_api.py**: HTTP handler functions called by `server.py`.
- **server.py**: BaseHTTPRequestHandler serving `/api/tickers`, `/api/simple`, `/api/advanced`, `/api/phylogeny`, and static files.
- **ui/simple.html** + **ui/advanced.html**: Frontend prototype pages using shared `styles.css` and `app.js`.
