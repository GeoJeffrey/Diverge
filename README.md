# Diverge — Financial Narrative Intelligence System

A production-grade financial narrative intelligence and sentiment tracking platform with real-time multi-index computation, coordination and trust integrity scoring, post-level explainability traces, and a modern dual-mode React dashboard.

---

## 📁 Repository Structure

```text
Diverge/
├── docs/                      # Shared API contract & architecture specifications
│   ├── openapi.json           # Frozen OpenAPI 3.0 specification
│   ├── API_CONTRACT_NOTES.md  # Specification freeze notes & endpoint contract
│   └── architecture.md        # System architecture and multi-phase pipeline flow
├── src/diverge/               # Core Python application package
│   ├── api/                   # FastAPI application, routers, schemas, dependencies
│   │   └── routers/           # auth, health, tickers endpoints
│   ├── auth/                  # JWT Bearer tokens & bcrypt password hashing
│   ├── db/                    # SQLAlchemy engine, models, session management
│   ├── indices/               # Phase 3: Financial indices (CLI, VDI, CASSI, Rn, CIRG)
│   ├── integrity/             # Phase 4: Bot & inorganic coordination scoring
│   ├── aggregation/           # Phase 5: Calibrated composite aggregation
│   ├── explainability/        # Phase 6: Post-level reasoning traces & lineage
│   ├── features/              # Phase 2: NLP sentiment, irony, periodicity features
│   └── scrapers/              # Phase 1: Ingest scrapers (Reddit, StockTwits, Telegram, RSS, Trends)
├── frontend/                  # Modern React + Vite dashboard
│   ├── src/
│   │   ├── auth/              # AuthProvider and token session management
│   │   ├── components/        # UI components, IndexCard, TrustBadge, Layouts
│   │   ├── lib/               # apiFetch client, approved label mappings
│   │   ├── pages/             # Tickers, Advanced, Simple, Integrity, Explainability
│   │   └── routes.tsx         # Route configuration & authenticated route guards
│   ├── package.json           # Frontend dependencies & scripts
│   ├── vite.config.ts         # Vite build configuration
│   └── Dockerfile             # Multi-stage production Nginx container
├── migrations/                # Alembic database migrations for PostgreSQL
├── scripts/                   # Migration, database setup, and diagnostic utilities
├── docker-compose.yml         # Full-stack container orchestration
├── Dockerfile                 # Backend FastAPI container definition
├── run_server.py              # API server launcher
└── run_all.py                 # Pipeline runner (Scrapers -> Features -> Indices)
```

---

## 🛠️ Prerequisites

- **Python**: 3.10+ (Python 3.11 recommended)
- **Node.js**: 18+ (Node.js 20 recommended) & npm
- **Database**: PostgreSQL 14+ (or automatic SQLite fallback for offline execution)
- **Docker & Docker Compose** (optional, for containerized multi-service deployment)

---

## 🚀 Quick Start (Local Setup)

### 1. Backend & Database Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/GeoJeffrey/Diverge.git
   cd Diverge
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure Database**:
   - **PostgreSQL (Recommended)**: Set the connection string in your environment:
     ```powershell
     # Windows PowerShell
     $env:DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/diverge"
     ```
     ```bash
     # Linux / macOS
     export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/diverge"
     ```
     Apply database migrations (Note: Migrations run automatically on Railway container startup, but can also be applied manually):
     ```bash
     alembic upgrade head
     ```
     To run migrations against Railway PostgreSQL from your local terminal:
     ```bash
     DATABASE_URL="<your_railway_postgres_connection_url>" alembic upgrade head
     ```
   - **SQLite Fallback**: If `DATABASE_URL` is unset, Diverge automatically stores data in `data/diverge_raw.db`.

4. **Launch the API Server**:
   ```bash
   python run_server.py --port 8000 --reload
   ```
   - **API Health**: [http://localhost:8000/health](http://localhost:8000/health)
   - **Interactive API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **OpenAPI 3.0 Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

### 2. Frontend Setup (React + Vite)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   Copy `.env.example` to `.env` (or configure as needed):
   ```bash
   cp .env.example .env
   ```
   *Default: `VITE_API_BASE_URL=http://localhost:8000`* (set to `mock` for standalone offline fixture testing).

4. **Start the development server**:
   ```bash
   npm run dev
   ```
   Open **[http://localhost:5173](http://localhost:5173)** in your browser.

5. **Build for production**:
   ```bash
   npm run build
   ```

---

## 🐳 Docker Deployment

To spin up PostgreSQL, the FastAPI backend, and the React frontend in isolated containers:

```bash
docker compose up --build
```

- **Frontend App**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`

---

## 🧪 Verification & Test Suite

Run the full Python test suite:
```bash
pytest -v
```
*(63 passed unit and integration tests covering indices math, sentiment features, integrity scoring, and explainability).*

Run backend concurrency verification (20 concurrent requests):
```bash
python scripts/test_concurrency.py
```

Run comprehensive API smoke tests across all 7 core endpoints:
```bash
python scripts/smoke_test_api.py
```

---

## 📊 Core API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|:---:|
| `GET` | `/health` | Service health status and database connectivity | No |
| `GET` | `/tickers` | Monitored equities list with composite scores & trust badges | No |
| `GET` | `/ticker/{symbol}/simple` | Plain-language narrative synthesis card | No |
| `POST` | `/auth/signup` | Trader account registration | No |
| `POST` | `/auth/login` | Authentication and JWT Bearer token generation | No |
| `GET` | `/auth/me` | Authenticated user profile | **Yes** |
| `GET` | `/ticker/{symbol}` | Diagnostic view: all 5 financial indices, trust, and risk flags | **Yes** |
| `GET` | `/ticker/{symbol}/reasoning` | Post-level reasoning traces and driver categorization | **Yes** |

---

## 📈 Financial Indices Reference

Diverge computes 5 distinct narrative and sentiment indices adhering strictly to frozen labels and null guards:

1. **Contagion Core (Rn)**: Epidemiological viral reproduction rate of social narrative spread.
2. **Reality Check (CIRG)**: Statistical divergence between retail/consumer product reviews and market hype.
3. **Capitulation Signal (CLI)**: Panic density and stop-loss liquidation language across investor communities.
4. **Cross-Market Spillover (CASSI)**: Cross-asset sentiment transmission and retail focus spillover.
5. **Language Divergence (VDI)**: Sentiment spread between regional vernacular discussion and institutional English channels.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
