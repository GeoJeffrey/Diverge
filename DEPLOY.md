# Cloud Deployment Guide — Railway & Vercel

This guide outlines the exact, step-by-step procedure to deploy the Diverge system from scratch:
- **Database & Services (Railway)**: Managed PostgreSQL, FastAPI Backend API, and continuous Background Scraper Worker.
- **Frontend Dashboard (Vercel)**: React + Vite Single Page Application (SPA).

---

## 🏛️ Architecture Overview

```text
[ Vercel (Frontend SPA) ] 
       │  (HTTPS API Requests)
       ▼
[ Railway (FastAPI Backend) ] ── (Automatic Migrations on Start)
       │                                     ▲
       ├── [ Railway Managed PostgreSQL ] ───┘
       │            ▲
[ Railway (Scraper Worker) ] ── (Runs every 4h via APScheduler)
```

---

## 🚂 Part 1: Railway Deployment (Postgres + Backend API + Worker)

### Step 1: Create a Railway Project
1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** $\rightarrow$ **Provision PostgreSQL**.
3. Once provisioned, Railway automatically provides the `DATABASE_URL` environment variable to attached services.

### Step 2: Deploy Backend API Service
1. In the same project, click **Create** $\rightarrow$ **GitHub Repo** $\rightarrow$ select your `Diverge` repository.
2. Railway detects the root `Dockerfile` and `railway.json`.
3. In **Settings** $\rightarrow$ **Networking**, click **Generate Domain** (e.g., `https://diverge-api-production.up.railway.app`).
4. In **Variables**, configure:

| Variable Name | Value | Description |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Auto-referenced from the PostgreSQL service |
| `DIVERGE_SECRET_KEY` | *(Generate a strong 32+ char secret)* | JWT signing secret for auth tokens |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | Production Vercel domain (comma-separated if multiple) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT token lifespan |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifespan |

*Note: Railway will inject `PORT` dynamically, which the backend reads automatically.*

### Step 3: Deploy Scraper Worker Service
To keep data ingested on schedule without blocking or overloading the HTTP API:
1. In the same Railway project, click **Create** $\rightarrow$ **GitHub Repo** $\rightarrow$ select `Diverge` again.
2. Rename this service to **`diverge-scraper-worker`**.
3. Go to **Settings** $\rightarrow$ **Deploy**:
   - Change **Custom Start Command** to:
     ```bash
     python -m diverge.pipeline_scheduler --hours 4 --run-now
     ```
4. In **Variables**, link to the shared database:

| Variable Name | Value | Description |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Shared PostgreSQL instance |

5. Click **Deploy**. This worker will execute an immediate ingestion pass and then run continuously every 4 hours, logging all runs to stdout.

---

## ⚡ Part 2: Vercel Deployment (Frontend)

### Step 1: Import Project to Vercel
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** $\rightarrow$ **Project** $\rightarrow$ Import your `Diverge` repository.

### Step 2: Configure Build Settings
In the Vercel project configuration screen:
- **Framework Preset**: `Vite`
- **Root Directory**: Click **Edit** and choose `frontend`.
- **Build Command**: `npm run build` (detected automatically)
- **Output Directory**: `dist` (detected automatically)

### Step 3: Configure Environment Variables
Add the following environment variable:

| Key | Value | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | `https://diverge-api-production.up.railway.app` | Use the live Railway API domain from Part 1 |

### Step 4: Deploy & Verify
1. Click **Deploy**.
2. Once the deployment finishes, copy your production Vercel domain (e.g. `https://diverge.vercel.app`).
3. Return to Railway $\rightarrow$ **Backend API** $\rightarrow$ **Variables** $\rightarrow$ ensure `ALLOWED_ORIGINS` includes your Vercel URL:
   ```env
   ALLOWED_ORIGINS=https://diverge.vercel.app
   ```
4. Visit `https://diverge.vercel.app`:
   - Register a trader account at `/signup`.
   - Browse monitored equities at `/tickers`.
   - View composite narrative signals and explainability traces.

---

## 🔍 Verification Checklist

After completing both deployments:
1. **API Health**: `curl https://<your-railway-domain>/health` should return `{"status":"healthy","database":"connected"}`.
2. **CORS Check**: Inspect Network tab in your browser on Vercel — confirm no CORS blocking on `/tickers` or `/auth/login`.
3. **Database Tables**: Railway's PostgreSQL table viewer should show populated `users`, `raw_posts`, `text_features`, and `ticker_window_metrics`.
4. **Worker Logs**: Check Deploy Logs in `diverge-scraper-worker` on Railway to confirm `[AUDIT LOG] Scheduled job executed cleanly`.
