# Diverge — Financial Narrative Intelligence System

A full-stack financial narrative intelligence and sentiment tracking platform with real-time multi-index computation, coordination/trust scoring, reasoning traces, and a modern dual-mode React dashboard.

---

## 📁 Repository Structure

```text
Diverge/
├── docs/                      # Shared API contract & architecture
│   ├── openapi.json           # Frozen OpenAPI 3.0 specification
│   ├── API_CONTRACT_NOTES.md  # Specification freeze notes & endpoints
│   └── architecture.md        # System design and pipeline phases
├── src/diverge/               # Backend Python application
│   ├── api/                   # FastAPI routers, schemas, dependencies
│   ├── auth/                  # JWT authentication & password hashing
│   ├── db/                    # SQLAlchemy models, sessions, PostgreSQL/SQLite engine
│   └── ...                    # Scrapers, NLP analysis, pipeline engines
├── frontend/                  # Modern React + Vite frontend application
│   ├── src/                   # React components, pages, routes, auth context
│   │   ├── auth/              # AuthProvider and session integration
│   │   ├── components/        # Index cards, trust badges, layouts
│   │   ├── lib/               # apiFetch client, labels, token session store
│   │   └── pages/             # Tickers, Advanced, Simple, Integrity, Explainability
│   ├── docs/                  # Synchronized openapi.json contract
│   ├── package.json           # Frontend dependencies & scripts
│   └── vite.config.ts         # Vite build configuration
├── migrations/                # Alembic database migrations
├── scripts/                   # Migration, database setup, and diagnostic utilities
├── docker-compose.yml         # Full-stack Docker orchestration
├── Dockerfile                 # Backend container definition
├── run_server.py              # API server launcher
└── run_all.py                 # Scraper and ingestion pipeline runner
```

---

## 🛠️ Prerequisites

- **Python**: 3.10+ (Python 3.11 recommended)
- **Node.js**: 18+ (Node.js 20 recommended) & npm
- **Database**: PostgreSQL 14+ (or SQLite fallback for offline testing)
- **Docker & Docker Compose** (optional, for containerized deployment)

---

## 🚀 Local Development Setup

### 1. Database Setup

#### Option A: PostgreSQL (Recommended)
Set the `DATABASE_URL` environment variable:

```powershell
# Windows PowerShell
$env:DATABASE_URL="postgresql+psycopg2://postgres@localhost:5432/diverge"
```

```bash
# Linux / macOS
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/diverge"
```

Run database migrations:
```bash
alembic upgrade head
```

#### Option B: SQLite Fallback
If `DATABASE_URL` is omitted, the backend automatically falls back to `data/diverge_raw.db`.

---

### 2. Backend Setup (FastAPI)

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Launch API Server**:
   ```bash
   python run_server.py --reload --port 8000
   ```

3. **Verify backend**:
   - Health Check: `http://localhost:8000/health`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Frozen OpenAPI Schema: `http://localhost:8000/openapi.json`

---

### 3. Frontend Setup (React + Vite)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Environment Configuration**:
   Create or verify `.env` in `frontend/`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
   *(Set `VITE_API_BASE_URL=mock` for offline mock testing).*

4. **Launch Vite Development Server**:
   ```bash
   npm run dev
   ```
   Access the dashboard at **`http://localhost:5173`**.

5. **Production Build**:
   ```bash
   npm run build
   ```

---

## 🐳 Docker Deployment

To launch the complete stack (PostgreSQL + FastAPI backend + React/Nginx frontend) in one command:

```bash
docker compose up --build
```

- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`

---

## 🧪 Verification & Smoke Checks

To verify all 7 endpoints against the live backend and schema contract:

1. `POST /auth/signup` — Create real trader account
2. `POST /auth/login` — Authenticate and obtain JWT Bearer tokens
3. `GET /auth/me` — Retrieve verified user profile
4. `GET /tickers` — Public market list across 16 monitored equities
5. `GET /ticker/{symbol}` — Protected Advanced mode multi-index view
6. `GET /ticker/{symbol}/simple` — Public Simple mode narrative card
7. `GET /ticker/{symbol}/reasoning` — Protected post-level explainability traces

Run frontend type check & production build:
```bash
cd frontend && npm run build
```
