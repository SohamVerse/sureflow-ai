# SureFlow OS — Industrial Intelligence Platform
## Complete Implementation Guide (Phases 1–5)

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Phase 1: Data Foundation](#phase-1-data-foundation)
3. [Phase 2: Agent Development](#phase-2-agent-development)
4. [Phase 3: Workflows & API](#phase-3-workflows--api)
5. [How to Run](#how-to-run)
6. [API Reference](#api-reference)
7. [What's Left (Phases 4–5)](#whats-left-phases-4-5)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                            │
│  Dashboard │ Copilot Chat │ KG Explorer │ Approval Center       │
└────────────────────────┬─────────────────────────────────────────┘
                         │ REST API (/api/v1)
┌────────────────────────┴─────────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│                                                                  │
│  ┌─────────────────────── API Layer ───────────────────────────┐ │
│  │  routes.py (existing)  │  industrial_routes.py (Phase 3)   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌─────────────── Temporal Workflow Layer ─────────────────────┐ │
│  │  DocumentIngestionWorkflow    (Upload → Extract → Embed)   │ │
│  │  MaintenanceLifecycleWorkflow (WO → RCA → Alert)           │ │
│  │  LessonsLearnedWorkflow       (Incident → Lessons)         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────── Agent Layer (BaseBrain) ────────────────────┐ │
│  │ Existing:  CEO│CMO│Research│SDR│AE│Risk│Email│Analyst      │ │
│  │ Phase 2:   DocIntel│KGAgent│Search│Maintenance│Lessons│Comp│ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────── Memory Layer ──────────────────────────────┐ │
│  │ Episodic (PG)   │ Reflection (PG)  │ Semantic (pgvector)   │ │
│  │ + equipment_tag  │ + equipment_tag   │ 12 collections total │ │
│  │ + context_type   │ + incident_id     │ (6 sales + 6 indust) │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────── Knowledge Graph Layer (Neo4j) ────────────────────┐ │
│  │ Strategic:  Competitor → Trend (existing)                  │ │
│  │ Industrial: Plant → Area → Equipment → Incidents/WOs/Docs  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────── MCP Layer ─────────────────────────────────┐ │
│  │ Sales: LinkedIn│Hubspot│Instagram│Gmail                    │ │
│  │ Industrial: CMMS (SAP PM mock)│IoT Sensors (mock)         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Foundation

### What was built
The data foundation that all agents and workflows build upon.

| Component | File | Description |
|---|---|---|
| Industrial KG Schema | `knowledge_graph/industrial_schema.py` | Neo4j constraints for Plant, Area, Equipment, Incident, WorkOrder, Inspection, Document |
| Industrial KG Store | `knowledge_graph/industrial_store.py` | Full CRUD interface — 7 write methods, 7 read methods, graceful degradation |
| pgvector Collections | `rag/embeddings.py` | 6 new industrial collections (10-oem-manuals through 15-incident-reports) |
| Extended Memory | `core/memory.py` | Equipment-scoped episodic/reflection memory, industrial semantic helpers |
| Extended DB Models | `models/memory.py` | Added equipment_tag, context_type, incident_id, category, source columns |
| Industrial Seed Data | `scripts/seed_industrial_data.py` | Demo data: 1 plant, 5 areas, 12 equipment, 6 incidents, 8 work orders, etc. |

---

## Phase 2: Agent Development

### 6 New Industrial Agents

| Agent | File | Model | Purpose |
|---|---|---|---|
| **Document Intelligence** | `agents/document_intelligence.py` | gemini-1.5-pro | Entity extraction, chunking, doc classification |
| **Knowledge Graph** | `agents/knowledge_graph_agent.py` | gemini-2.5-flash | Entity resolution, dedup, Neo4j writes |
| **Search (Copilot)** | `agents/search_agent.py` | gemini-1.5-pro | Hybrid search, multi-source synthesis, citations |
| **Maintenance** | `agents/maintenance.py` | gemini-1.5-pro | RCA (5-Why), failure prediction, MTBF |
| **Lessons Learned** | `agents/lessons_learned.py` | gemini-2.5-flash | Incident parsing, cross-asset warnings, patterns |
| **Compliance** | `agents/compliance.py` | gemini-2.5-flash | Regulatory gap analysis, audit readiness |

### Config and Registry Updates

| File | Change |
|---|---|
| `core/config.py` | 6 new model settings |
| `evaluation/evaluator.py` | All 6 agents added to AGENT_MODELS |
| `api/routes.py` | /agents/status now returns all 14 agents |

---

## Phase 3: Workflows and API

### Temporal Workflows

| Workflow | Pipeline |
|---|---|
| **DocumentIngestionWorkflow** | OCR → Doc Intelligence → pgvector Embed → KG Agent |
| **MaintenanceLifecycleWorkflow** | Record WO → Maintenance Agent → Alert if critical |
| **LessonsLearnedWorkflow** | Incident → Lessons Agent → Reflection Memory |

### Temporal Activities (9 new)

| Activity | Purpose |
|---|---|
| `ocr_extract_activity` | PDF/text/image → raw text |
| `doc_intelligence_activity` | Run Document Intelligence Agent |
| `embed_and_store_activity` | Chunk + embed into pgvector |
| `update_industrial_graph_activity` | Run KG Agent → Neo4j |
| `maintenance_analysis_activity` | Run Maintenance Agent |
| `record_work_order_activity` | Write WO to graph + memory |
| `lessons_learned_activity` | Run Lessons Learned Agent |
| `compliance_audit_activity` | Run Compliance Agent |
| `copilot_query_activity` | Run Search Agent |

### API Endpoints (19 new)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/industrial/upload` | POST | Upload document → full ingestion pipeline |
| `/api/v1/industrial/copilot` | POST | Chat with Industrial Copilot |
| `/api/v1/industrial/maintenance/analyze` | POST | Run maintenance analysis on equipment |
| `/api/v1/industrial/lessons-learned` | POST | Extract lessons from incidents |
| `/api/v1/industrial/compliance/audit` | POST | Run compliance gap analysis |
| `/api/v1/industrial/work-orders` | POST | Create work order |
| `/api/v1/industrial/graph/hierarchy` | GET | Plant → Area → Equipment tree |
| `/api/v1/industrial/graph/equipment` | GET | All equipment |
| `/api/v1/industrial/graph/equipment/{tag}` | GET | Equipment detail |
| `/api/v1/industrial/graph/equipment/{tag}/timeline` | GET | Asset timeline |
| `/api/v1/industrial/graph/incidents` | GET | All incidents |
| `/api/v1/industrial/graph/compliance-gaps/{area_id}` | GET | Compliance gaps |
| `/api/v1/industrial/graph/overview` | GET | Graph stats |
| `/api/v1/industrial/kpis` | GET | Industrial KPIs |
| `/api/v1/industrial/vault/stats` | GET | Industrial collection stats |
| `/api/v1/industrial/mcp/sensor/{tag}` | GET | Mock IoT sensor data |
| `/api/v1/industrial/mcp/cmms/work-order` | POST | Mock CMMS work order |
| `/api/v1/industrial/mcp/cmms/equipment/{tag}` | GET | Mock CMMS equipment |

### MCP Extension

| Platform | Mock Capabilities |
|---|---|
| **CMMS (SAP PM)** | create_work_order, get_equipment (4 realistic profiles), get_maintenance_history |
| **IoT Sensors** | read_sensors (vibration, temp, pressure, flow, current, RPM), get_alerts |

### Other Updates

| File | Change |
|---|---|
| `main.py` | Mounted industrial_router at /api/v1 |
| `workflows/worker.py` | Registered 3 industrial workflows + 9 activities |

---

## How to Run

### Prerequisites

1. **Docker Desktop** — for PostgreSQL, Neo4j, Temporal, Jaeger
2. **Python 3.11+** — backend
3. **Node.js 18+** — frontend
4. **Ollama** — for local embeddings (nomic-embed-text)
5. **Google Gemini API Key** — for agent LLM calls

### Step 1: Environment Setup

```bash
# Clone the repo
cd sureflow-ai

# Copy env file and configure
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your keys:
```
GOOGLE_API_KEY=your-gemini-api-key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
DATABASE_URL=postgresql://user:password@localhost:5432/sureflow
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 2: Start Infrastructure (Docker)

```bash
docker compose up -d
```

This starts:
- **PostgreSQL** (port 5433) — with pgvector extension
- **Neo4j** (ports 7474/7687) — Knowledge Graph
- **Temporal** (port 7233) — Workflow orchestration
- **Jaeger** (port 16686) — Distributed tracing
- **Prometheus** (9090) / **Grafana** (3001) — metrics and dashboards
- **Backend** (port 8000) and the **Temporal worker**

### Step 3: Install Ollama Model

```bash
ollama pull nomic-embed-text
```

### Step 4: Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Seed Industrial Demo Data

```powershell
cd backend
.venv\Scripts\python.exe scripts/seed_industrial_data.py
```

This populates Neo4j with 1 plant, 5 areas, 12 equipment, 6 incidents, 8 work orders, 5 inspections, and 4 operational lessons in Reflection Memory.

### Step 6: Start the Backend

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

You should see:
```
[START] Sureflow Agentic OS starting...
[OK] PostgreSQL tables ready.
[OK] Neo4j Strategic Knowledge Graph ready.
[OK] Neo4j Industrial Knowledge Graph ready.
[READY] All agents standing by.
```

### Step 7: (Optional) Start Temporal Worker

```powershell
# In a separate terminal
cd backend
.venv\Scripts\python.exe workflows/worker.py
```

### Step 8: Start the Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Step 9: Verify Everything Works

Open `http://localhost:8000/docs` for the Swagger API docs.

**Test the Copilot:**
```bash
curl -X POST http://localhost:8000/api/v1/industrial/copilot -H "Content-Type: application/json" -d "{\"query\": \"Show me the maintenance history for pump P-101\"}"
```

**Test Document Upload:**
```bash
curl -X POST http://localhost:8000/api/v1/industrial/upload -F "file=@your_document.pdf" -F "doc_type=oem_manual"
```

**Test Mock IoT Sensors:**
```bash
curl http://localhost:8000/api/v1/industrial/mcp/sensor/P-101
```

**Test KG Overview:**
```bash
curl http://localhost:8000/api/v1/industrial/graph/overview
```

---

## File Map (All Changes)

```
backend/
├── agents/
│   ├── document_intelligence.py  [NEW - Phase 2]
│   ├── knowledge_graph_agent.py  [NEW - Phase 2]
│   ├── search_agent.py           [NEW - Phase 2]
│   ├── maintenance.py            [NEW - Phase 2]
│   ├── lessons_learned.py        [NEW - Phase 2]
│   └── compliance.py             [NEW - Phase 2]
├── api/
│   ├── routes.py                 [MODIFIED - Phase 2/3]
│   └── industrial_routes.py      [NEW - Phase 3]
├── core/
│   ├── config.py                 [MODIFIED - Phase 2]
│   ├── memory.py                 [MODIFIED - Phase 1]
│   └── mcp.py                    [MODIFIED - Phase 3]
├── evaluation/
│   └── evaluator.py              [MODIFIED - Phase 2]
├── knowledge_graph/
│   ├── industrial_schema.py      [NEW - Phase 1]
│   └── industrial_store.py       [NEW - Phase 1]
├── models/
│   └── memory.py                 [MODIFIED - Phase 1]
├── rag/
│   └── embeddings.py             [MODIFIED - Phase 1]
├── scripts/
│   └── seed_industrial_data.py   [NEW - Phase 1]
├── workflows/
│   ├── worker.py                 [MODIFIED - Phase 3]
│   ├── industrial_activities.py  [NEW - Phase 3]
│   └── industrial_workflows.py   [NEW - Phase 3]
└── main.py                       [MODIFIED - Phase 3]
```

---

## Phase 4: Frontend Refactoring (complete)
- Dark industrial theme (globals.css overhaul)
- Knowledge Graph Explorer (React Flow + Neo4j visualization)
- Industrial Copilot Chat component (renders markdown + citations)
- Equipment Dashboard (timeline, sensor data, alerts)
- Maintenance Dashboard (RCA results, predictions)
- Compliance Dashboard (gap analysis, audit readiness)
- Document Upload UI (drag and drop + progress)

## Phase 5: Polish and Demo (complete)

| Item | What was built |
|---|---|
| **Real OCR** | `workflows/industrial_activities.py` `ocr_extract_activity` now does real Tesseract OCR (`pytesseract` + `Pillow`) for image files, real DOCX text extraction (`python-docx`), and a scanned-PDF fallback (`pdf2image` rasterization + OCR) when `PyPDFLoader` yields near-empty text. All three degrade gracefully to the prior placeholder text with a logged warning if the optional system binaries (Tesseract/Poppler) aren't installed. New `TESSERACT_CMD` / `POPPLER_PATH` settings in `core/config.py`. |
| **SSE Streaming** | New `POST /industrial/upload/stream` and `POST /industrial/copilot/stream` endpoints in `api/industrial_routes.py` stream real backend stage progress via SSE (same pattern as the existing `/pipeline/run`). Frontend: `industrialApi.uploadDocumentStream` / `copilotStream` in `lib/api.ts`; the Upload page now shows genuine pipeline progress instead of `setTimeout` animation, and the Copilot chat shows a live stage label while waiting. |
| **Agent Reasoning Visualization** | New `components/industrial/AgentReasoningPanel.tsx` — a collapsible panel surfacing `reasoning`, `confidence`, `risk_level`, `alternatives`, and `self_challenge`, fields every agent already returns via the shared `BaseBrain`/`parse_brain_output` contract but which the UI previously discarded. Wired into the Copilot chat, Maintenance dashboard, and Compliance dashboard. |
| **Performance Optimization** | 30s TTL cache on `IndustrialGraphStore.get_industrial_overview()` (hit on every Copilot query + KPI load) and an `lru_cache`-backed query-embedding cache in `rag/embeddings.py` (`query_collection`). Chunk embedding was already batched via a single `embed_documents()` call; LLM responses were already cached via `core/model_broker.py`'s `InMemoryCache`. |
| **Demo Script** | `docs/DEMO_SCRIPT.md` — setup checklist, a scripted plant-engineer walkthrough across every dashboard, and an explicit "what's real AI vs. mocked" table. |

Note: a dedicated Lessons Learned *page* doesn't exist in the frontend yet (only the `/industrial/lessons-learned` API + `industrialApi.analyzeLessons` client) — the reasoning panel is ready to wire in whenever that page is built.
