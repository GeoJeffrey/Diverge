# Diverge — Developer & Diagnostic Scripts

This directory contains utility scripts for database maintenance, migration, diagnostics, and test runs.

## 🛠️ Diagnostics & Testing

- **`smoke_test_api.py`**  
  Comprehensive end-to-end smoke test validating all 7 core API endpoints (`/health`, `/tickers`, `/ticker/{symbol}/simple`, `/auth/signup`, `/auth/login`, `/auth/me`, `/ticker/{symbol}`, `/ticker/{symbol}/reasoning`) and checking 401 unauthorized protection.
  ```bash
  python scripts/smoke_test_api.py
  ```

- **`test_concurrency.py`**  
  Spawns 20 concurrent worker requests against PostgreSQL through the FastAPI server to verify connection pooling and lack of database lock contention.
  ```bash
  python scripts/test_concurrency.py
  ```

- **`verify_pg_conn.py`**  
  Verifies connection to PostgreSQL, checks PostgreSQL version, and ensures the target `diverge` database exists.
  ```bash
  python scripts/verify_pg_conn.py
  ```

- **`validate_endpoints.py`**  
  Validates API responses against OpenAPI contracts.

- **`inspect_multi_tickers.py`**  
  Inspects dynamic calculation of financial indices across representative equities (`RELIANCE`, `WIPRO`, `LT`, etc.).

- **`diff_openapi.py`**  
  Compares live runtime OpenAPI schema with `docs/openapi.json` to guarantee zero drift.

---

## 🗄️ Database Operations

- **`migrate_sqlite_to_pg.py`**  
  Migrates legacy SQLite tables (`raw_posts`, `text_features`, `index_values`, etc.) into PostgreSQL.
  ```bash
  python scripts/migrate_sqlite_to_pg.py
  ```

- **`purge_seeded_data.py`**  
  Cleans out synthetic test accounts and resets state while preserving scraped market data.

- **`inspect_table_counts.py` / `check_sqlite_counts.py`**  
  Prints record counts across all pipeline tables.
