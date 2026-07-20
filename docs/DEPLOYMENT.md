<div align="center">

# 🚀 SureFlow AI — Deployment Guide

### Deploy to Production on Render + Neo4j AuraDB + NeonDB

![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![Neo4j AuraDB](https://img.shields.io/badge/Neo4j_AuraDB-4581C3?style=for-the-badge&logo=neo4j&logoColor=white)
![NeonDB](https://img.shields.io/badge/NeonDB_Postgres-00E5CC?style=for-the-badge&logo=postgresql&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

</div>

---

## 📋 What This Guide Covers

This guide deploys the **full SureFlow AI backend** to production:

| Component | Where | Free? |
|---|---|---|
| **FastAPI Backend** | Render (Docker) | ✅ Free tier |
| **PostgreSQL + pgvector** | NeonDB | ✅ Already hosted |
| **Neo4j Knowledge Graph** | Neo4j AuraDB | ✅ Free tier |
| **Frontend** | Vercel | ✅ Free tier |

> **Note on Ollama:** Render has no GPU. Since all six AI agents already use **Gemini 2.5 Flash** as the primary model, Ollama is only a fallback — the app works fully without it in production.

---

## 🗺️ Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                      PRODUCTION STACK                       │
│                                                             │
│  ┌──────────────┐    REST/SSE    ┌──────────────────────┐   │
│  │   Vercel     │◄─────────────►│   Render (Docker)    │   │
│  │  (Next.js)   │               │   FastAPI Backend    │   │
│  └──────────────┘               └──────────┬───────────┘   │
│                                            │               │
│                          ┌─────────────────┼─────────────┐ │
│                          │                 │             │ │
│                   ┌──────▼──────┐  ┌───────▼──────┐     │ │
│                   │   NeonDB    │  │  Neo4j Aura  │     │ │
│                   │  Postgres   │  │  Knowledge   │     │ │
│                   │  +pgvector  │  │    Graph     │     │ │
│                   └─────────────┘  └──────────────┘     │ │
│                                                         │ │
│                          ┌──────────────┐               │ │
│                          │ Gemini 2.5   │               │ │
│                          │  Flash API   │               │ │
│                          └──────────────┘               │ │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1 — Set Up Neo4j AuraDB (Free Cloud Neo4j)

Render cannot self-host Neo4j. Use **Neo4j AuraDB Free** — no credit card required.

### 1.1 Create Your AuraDB Instance

1. Go to **[neo4j.com/cloud/aura](https://neo4j.com/cloud/platform/aura-graph-database/)**
2. Click **Start for Free** and create an account
3. Click **Create Instance** → choose **AuraDB Free**
4. Select a region close to your Render region (e.g. US East)
5. Click **Download credentials** — a `.txt` file with your connection details is downloaded

### 1.2 Save Your Credentials

From the downloaded file, note:

```env
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io   # ← TLS URI (NOT bolt://)
NEO4J_USER=neo4j
NEO4J_PASSWORD=<generated-password>               # ← Shown ONCE — save it now!
```

> ⚠️ **Critical:** The password is shown **only once** during creation. If you lose it, you must reset the database (all data is wiped).

### 1.3 Verify Connectivity (optional)

After the instance is ready (takes ~60 seconds), you can verify it from the **AuraDB console**:
- Click **Open** → Neo4j Browser
- Run: `RETURN 1` → should return `1`

---

## Step 2 — Prepare the Repository

### 2.1 Files Already Created for You

These files are already in the repo:

| File | Purpose |
|---|---|
| `backend/Dockerfile` | Docker image for Render (uses `${PORT:-8000}`) |
| `render.yaml` | Render Blueprint — auto-configures the service |
| `backend/.env.example` | Template for all environment variables |

### 2.2 Make Sure `.env` is Git-Ignored

Your secrets must **never** be committed. Verify:

```bash
# Should output: backend/.env
git check-ignore -v backend/.env
```

If it's not ignored, add to `.gitignore`:

```
backend/.env
```

### 2.3 Push to GitHub

```bash
git add render.yaml backend/Dockerfile
git commit -m "chore: add Render deployment config"
git push origin main
```

---

## Step 3 — Deploy the Backend on Render

### Option A — Blueprint (Recommended, 2 clicks)

1. Go to **[render.com](https://render.com)** → sign in
2. Click **New** → **Blueprint**
3. Connect your GitHub account and select `SohamVerse/sureflow-ai`
4. Render auto-detects `render.yaml` and shows the service to create
5. Click **Apply**

Render will start building the Docker image. The first build takes ~5–8 minutes.

### Option B — Manual Web Service

1. Go to Render → **New** → **Web Service**
2. Connect repo → select `main` branch
3. Fill in:
   - **Name:** `sureflow-backend`
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `./backend/Dockerfile`
   - **Docker Build Context Directory:** `./backend`
   - **Plan:** Starter (free)
4. Click **Create Web Service**

---

## Step 4 — Configure Environment Variables

After the service is created, go to **Dashboard → sureflow-backend → Environment**.

Add every variable in the table below. Variables marked 🔒 are secrets and must be entered manually.

### Required Variables

| Variable | Value | Notes |
|---|---|---|
| 🔒 `DATABASE_URL` | `postgresql://neondb_owner:...@...neon.tech/neondb?sslmode=require&channel_binding=require` | From your `.env` (NeonDB URL) |
| 🔒 `NEO4J_URI` | `neo4j+s://xxxxxxxx.databases.neo4j.io` | From AuraDB — use `neo4j+s://` NOT `bolt://` |
| `NEO4J_USER` | `neo4j` | |
| 🔒 `NEO4J_PASSWORD` | `<auradb-password>` | From AuraDB credentials file |
| 🔒 `GEMINI_API_KEY` | `your-gemini-key` | [Get one free](https://aistudio.google.com/apikey) |
| 🔒 `JWT_SECRET` | any long random string | e.g. `openssl rand -hex 32` |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `1440` | 24 hours |
| `DEBUG` | `false` | |
| `PYTHONUNBUFFERED` | `1` | |
| `PYTHONPATH` | `/app` | |

### CORS — Set After Frontend Deploy

```
CORS_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]
```

> **Tip:** Set this to `["*"]` temporarily while testing, then restrict it to your real frontend URL.

---

## Step 5 — Run Database Migrations

Once the service is deployed and healthy, run Alembic migrations.

### Via Render Shell

1. Render Dashboard → **sureflow-backend** → **Shell** tab
2. Run:

```bash
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, add pgvector
```

### Verify the Database

```bash
python -c "from core.database import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT 1')).scalar())"
# → 1
```

---

## Step 6 — Seed Demo Data

From the Render Shell:

```bash
# 2 plants, 12 equipment, locations, areas
python scripts/seed_industrial_data.py

# 3 demo users (CTO, Karnataka manager, Delhi manager)
python scripts/seed_users.py

# KPI snapshot history for the Trends dashboard
python scripts/seed_kpi_snapshots.py
```

All scripts are **idempotent** — safe to re-run.

---

## Step 7 — Verify Deployment

Check these endpoints after deploy (replace with your Render URL):

```bash
# Health check
curl https://sureflow-backend.onrender.com/
# → {"name":"CompanyOS","version":"2.0.0","status":"online","docs":"/docs"}

# API health
curl https://sureflow-backend.onrender.com/api/v1/health
# → {"status":"online","service":"SureFlow AI","version":"2.0.0"}

# Swagger UI (open in browser)
https://sureflow-backend.onrender.com/docs
```

---

## Step 8 — Deploy the Frontend on Vercel

```bash
cd frontend
```

1. Go to **[vercel.com](https://vercel.com)** → **New Project**
2. Import `SohamVerse/sureflow-ai` → set **Root Directory** to `frontend`
3. Framework: **Next.js** (auto-detected)
4. Add environment variable:

   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://sureflow-backend.onrender.com/api/v1` |

5. Click **Deploy**

### Update CORS on Render

After Vercel gives you a URL (e.g. `https://sureflow-ai-xyz.vercel.app`), go back to Render and update:

```
CORS_ORIGINS=["https://sureflow-ai-xyz.vercel.app","http://localhost:3000"]
```

Then trigger a redeploy: **Manual Deploy → Deploy latest commit**.

---

## 🔑 Demo Logins

| Role | Email | Password |
|---|---|---|
| 🌐 CTO (all plants) | `cto@sureflow.ai` | `Sureflow_CTO_2026!` |
| 🏭 Karnataka Manager | `karnataka@sureflow.ai` | `Sureflow_Plant_2026!` |
| 🏭 Delhi Manager | `delhi@sureflow.ai` | `Sureflow_Plant_2026!` |

---

## ⚠️ Render Free Tier Limitations

| Limitation | Impact | Fix |
|---|---|---|
| **Spins down after 15 min idle** | First request after idle = ~30s cold start | Upgrade to $7/mo Starter |
| **512 MB RAM** | Heavy PDF OCR may OOM on large files | Upgrade plan or compress files |
| **No GPU** | Ollama local models don't run | Already handled — Gemini is primary |
| **Ephemeral disk** | `uploads/` folder cleared on redeploy | Use Cloudflare R2 or AWS S3 |

---

## 🐛 Deployment Troubleshooting

<details>
<summary><b>Build fails: "could not find Dockerfile"</b></summary>

Check that **Dockerfile Path** is set to `./backend/Dockerfile` and **Build Context** is `./backend` in Render settings.

</details>

<details>
<summary><b>Neo4j connection refused on startup</b></summary>

- Make sure `NEO4J_URI` uses `neo4j+s://` (TLS), not `bolt://`
- AuraDB takes ~60 seconds to be ready after creation — wait and redeploy
- Verify credentials in Render environment tab match AuraDB credentials file

</details>

<details>
<summary><b>DATABASE_URL connection error</b></summary>

NeonDB requires `?sslmode=require` in the URL. Make sure the full URL is copied including the query string params.

</details>

<details>
<summary><b>Agents return empty responses / 500 errors</b></summary>

Check Render logs → likely `GEMINI_API_KEY` is missing or wrong:
```
Settings → Environment → verify GEMINI_API_KEY is set
```

</details>

<details>
<summary><b>CORS errors in the browser</b></summary>

Update `CORS_ORIGINS` in Render environment to include your exact Vercel URL (with `https://`, no trailing slash), then redeploy.

</details>

<details>
<summary><b>Alembic migration fails: "relation does not exist"</b></summary>

The pgvector extension may not be enabled on NeonDB. Run in Render Shell:
```bash
python -c "from core.database import engine; from sqlalchemy import text; engine.connect().execute(text('CREATE EXTENSION IF NOT EXISTS vector'))"
```
Then re-run `alembic upgrade head`.

</details>

<details>
<summary><b>Cold start is too slow</b></summary>

Free tier services spin down after 15 min idle. Options:
- Use a cron service to ping `/` every 10 minutes (UptimeRobot has a free tier)
- Upgrade to Render Starter ($7/mo) — always-on

</details>

---

## 📋 Complete Checklist

```
Backend
[ ] Neo4j AuraDB Free instance created
[ ] AuraDB credentials saved (URI, user, password)
[ ] render.yaml committed and pushed to GitHub
[ ] Render Web Service created (via Blueprint or manually)
[ ] All environment variables set in Render dashboard
[ ] Docker build succeeded (green in Render deploy logs)
[ ] Service responds at https://your-service.onrender.com/
[ ] alembic upgrade head run from Render Shell
[ ] Seed scripts run (industrial data + users + KPIs)

Frontend
[ ] Vercel project created from /frontend directory
[ ] NEXT_PUBLIC_API_URL set to Render backend URL
[ ] Frontend deployed and accessible
[ ] CORS_ORIGINS on Render updated with Vercel URL
[ ] Render redeployed after CORS update

Verification
[ ] GET / returns {"status":"online"}
[ ] /docs shows Swagger UI
[ ] Login works with demo credentials
[ ] Industrial dashboard loads with equipment data
[ ] Copilot responds to a query
```

---

## 🔗 Useful Links

| Resource | URL |
|---|---|
| Render Dashboard | https://render.com/dashboard |
| Neo4j AuraDB Console | https://console.neo4j.io |
| NeonDB Console | https://console.neon.tech |
| Gemini API Keys | https://aistudio.google.com/apikey |
| Vercel Dashboard | https://vercel.com/dashboard |

---

<div align="center">

**SureFlow AI** · [Main README](../README.md) · [Project Status](PROJECT_STATUS.md) · [Roadmap](ROADMAP.md)

</div>
