<div align="center">

<img src="frontend/public/logo.png" alt="SureFlow Logo" width="120" />

# SureFlow AI

### Intelligent Multi-Agent Knowledge Engine for Industrial Operations

**Complexity Down, Clarity Up.**

SureFlow transforms unstructured plant documents—such as OEM manuals, SOPs, incident logs, and inspection sheets—into a live, unified **Knowledge Graph** (Neo4j) and **semantic vector store** (pgvector). Six specialized, cooperative AI agents reason over this dual-memory system to deliver predictive maintenance intelligence, automated compliance audits, proactive risk alerts, and a natural-language Copilot.

Vercel : https://sureflow-ai-xz25.vercel.app
<br/>

![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j_5-4581C3?style=for-the-badge&logo=neo4j&logoColor=white)
![Postgres](https://img.shields.io/badge/pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-darkred?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](./LICENSE)
[![Copyright](https://img.shields.io/badge/Copyright-%C2%A9_2026_Team_Hogwart-6C3483?style=for-the-badge)](./NOTICE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-crimson?style=for-the-badge&logo=shieldsdotio&logoColor=white)](./SECURITY.md)
[![Version](https://img.shields.io/badge/Version-2.0.0-2E86AB?style=for-the-badge)](./NOTICE)
![Build](https://img.shields.io/badge/Build-Passing-28A745?style=for-the-badge&logo=githubactions&logoColor=white)
[![Team Hogwart](https://img.shields.io/badge/Team-Hogwart-4A235A?style=for-the-badge)](./NOTICE)
[![ET AI Hackathon 2.0](https://img.shields.io/badge/ET_AI_Hackathon-2.0-E67E22?style=for-the-badge&logo=rocket&logoColor=white)](./NOTICE)
![Last Updated](https://img.shields.io/badge/Last_Updated-July_2026-17A589?style=for-the-badge)

</div>

---

## 📑 Contents

**[The Problem](#-the-problem)** · **[What It Does](#-what-it-does)** ·
**[⚡ Quick Start](#-quick-start)** · **[Demo Logins](#-demo-logins)** ·
**[Service Map](#-service-map)** · **[Running Locally (no Docker)](#-running-the-backend-without-docker)** ·
**[🔧 Troubleshooting](#-troubleshooting)** · **[Features](#-features)** ·
**[Architecture](#-architecture)** · **[The Six AI Brains](#-the-six-ai-brains)** ·
**[Tech Stack](#-tech-stack)** · **[Project Structure](#-project-structure)** ·
**[More Docs](#-more-documentation)** · **[License & IP](#-license--intellectual-property)**

---

## 🔥 The Problem

A petrochemical plant's most valuable operational knowledge is **trapped in unstructured documents** —
thousands of PDF manuals, scanned inspection sheets, and incident write-ups nobody can query.

When a pump fails at 3 AM, the answer usually exists. It's on page 340 of a 2011 OEM manual, or in an
incident report from a sister plant that hit the same failure last year. Nobody finds it in time.

**The result:** repeat failures, missed compliance gaps, and lessons that are never actually learned.

## 💡 What It Does

SureFlow ingests those documents and builds two complementary memories:

- a **Knowledge Graph** (Neo4j) — the plant's *structure*: `Plant → Area → Equipment → Incidents`
- a **semantic vector store** (pgvector) — the plant's *meaning*: what the documents actually say

Six specialized agents reason across **both at once**. Ask *"why does P-101 keep cavitating?"* and the
Copilot walks the graph for that pump's real failure history **and** semantically searches every
manual — then answers with **citations** back to the source document.

> **The key property:** upload a document and it lands in *every* dashboard — Equipment, Maintenance,
> Compliance, Lessons Learned — not just in a chatbot's search index.

---

## ⚡ Quick Start

### Prerequisites

| Requirement | Why | Notes |
|---|---|---|
| **Docker Desktop** | Runs the backend + all infrastructure | Required |
| **Node.js 20+** | The frontend | Always runs on the host |
| **Gemini API key** | Powers all six agents | Free tier is plenty — [get one](https://aistudio.google.com/apikey) |
| **Ollama** *(optional)* | Embeddings + offline fallback | Improves semantic search |

### 1️⃣ Configure

```bash
git clone <your-repo-url>
cd sureflow-ai

cp backend/.env.example backend/.env
```

Open `backend/.env` and set your key. **This is the only value you must provide** — everything else
has a working default:

```env
GEMINI_API_KEY=your-key-here
```

### 2️⃣ Start everything

```bash
docker compose up -d
```

This brings up **nine services**: the FastAPI backend, the Temporal worker, Postgres + pgvector,
Neo4j, Temporal, Jaeger, Prometheus, and Grafana.

Verify it's healthy:

```bash
docker compose ps
curl http://localhost:8000/api/v1/health
# → {"status":"online","service":"SureFlow AI","version":"2.0.0"}
```

### 3️⃣ Seed the demo data

Without this the app runs but every dashboard is empty. All three scripts are idempotent:

```bash
docker compose exec backend python scripts/seed_industrial_data.py   # 2 plants, 12 equipment
docker compose exec backend python scripts/seed_users.py             # 3 demo users
docker compose exec backend python scripts/seed_kpi_snapshots.py     # KPI history for Trends
```

### 4️⃣ Start the frontend

```bash
cd frontend
npm install
npm run dev
```

No frontend `.env` is needed — it defaults to `http://localhost:8000/api/v1`.

### 5️⃣ Open it

**→ [http://localhost:3000](http://localhost:3000)**, then sign in below.

### Optional: Ollama

Provides the embedding model for semantic search plus a local fallback when Gemini errors or hits
quota. The app runs without it, but retrieval quality drops.

```bash
ollama pull nomic-embed-text    # 768-dim embeddings
ollama pull llama3.2            # offline fallback LLM
```

---

## 🔑 Demo Logins

| Role | Email | Password | Sees |
|---|---|---|---|
| 🌐 **CTO** *(global)* | `cto@sureflow.ai` | `Sureflow_CTO_2026!` | **All plants** + the HQ roll-up layer |
| 🏭 **Karnataka Manager** | `karnataka@sureflow.ai` | `Sureflow_Plant_2026!` | `PLANT-001` only |
| 🏭 **Delhi Manager** | `delhi@sureflow.ai` | `Sureflow_Plant_2026!` | `PLANT-002` only |

Scope is derived server-side from the verified JWT — never from a client field. A plant manager
requesting another plant's data gets **403**. Tokens last 24 hours.

> Source of truth is `backend/scripts/seed_users.py`. If a login ever fails, check there first.

**Try this:** log in as Karnataka and note the equipment list. Then log in as the CTO and use the
**plant switcher** in the sidebar — same data, plus a cross-plant benchmark a manager can't reach.

---

## 🌐 Service Map

| Service | URL | Purpose |
|---|---|---|
| **Frontend** | [localhost:3000](http://localhost:3000) | The app |
| **API docs** | [localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI — ~55 routes |
| **Health** | [localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | Liveness check |
| **Neo4j Browser** | [localhost:7474](http://localhost:7474) | Inspect the graph — `neo4j` / `sureflow_password` |
| **Temporal UI** | [localhost:8085](http://localhost:8085) | Durable workflows |
| **Jaeger** | [localhost:16686](http://localhost:16686) | Distributed traces |
| **Grafana** | [localhost:3001](http://localhost:3001) | Metrics dashboards |
| **Prometheus** | [localhost:9090](http://localhost:9090) | Raw metrics |

### Common commands

```bash
docker compose up -d                    # start everything
docker compose down                     # stop (data volumes survive)
docker compose down -v                  # stop AND wipe all data
docker compose up -d --build            # rebuild after backend code changes
docker compose ps                       # status
docker compose logs -f backend          # follow backend logs
docker compose exec backend bash        # shell into the backend

cd frontend && npm run dev              # dev server
cd frontend && npx tsc --noEmit         # typecheck
```

---

## 💻 Running the backend without Docker

Useful when actively editing backend code and you want hot-reload.

**1. Stop the containerized backend** — otherwise both fight over port 8000:

```bash
docker compose stop backend temporal-worker
docker compose up -d db neo4j temporal jaeger prometheus grafana
```

**2. Point `.env` at localhost.** Compose injects Docker-internal hostnames; on the host you need the
published ports instead:

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

**4. Windows only — OCR binaries.** Document upload needs Tesseract and Poppler. They're baked into
the Docker image but not present on Windows. Install
[Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and
[Poppler](https://github.com/oschwartz10612/poppler-windows/releases), then set in `.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\poppler\Library\bin
```

---

## 🔧 Troubleshooting

<details>
<summary><b>🐳 Docker build fails: <code>invalid file request Dockerfile</code></b></summary>

<br/>

```
#2 transferring dockerfile: 31B
#2 ERROR: invalid file request Dockerfile
```

The giveaway is the byte count — `31B` when the real Dockerfile is ~640B. Docker isn't reading your
file at all.

**Cause:** the project sits in a **OneDrive**-synced folder. OneDrive Files On-Demand turns files
into dehydrated placeholders carrying the `ReparsePoint` attribute, and Docker BuildKit refuses to
read any file with a reparse point.

**Confirm it:**
```powershell
Get-Item .\backend\Dockerfile | Select-Object Name, Length, Attributes
# ReparsePoint in the output → this is your problem
```

**What does NOT work:** `attrib +P` ("Always keep on this device") hydrates the content but leaves
the reparse point tag in place. The build fails identically. This is the advice you'll find
everywhere and it does not fix this.

**The fix** — rewrite each affected file as a genuine local file:

```powershell
$root = "path\to\sureflow-ai"
$venv = [System.IO.Path]::Combine($root, "backend", ".venv")

$targets = @()
$targets += Get-ChildItem $root -File -Force -ErrorAction SilentlyContinue
$targets += Get-ChildItem ([System.IO.Path]::Combine($root,"backend")) -Recurse -File -Force `
            -ErrorAction SilentlyContinue |
            Where-Object { -not $_.FullName.StartsWith($venv, 'OrdinalIgnoreCase') }
$targets = $targets | Where-Object { ([int]$_.Attributes -band 0x400) -ne 0 }

foreach ($f in $targets) {
  $src = $f.FullName; $tmp = "$src.hyd"
  $bytes = [System.IO.File]::ReadAllBytes($src)
  [System.IO.File]::WriteAllBytes($tmp, $bytes)
  [System.IO.File]::Delete($src)
  [System.IO.File]::Move($tmp, $src)
}
```

Attributes should drop to `32` (Archive only), and the build succeeds.

⚠️ **This recurs** — OneDrive re-dehydrates files within hours. Worse, a re-dehydrated file can leave
your **built image holding stale code** while the host source is current. If a container behaves
oddly, diff its copy against the host and rebuild:

```bash
docker compose exec -T backend grep -n "something" scripts/seed_users.py
docker compose build backend
```

**The durable fix is moving the repository outside OneDrive.**

</details>

<details>
<summary><b>🔌 Port already in use</b></summary>

<br/>

```powershell
netstat -ano | findstr :8000        # Windows
lsof -i :8000                       # macOS / Linux
```

| Port | Service | Frequent conflict |
|---|---|---|
| 3000 | Frontend | Another Next.js/React app |
| 8000 | Backend | **A local backend and the Docker backend both running** |
| 5433 | Postgres | Deliberately not 5432, to dodge a local Postgres |
| 7474 / 7687 | Neo4j | A local Neo4j install |
| 3001 | Grafana | Mapped off 3000 because the frontend owns it |

By far the most common case is running Docker *and* local backend at once. Pick one:

```bash
docker compose stop backend temporal-worker   # then run uvicorn locally
```

</details>

<details>
<summary><b>🔑 Login returns 401</b></summary>

<br/>

**Check the password first.** Older drafts of these docs circulated `admin123` / `plant123` — those
are stale and return 401. The working credentials are in [Demo Logins](#-demo-logins) above, with
`backend/scripts/seed_users.py` as the source of truth.

**If the password is right,** the users aren't seeded:

```bash
docker compose exec backend python scripts/seed_users.py
```

**If you were logged in and suddenly get 401s,** your JWT expired — tokens last 24 hours. Log in again.

</details>

<details>
<summary><b>🔁 Browser flickers between /login and /industrial</b></summary>

<br/>

A redirect loop from a desynced session: `sureflow_user` present in `localStorage` but
`sureflow_token` missing, so each route's guard bounces to the other.

**Fix:** hard-refresh (`Ctrl+Shift+R`). The auth layer treats a session as valid only when *both*
keys exist and clears a half-session automatically, so it self-heals to the login page.

If it somehow persists, clear it manually in DevTools → Console:

```js
localStorage.removeItem('sureflow_token');
localStorage.removeItem('sureflow_user');
localStorage.removeItem('sureflow_target_plant');
location.href = '/login';
```

</details>

<details>
<summary><b>📭 Dashboards are empty</b></summary>

<br/>

Almost always missing seed data — run all three [seed scripts](#3️⃣-seed-the-demo-data).

Verify the graph actually has nodes at [localhost:7474](http://localhost:7474):

```cypher
MATCH (e:Equipment) RETURN count(e)
```

If that returns `0`, `seed_industrial_data.py` didn't complete — check its output for errors.

**If data exists but one plant looks empty,** that's the isolation model working correctly: a plant
manager only ever sees their own plant. Log in as the CTO to see everything.

</details>

<details>
<summary><b>🤖 Agents fail or return nothing</b></summary>

<br/>

**1. Is the API key set?** The most common cause by far.

```bash
docker compose exec backend printenv | grep GEMINI
```

Empty means `backend/.env` is missing or lacks the key. Editing `.env` requires a restart:
`docker compose restart backend`.

**2. Quota exhausted.** A `429` in the logs means you've hit the free-tier daily limit. The Model
Broker falls back to local Ollama automatically — but only if Ollama is running (`ollama list`).

**3. Malformed JSON from the LLM** is already handled — `core/json_utils.py` uses `json-repair` to
recover broken model output.

**4. Watch it happen:** `docker compose logs -f backend`

</details>

<details>
<summary><b>🕸 Neo4j connection refused</b></summary>

<br/>

**Wrong hostname for your setup.** Inside Docker the host is `neo4j`; from your machine it's
`localhost`:

```env
NEO4J_URI=bolt://neo4j:7687        # backend running in Docker
NEO4J_URI=bolt://localhost:7687    # backend running on the host
```

Compose sets the Docker value automatically — you only change this when running locally.

**Neo4j is slow to start** — it accepts Bolt connections several seconds after the container reports
as running. Check with `docker compose logs neo4j | grep -i started`.

**Credentials** (`neo4j` / `sureflow_password`) come from `NEO4J_AUTH` in compose. Changing that
after the volume exists has no effect without `docker compose down -v`, which erases all data.

</details>

<details>
<summary><b>📄 Document upload fails</b></summary>

<br/>

**In Docker** the OCR toolchain is preinstalled, so check the logs for the real exception.

**Running locally on Windows** you need Tesseract and Poppler — see
[Running without Docker](#-running-the-backend-without-docker).

**Scanned PDFs with no text layer** fall back to OCR, which is slow. The endpoint streams SSE
progress, so the UI shows which stage it's on — give it time before assuming it hung.

</details>

<details>
<summary><b>⚠️ Next.js picks the wrong workspace root</b></summary>

<br/>

```
⚠ Warning: Next.js inferred your workspace root, but it may not be correct.
```

Multiple `package-lock.json` files exist and Next picked one outside the project. Harmless, but it
can cause odd module resolution. Delete the stray lockfiles (keep `frontend/package-lock.json`), or
pin the root in `next.config.ts`:

```ts
const nextConfig = { turbopack: { root: __dirname } };
```

</details>

---

## ✨ Features

### Core platform

| | Feature | What it does |
|---|---|---|
| 🏠 | **Landing + Plant Overview** | Public page at `/`; the app at `/industrial` with live KPIs, the `Plant → Area → Equipment` tree, and recent incidents. |
| 💬 | **Industrial Copilot** | Conversational assistant doing **hybrid search** — graph traversal *plus* vector semantic search — answering **with citations**. |
| 🔧 | **Equipment Dashboard** | Browse, search, and filter every asset; per-asset detail with an event **timeline** and live sensor gauges. |
| 🛠️ | **Maintenance Intelligence** | Root Cause Analysis (5-Why), cross-asset failure **prediction** (MTBF), prioritized preventive recommendations. |
| 📋 | **Compliance** | Regulatory **gap analysis**, SOP checks, audit-readiness scoring (OSHA / ISO / Factory Act). |
| 🎓 | **Lessons Learned** | Extracts lessons from incidents, raises **cross-asset warnings**, detects recurring failure patterns. |
| 📤 | **Document Ingestion** | PDF/DOCX/image/text → OCR → entity extraction → embedded into pgvector **and** synced into the graph, with **live SSE progress**. |

### Multi-plant & operations

| | Feature | What it does |
|---|---|---|
| 🔐 | **Auth + RBAC** | JWT login, bcrypt hashing, three roles, complete plant-level data isolation. |
| 🏢 | **HQ layer** *(CTO)* | Cross-plant roll-up, side-by-side comparison, reliability benchmarking, and a **global Copilot**. |
| 🔔 | **Alerts & Digest** | Deterministic alerts from graph signals, sidebar bell badge, and a prioritized "morning briefing". |
| ⚙️ | **Closed-loop Work Orders** | Create a work order straight from a Maintenance recommendation, track `open → in_progress → completed`. |
| 📊 | **KPI Trends** | Snapshot history with per-metric line charts. |
| 🔎 | **Global Search + CSV Export** | Search equipment, incidents, documents, and lessons; export any table. |
| 🧪 | **AI Quality & Cost panel** | Per-agent confidence, latency, cost, and schema-validity tracking. |

> 📌 For the complete inventory — including **what isn't built and why** — see
> [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md).

---

## 🏗 Architecture

<div align="center">
  <img src="frontend/public/architecture.svg" alt="SureFlow AI Architecture" width="800" />
</div>

### Key data flows

**Document upload → insight** — `POST /api/v1/industrial/upload/stream`

```
File → OCR/extract (Tesseract · pypdf · docx)
     → Doc Intelligence Agent (entities, relationships, type)
     → embed chunks into pgvector
     → MERGE Equipment + Document nodes into Neo4j (deterministic)
     → live SSE progress at every stage
```

**Copilot query** — `POST /api/v1/industrial/copilot/stream`

```
Query → detect equipment tags
      → Neo4j: graph overview + asset timeline
      → pgvector: semantic search across all collections
      → single Gemini synthesis call → cited answer
```

### Knowledge graph ontology

```
Plant ─CONTAINS→ Area ─CONTAINS→ Equipment
Equipment ─IS_TYPE→ AssetClass       Equipment ─MANUFACTURED_BY→ OEM
Incident ─INVOLVED→ Equipment        WorkOrder ─PERFORMED_ON→ Equipment
Inspection ─INSPECTED→ Equipment     Document ─HAS_MANUAL→ Equipment
```

Every node carries a denormalized `plant_id`, so all reads filter by plant — this is what makes the
multi-tenant isolation airtight.

---

## 🧠 The Six AI Brains

Each agent lives in `backend/agents/` and emits a structured `BrainOutput` — reasoning, confidence,
risk level, citations, and a self-challenge.

| Agent | ID | Role |
|---|---|---|
| **Document Intelligence** | `DOC_INTELLIGENCE` | OCR'd text → entities, relationships, doc type, intelligent chunks |
| **Knowledge Graph** | `KG_AGENT` | Resolves and deduplicates entities, writes nodes/edges to Neo4j |
| **Search / Copilot** | `SEARCH_AGENT` | Hybrid graph + vector retrieval → cited natural-language answers |
| **Maintenance** | `MAINTENANCE` | RCA, failure prediction, preventive recommendations |
| **Compliance** | `COMPLIANCE` | Regulatory gap analysis, SOP checks, audit readiness |
| **Lessons Learned** | `LESSONS_LEARNED` | Lesson extraction, cross-asset warnings, pattern detection |

All six share one shape: **gather graph + vector context → a single LLM reasoning call → structured
JSON out.** The **Model Broker** routes each call cost-aware and falls back to local Ollama
automatically if the primary model errors.

---

## 🛠 Tech Stack

<table>
<tr><td><b>Frontend</b></td><td>
Next.js 16 (App Router) · React 19 · TypeScript · Zustand · Axios (REST + SSE) · Tailwind CSS v4 · lucide-react · react-hot-toast
</td></tr>
<tr><td><b>Backend</b></td><td>
Python · FastAPI (REST + SSE) · LangChain + LangGraph · SQLAlchemy · Alembic · a cost-aware Model Broker
</td></tr>
<tr><td><b>AI / LLM</b></td><td>
Google <b>Gemini 2.5 Flash</b> (all six agents) · Ollama <code>nomic-embed-text</code> (768-dim embeddings) + <code>llama3.2</code> (offline fallback) · pgvector RAG · <code>json-repair</code> for malformed LLM JSON
</td></tr>
<tr><td><b>Data</b></td><td>
PostgreSQL 15 + pgvector (embeddings, memory, users, alerts) · Neo4j 5 (Industrial Knowledge Graph)
</td></tr>
<tr><td><b>Infra & Observability</b></td><td>
Docker Compose · Temporal (durable workflows) · OpenTelemetry → Jaeger (traces) / Prometheus + Grafana (metrics) · Tesseract + Poppler OCR
</td></tr>
</table>

---

## 📁 Project Structure

```
sureflow-ai/
├── README.md                   ← you are here: product, setup, troubleshooting
│
├── frontend/                   # Next.js 16 app (runs on the host)
│   └── src/
│       ├── app/                # / (landing) · /login · /industrial/*
│       ├── components/         # landing/ · industrial/ · layout/
│       └── lib/                # api.ts (Axios+SSE) · AuthContext.tsx · store.ts
│
├── backend/                    # FastAPI app (runs in Docker)
│   ├── agents/                 # the six Brains
│   ├── api/                    # routes.py · industrial_routes.py · hq_routes.py
│   ├── core/                   # config · model_broker · memory · security · telemetry
│   ├── knowledge_graph/        # Neo4j store + schema
│   ├── rag/                    # pgvector embeddings
│   ├── models/                 # SQLAlchemy: memory · vault · auth
│   ├── workflows/              # Temporal activities & workflows
│   ├── scripts/                # seed_industrial_data · seed_users · seed_kpi_snapshots
│   └── .env.example            # ← copy to .env
│
├── docs/                       # supplementary documentation
├── observability/              # Prometheus + Grafana provisioning
└── docker-compose.yml          # all nine services
```

---

## 📚 More Documentation

Everything needed to **run** the product is in this file. These go deeper:

| Doc | What's in it |
|---|---|
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 🚀 **Full production deployment guide** — Render + Neo4j AuraDB + Vercel |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | 🎬 An 8–10 minute guided walkthrough for presenting |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | What's built, what isn't, and **why** each gap was deferred |
| [docs/MULTI_LOCATION.md](docs/MULTI_LOCATION.md) | Multi-plant architecture and the isolation model |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What comes next, ranked by impact vs. effort |

---

<div align="center">

**SureFlow AI** — built for the ET Gen AI 2.0 Hackathon 🏆

*Turning shelf-ware documents into operating intelligence.*

</div>

---

## 🔐 License & Intellectual Property

<div align="center">

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-darkred?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](./LICENSE)
[![Copyright](https://img.shields.io/badge/Copyright-%C2%A9_2026_Team_Hogwart-6C3483?style=for-the-badge)](./NOTICE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-crimson?style=for-the-badge&logo=shieldsdotio&logoColor=white)](./SECURITY.md)
[![Version](https://img.shields.io/badge/Version-2.0.0-2E86AB?style=for-the-badge)](./NOTICE)
[![Team Hogwart](https://img.shields.io/badge/Team-Hogwart-4A235A?style=for-the-badge)](./NOTICE)
[![ET AI Hackathon 2.0](https://img.shields.io/badge/ET_AI_Hackathon-2.0-E67E22?style=for-the-badge)](./NOTICE)

</div>

This repository contains **proprietary software** developed and owned by **Team Hogwarts_House**.

- **Ownership.** All source code, documentation, architecture, AI workflows, prompts, APIs, database schema, branding, and related intellectual property are the exclusive property of Team Hogwarts_House, unless otherwise specified by the official terms and conditions of ET AI Hackathon 2.0.
- **Hackathon Context.** This project was created during **ET AI Hackathon 2.0**. Participation in the hackathon does not, by itself, transfer ownership of the source code or intellectual property to any third party.
- **Confidentiality.** The source code is **confidential and proprietary**. Viewing this repository does not grant permission to copy, modify, redistribute, reverse engineer, or commercially use any portion of the project.
- **Protected Assets.** All trademarks, branding, documentation, architecture, AI workflows, prompts, database schema, APIs, UI/UX designs, and source code are protected intellectual property belonging to Team Hogwarts_House.
- **No Open-Source License.** This project is **not** licensed under MIT, Apache, GPL, or any other open-source license.

### Legal Notice

> **⚠️ NOTICE:** Unauthorized copying, reproduction, modification, distribution, reverse engineering, sublicensing, or commercial use of this software — in whole or in part — is strictly prohibited without prior written permission from Team Hogwarts_House. Violations may result in legal action to the fullest extent permitted by applicable law.
>
> For licensing inquiries, contact: **[17nyasa.parikh@gmail.com]** or **[atharvashewale361@gmail.com]**

| Document | Purpose |
|---|---|
| [`LICENSE`](./LICENSE) | Proprietary Software License Agreement |
| [`NOTICE`](./NOTICE) | Ownership & confidentiality notice |
| [`SECURITY.md`](./SECURITY.md) | Responsible vulnerability disclosure policy |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | Internal contributor guidelines |
| [`docs/COPYRIGHT_HEADERS.md`](./docs/COPYRIGHT_HEADERS.md) | Source file copyright header templates |

---

<div align="center">

---

© 2026 **Team Hogwarts_House** · All Rights Reserved.

Developed during **ET AI Hackathon 2.0**.

*This repository contains confidential and proprietary software owned by Team Hogwarts_House.*
*Unauthorized copying, reproduction, modification, distribution, reverse engineering,*
*or commercial use is prohibited without prior written permission.*

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-darkred?style=flat-square)](./LICENSE)
[![Team Hogwarts_House](https://img.shields.io/badge/Team-Hogwarts__House-6C3483?style=flat-square)](./NOTICE)
[![ET AI Hackathon 2.0](https://img.shields.io/badge/ET_AI_Hackathon-2.0-E67E22?style=flat-square)](./NOTICE)

---

</div>
