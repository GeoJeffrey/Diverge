"""
server.py

Diverge Phase 1 + Phase 2 Web Dashboard Server.
Provides REST API endpoints and serves the full multi-tab dashboard.

Usage:
    python server.py [--port 8000]
"""

import argparse
import json
import sqlite3
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from diverge_scraper import config, storage
from diverge_scraper.main import run_pipeline

BASE_DIR = Path(__file__).parent
DB_PATH = config.DB_PATH
HTML_FILE = BASE_DIR / "dashboard.html"


class DivergeDashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html_content, status=200):
        body = html_content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        params = urllib.parse.parse_qs(parsed_url.query)

        # ── Serve HTML ─────────────────────────────────────────
        if path in ("/", "/dashboard.html"):
            if HTML_FILE.exists():
                with open(HTML_FILE, "r", encoding="utf-8") as f:
                    self.send_html(f.read())
            else:
                self.send_html("<h1>dashboard.html missing</h1>", status=404)
            return

        # ── /api/stats ─────────────────────────────────────────
        if path == "/api/stats":
            conn = sqlite3.connect(DB_PATH)
            storage.get_connection(DB_PATH)  # ensure tables exist

            platform_counts = dict(conn.execute(
                "SELECT platform, COUNT(*) FROM raw_posts GROUP BY platform"
            ).fetchall())
            total_raw = sum(platform_counts.values())

            def safe_count(table):
                try:
                    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                except Exception:
                    return 0

            sentiment_dist = dict(conn.execute(
                "SELECT sentiment_label, COUNT(*) FROM text_features GROUP BY sentiment_label"
            ).fetchall() if safe_count("text_features") > 0 else [])

            cap_count = conn.execute(
                "SELECT COUNT(*) FROM text_features WHERE capitulation_flag = 1"
            ).fetchone()[0] if safe_count("text_features") > 0 else 0

            sarcasm_count = conn.execute(
                "SELECT COUNT(*) FROM text_features WHERE is_sarcastic = 1"
            ).fetchone()[0] if safe_count("text_features") > 0 else 0

            conn.close()
            self.send_json({
                "total_raw_posts": total_raw,
                "platform_counts": platform_counts,
                "tickers": list(config.TICKERS.keys()),
                "retention_days": config.RETENTION_DAYS,
                "phase2": {
                    "post_timing": safe_count("post_timing"),
                    "ticker_time_bins": safe_count("ticker_time_bins"),
                    "text_features": safe_count("text_features"),
                    "periodicity_stats": safe_count("periodicity_stats"),
                    "sentiment_distribution": sentiment_dist,
                    "capitulation_posts": cap_count,
                    "sarcastic_posts": sarcasm_count,
                },
                "phase3": {
                    "index_values": safe_count("index_values"),
                    "consumer_sentiment": safe_count("consumer_sentiment"),
                },
                "phase4": {
                    "coordination_scores": safe_count("coordination_scores"),
                },
                "phase5": {
                    "ticker_window_metrics": safe_count("ticker_window_metrics"),
                },
                "phase6": {
                    "reasoning_trace": safe_count("reasoning_trace"),
                    "duplicate_pairs": safe_count("duplicate_pairs"),
                    "narrative_phylogeny": safe_count("narrative_phylogeny"),
                },
            })
            return

        # ── Phase 7 Mode API Endpoints ────────────────────────────
        if path.startswith("/api/simple/"):
            parts = [p for p in path.split("/") if p]
            # /api/simple/<ticker>/<window_start_utc>
            if len(parts) >= 4:
                t = parts[2]
                w = unquote("/".join(parts[3:]))
                from diverge_scraper import mode_api
                status, data = mode_api.handle_get_simple(t, w, db_path=DB_PATH)
                self.send_json(data, status=status)
                return

        if path.startswith("/api/advanced/"):
            parts = [p for p in path.split("/") if p]
            # /api/advanced/<ticker>/<window_start_utc>
            if len(parts) >= 4:
                t = parts[2]
                w = unquote("/".join(parts[3:]))
                from diverge_scraper import mode_api
                status, data = mode_api.handle_get_advanced(t, w, db_path=DB_PATH)
                self.send_json(data, status=status)
                return

        if path == "/api/tickers":
            from diverge_scraper import mode_api
            status, data = mode_api.handle_get_tickers(db_path=DB_PATH)
            self.send_json(data, status=status)
            return

        if path.startswith("/api/phylogeny/"):
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 3:
                t = parts[2]
                from diverge_scraper import mode_api
                status, data = mode_api.handle_get_phylogeny(t, db_path=DB_PATH)
                self.send_json(data, status=status)
                return

        # ── /api/reasoning-trace (Phase 6 Audit Trail) ────────
        if path.startswith("/api/reasoning-trace"):
            query_params = parse_qs(parsed.query)
            ticker = query_params.get("ticker", [""])[0]
            wstart = query_params.get("window_start", [""])[0]
            from diverge_scraper import render_prototype
            panel_data = render_prototype.reasoning_trace_panel(ticker, wstart, db_path=DB_PATH)
            self.send_json(panel_data)
            return

        # ── /api/narrative-phylogeny (Phase 6 Narrative Lineage) ─
        if path.startswith("/api/narrative-phylogeny"):
            query_params = parse_qs(parsed.query)
            ticker = query_params.get("ticker", [""])[0]
            from diverge_scraper import render_prototype
            tree_data = render_prototype.narrative_phylogeny_tree(ticker, db_path=DB_PATH)
            self.send_json(tree_data)
            return

        # ── /api/composite-metrics ──────────────────────────────
        if path.startswith("/api/composite-metrics"):
            query_params = parse_qs(parsed.query)
            ticker_filter = query_params.get("ticker", [None])[0]

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM ticker_window_metrics WHERE 1=1"
            params = []
            if ticker_filter and ticker_filter.upper() != "ALL":
                query += " AND ticker = ?"
                params.append(ticker_filter.upper())
            query += " ORDER BY ticker ASC, window_start_utc DESC LIMIT 200"

            try:
                rows = conn.execute(query, params).fetchall()
                data = [dict(r) for r in rows]
            except Exception as e:
                data = []
            conn.close()
            self.send_json({"metrics": data})
            return

        # ── /api/posts (raw_posts + joined text_features) ──────
        if path == "/api/posts":
            ticker  = params.get("ticker",   [None])[0]
            platform = params.get("platform", [None])[0]
            search  = params.get("search",   [None])[0]
            sentiment = params.get("sentiment", [None])[0]
            limit   = int(params.get("limit", [100])[0])
            offset  = int(params.get("offset", [0])[0])

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row

            query = """
                SELECT rp.post_id, rp.account_id, rp.timestamp_utc, rp.community,
                       rp.ticker, rp.raw_text, rp.upvotes, rp.platform, rp.scraped_at,
                       tf.sentiment_score, tf.sentiment_label, tf.capitulation_flag,
                       tf.capitulation_confidence, tf.is_sarcastic,
                       tf.irony_adjusted_sentiment, tf.conviction_hedge_ratio, tf.language
                FROM raw_posts rp
                LEFT JOIN text_features tf ON rp.post_id = tf.post_id
                WHERE 1=1
            """
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND rp.ticker = ?"
                args.append(ticker.upper())
            if platform and platform.lower() != "all":
                query += " AND rp.platform = ?"
                args.append(platform.lower())
            if search:
                pat = f"%{search}%"
                query += " AND (rp.raw_text LIKE ? OR rp.account_id LIKE ? OR rp.community LIKE ?)"
                args.extend([pat, pat, pat])
            if sentiment and sentiment.lower() != "all":
                query += " AND tf.sentiment_label = ?"
                args.append(sentiment.lower())

            total_row = conn.execute(
                "SELECT COUNT(*) FROM (" + query + ")", args
            ).fetchone()[0]

            query += " ORDER BY rp.scraped_at DESC LIMIT ? OFFSET ?"
            args.extend([limit, offset])

            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"posts": [dict(r) for r in rows], "total": total_row, "count": len(rows)})
            return

        # ── /api/text-features ─────────────────────────────────
        if path == "/api/text-features":
            ticker   = params.get("ticker",    [None])[0]
            sentiment = params.get("sentiment", [None])[0]
            cap_only = params.get("capitulation", ["0"])[0] == "1"
            limit    = int(params.get("limit", [100])[0])
            offset   = int(params.get("offset", [0])[0])

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = """
                SELECT tf.post_id, rp.ticker, rp.platform, rp.account_id,
                       rp.timestamp_utc, rp.raw_text,
                       tf.sentiment_score, tf.sentiment_label, tf.capitulation_flag,
                       tf.capitulation_confidence, tf.is_sarcastic,
                       tf.irony_adjusted_sentiment, tf.conviction_hedge_ratio,
                       tf.language, tf.computed_at
                FROM text_features tf
                JOIN raw_posts rp ON tf.post_id = rp.post_id
                WHERE 1=1
            """
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND rp.ticker = ?"
                args.append(ticker.upper())
            if sentiment and sentiment.lower() != "all":
                query += " AND tf.sentiment_label = ?"
                args.append(sentiment.lower())
            if cap_only:
                query += " AND tf.capitulation_flag = 1"

            total_row = conn.execute("SELECT COUNT(*) FROM (" + query + ")", args).fetchone()[0]
            query += " ORDER BY rp.timestamp_utc DESC LIMIT ? OFFSET ?"
            args.extend([limit, offset])
            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"features": [dict(r) for r in rows], "total": total_row, "count": len(rows)})
            return

        # ── /api/timing ────────────────────────────────────────
        if path == "/api/timing":
            ticker = params.get("ticker", [None])[0]
            limit  = int(params.get("limit", [100])[0])
            offset = int(params.get("offset", [0])[0])

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = """
                SELECT pt.post_id, pt.ticker, pt.timestamp_utc, pt.delta_seconds,
                       pt.is_first_mention, pt.computed_at, rp.platform, rp.account_id
                FROM post_timing pt
                JOIN raw_posts rp ON pt.post_id = rp.post_id
                WHERE 1=1
            """
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND pt.ticker = ?"
                args.append(ticker.upper())

            total_row = conn.execute("SELECT COUNT(*) FROM (" + query + ")", args).fetchone()[0]
            query += " ORDER BY pt.timestamp_utc DESC LIMIT ? OFFSET ?"
            args.extend([limit, offset])
            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"timing": [dict(r) for r in rows], "total": total_row})
            return

        # ── /api/time-bins ─────────────────────────────────────
        if path == "/api/time-bins":
            ticker = params.get("ticker", [None])[0]
            limit  = int(params.get("limit", [200])[0])

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = "SELECT ticker, bin_start_utc, post_count FROM ticker_time_bins WHERE 1=1"
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND ticker = ?"
                args.append(ticker.upper())
            query += " ORDER BY bin_start_utc DESC LIMIT ?"
            args.append(limit)
            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"bins": [dict(r) for r in rows]})
            return

        # ── /api/periodicity ───────────────────────────────────
        if path == "/api/periodicity":
            ticker = params.get("ticker", [None])[0]
            limit  = int(params.get("limit", [100])[0])
            offset = int(params.get("offset", [0])[0])

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = """
                SELECT ticker, window_start_utc, window_end_utc,
                       ks_statistic, acf_peak_lag_minutes, acf_peak_strength,
                       dominant_frequency_minutes, onset_dispersion_index
                FROM periodicity_stats WHERE 1=1
            """
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND ticker = ?"
                args.append(ticker.upper())
            total_row = conn.execute("SELECT COUNT(*) FROM (" + query + ")", args).fetchone()[0]
            query += " ORDER BY window_start_utc DESC LIMIT ? OFFSET ?"
            args.extend([limit, offset])
            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"periodicity": [dict(r) for r in rows], "total": total_row})
            return

        # ── /api/index-values (Phase 3 Financial Indices) ─────
        if path == "/api/index-values":
            ticker = params.get("ticker", [None])[0]

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            query = """
                SELECT ticker, window_start_utc, window_end_utc,
                       rn, rn_confidence, cirg, cli, cassi, vdi, computed_at
                FROM index_values WHERE 1=1
            """
            args = []
            if ticker and ticker.upper() != "ALL":
                query += " AND ticker = ?"
                args.append(ticker.upper())

            query += " ORDER BY ticker ASC, window_start_utc DESC"
            rows = conn.execute(query, args).fetchall()
            conn.close()
            self.send_json({"indices": [dict(r) for r in rows], "total": len(rows)})
            return

        self.send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        if self.path == "/api/run-scraper":
            try:
                run_pipeline()
                counts = storage.count_by_platform(db_path=DB_PATH)
                self.send_json({"status": "success", "message": "Scraper pipeline executed.", "counts": counts})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
        elif self.path == "/api/run-phase2":
            try:
                from diverge_scraper import timing_features, periodicity_analysis, text_features
                t = timing_features.run()
                p = periodicity_analysis.run()
                tf = text_features.run()
                self.send_json({"status": "success", "timing_rows": t, "periodicity_rows": p, "text_rows": tf})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
        elif self.path == "/api/run-phase3":
            try:
                import run_phase3
                inserted = run_phase3.run(db_path=DB_PATH)
                self.send_json({"status": "success", "message": f"Phase 3 completed ({inserted} index_values rows)."})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
        elif self.path == "/api/run-phase5":
            try:
                import run_phase5
                inserted = run_phase5.run(db_path=DB_PATH)
                self.send_json({"status": "success", "message": f"Phase 5 completed ({inserted} ticker_window_metrics rows)."})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
        elif self.path == "/api/run-phase6":
            try:
                import run_phase6
                inserted = run_phase6.run(db_path=DB_PATH)
                self.send_json({"status": "success", "message": f"Phase 6 completed ({inserted} reasoning_trace rows)."})
            except Exception as e:
                self.send_json({"status": "error", "message": str(e)}, status=500)
        else:
            self.send_json({"error": "Endpoint not found"}, status=404)


def run_server(port=8000):
    httpd = HTTPServer(("", port), DivergeDashboardHandler)
    print(f"=======================================================")
    print(f"Diverge Phase 1+2 Dashboard  ->  http://localhost:{port}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(port=args.port)
