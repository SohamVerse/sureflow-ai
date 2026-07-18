# 🚀 Getting Started

Complete setup instructions for SureFlow OS. For the 5-minute version, see the
[root README](../README.md#-quick-start).

---

## Contents

- [Prerequisites](#prerequisites)
- [Environment configuration](#environment-configuration)
- [Path A — everything in Docker](#path-a--everything-in-docker-recommended)
- [Path B — backend on the host](#path-b--backend-on-the-host-hot-reload)
- [Seeding the demo data](#seeding-the-demo-data)
- [The frontend](#the-frontend)
- [Verifying it works](#verifying-it-works)
- [Common commands](#common-commands)

---

## Prerequisites

| Requirement | Why | Notes |
|---|---|---|
| **Docker Desktop** | Runs the backend + all infrastructure | Required for both paths |
| **Node.js 20+** | The frontend | Never containerized — always runs on the host |
| **Gemini API key** | All six agents | Free tier is sufficient — [get one](https://aistudio.google.com/apikey) |
| **Python 3.11+** | Only for Path B | Skip if using Docker |
| **Ollama** | Embeddings + offline fallback | Optional but recommended |

### Ollama setup (optional)

Ollama provides the embedding model for semantic search and a local fallback LLM for when Gemini
errors or hits quota:

```bash
ollama pull nomic-embed-text    # 768-dim embeddings — used by RAG
ollama pull llama3.2            # offline fallback model
```

The backend reaches Ollama on the host via `host.docker.internal`, which `docker-compose.yml`
already configures. Without Ollama, semantic search quality degrades but the app still runs.

---

## Environment configuration

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env`. **The only value you must set is your Gemini key:**

```env
GEMINI_API_KEY=your-key-here
```

Everything else has a working default in `backend/core/config.py`. Notable keys:

| Key | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | *(none)* | **Required.** Agents fail without it. |
| `DATABASE_URL` | Postgres | Point at the Docker instance on `:5433`, or a hosted Neon DB |
| `NEO4J_URI` | `bolt://localhost:7687` | Compose overrides this to `bolt://neo4j:7687` inside Docker |
| `JWT_SECRET` | `change-me-in-production` | **Change before deploying anywhere real** |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Compose overrides to `host.docker.internal` |
| `TESSERACT_CMD` / `POPPLER_PATH` | *(none)* | Windows-only, for Path B. Unnecessary in Docker. |

> ⚠️ `backend/.env` is gitignored — your key is never committed. This is also why a fresh clone has
> no `.env` and you must create one.

---

## Path A — everything in Docker *(recommended)*

The backend, the Temporal worker, and all infrastructure run as containers.

```bash
docker compose up -d
```

Nine services come up:

| Container | Port | Role |
|---|---|---|
| `sureflow-backend` | 8000 | FastAPI application |
| `sureflow-temporal-worker` | — | Durable workflow worker |
| `sureflow-postgres` | 5433 | Postgres 15 + pgvector |
| `sureflow-neo4j` | 7474 / 7687 | Knowledge graph |
| `sureflow-temporal` | 7233 | Workflow engine |
| `sureflow-temporal-ui` | 8085 | Workflow UI |
| `sureflow-jaeger` | 16686 | Trace UI |
| `sureflow-prometheus` | 9090 | Metrics |
| `sureflow-grafana` | 3001 | Dashboards |

Check they're healthy:

```bash
docker compose ps
docker compose logs -f backend
```

A healthy backend logs:

```
[OK] PostgreSQL tables ready (pgvector Knowledge Vault included).
[OK] Neo4j Industrial Knowledge Graph ready.
[READY] All agents standing by.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

After changing backend code, rebuild:

```bash
docker compose up -d --build
```

---

## Path B — backend on the host *(hot-reload)*

Useful when actively editing backend code. Run the **infrastructure** in Docker but the app locally.

**1. Stop the containerized backend** — otherwise both fight over port 8000:

```bash
docker compose stop backend temporal-worker
docker compose up -d db neo4j temporal jaeger prometheus grafana
```

**2. Point `.env` at localhost.** Compose normally injects Docker-internal hostnames; on the host you
need the published ports instead:

```env
NEO4J_URI=bolt://localhost:7687
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://sureflow_user:sureflow_password@localhost:5433/sureflow_db
```

**3. Install and run:**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn main:app --reload --port 8000

# macOS / Linux
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn main:app --reload --port 8000
```

**4. Windows only — OCR binaries.** Document upload needs Tesseract and Poppler, which are baked into
the Docker image but not present on Windows. Install both, then set `TESSERACT_CMD` and
`POPPLER_PATH` in `.env`.

---

## Seeding the demo data

Without seeding, the app runs but every dashboard is empty.

```bash
# Path A (Docker)
docker compose exec backend python scripts/seed_industrial_data.py
docker compose exec backend python scripts/seed_users.py
docker compose exec backend python scripts/seed_kpi_snapshots.py

# Path B (local) — from backend/, with the venv active
python scripts/seed_industrial_data.py
python scripts/seed_users.py
python scripts/seed_kpi_snapshots.py
```

| Script | Creates |
|---|---|
| `seed_industrial_data.py` | 2 plants, 12 pieces of equipment, areas, incidents, inspections — all plant-stamped |
| `seed_users.py` | The 3 demo users + their `Location` records |
| `seed_kpi_snapshots.py` | Synthetic KPI history so the Trends charts have something to plot |

Seeding is **idempotent** — re-running resets the demo passwords rather than duplicating rows.

### Demo accounts

| Email | Password | Scope |
|---|---|---|
| `cto@sureflow.ai` | `Sureflow_CTO_2026!` | Global — all plants + HQ layer |
| `karnataka@sureflow.ai` | `Sureflow_Plant_2026!` | PLANT-001 only |
| `delhi@sureflow.ai` | `Sureflow_Plant_2026!` | PLANT-002 only |

Source of truth is `backend/scripts/seed_users.py`. If login fails, check there before anything else.

---

## The frontend

Always runs on the host — it is deliberately not part of `docker-compose.yml`.

```bash
cd frontend
npm install
npm run dev          # → http://localhost:3000
```

No frontend `.env` is needed. `src/lib/api.ts` defaults to `http://localhost:8000/api/v1`, which
matches the backend. To point elsewhere, set `NEXT_PUBLIC_API_URL`.

For a production build:

```bash
npm run build && npm run start
```

---

## Verifying it works

Work down this list — each step depends on the ones above it.

**1. Backend is alive**

```bash
curl http://localhost:8000/api/v1/health
# → {"status":"online","service":"SureFlow OS","version":"2.0.0"}
```

**2. Auth works** *(proves the DB is reachable and seeded)*

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cto@sureflow.ai","password":"Sureflow_CTO_2026!"}'
# → {"access_token":"eyJ...","token_type":"bearer","user":{...}}
```

**3. The graph has data** — open [localhost:7474](http://localhost:7474)
(`neo4j` / `sureflow_password`) and run:

```cypher
MATCH (e:Equipment) RETURN e.tag, e.plant_id LIMIT 25
```

**4. The API surface** — [localhost:8000/docs](http://localhost:8000/docs) should list ~55 routes.

**5. End to end** — open [localhost:3000](http://localhost:3000), log in as the CTO, and confirm the
Plant Overview shows KPIs and an equipment tree.

> Anything failing? → **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**

---

## Common commands

```bash
# Lifecycle
docker compose up -d                    # start everything
docker compose down                     # stop (data volumes survive)
docker compose down -v                  # stop AND wipe all data
docker compose restart backend          # restart one service
docker compose up -d --build            # rebuild after code changes

# Inspection
docker compose ps                       # status of all services
docker compose logs -f backend          # follow backend logs
docker compose exec backend bash        # shell into the backend

# Frontend
cd frontend && npm run dev              # dev server, hot reload
cd frontend && npx tsc --noEmit         # typecheck
cd frontend && npm run lint             # lint
```
