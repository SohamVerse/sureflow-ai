# SureFlow OS — Project Status & Feature Inventory

The single source of truth for **what's built, what's not, and why.** For deeper detail see the companion docs:
[`README.md`](../README.md) (architecture & tech stack) · [`MULTI_LOCATION.md`](./MULTI_LOCATION.md) (multi-plant design) · [`ROADMAP.md`](./ROADMAP.md) (future enhancements).

> **What it is:** an agentic operations platform for heavy industry. Operators upload their documents (OEM manuals, SOPs, incident/inspection reports); SureFlow turns them into a live **Knowledge Graph + semantic memory** that a team of six specialized AI "Brains" reason over to deliver maintenance intelligence, compliance audits, lessons learned, proactive alerts, and a natural-language Copilot — across **multiple plants** with role-based access.

---

## Running it

Full instructions live in [`GETTING_STARTED.md`](./GETTING_STARTED.md). The short version:

```bash
cp backend/.env.example backend/.env    # then set GEMINI_API_KEY
docker compose up -d                    # backend + worker + all infrastructure

docker compose exec backend python scripts/seed_industrial_data.py   # 2 plants, 12 equipment
docker compose exec backend python scripts/seed_users.py             # CTO + 2 plant managers
docker compose exec backend python scripts/seed_kpi_snapshots.py     # KPI history for Trends

cd frontend && npm install && npm run dev   # http://localhost:3000
```

**Demo logins** (source of truth: `backend/scripts/seed_users.py`):

| Email | Password | Scope |
|---|---|---|
| `cto@sureflow.ai` | `Sureflow_CTO_2026!` | global |
| `karnataka@sureflow.ai` | `Sureflow_Plant_2026!` | PLANT-001 |
| `delhi@sureflow.ai` | `Sureflow_Plant_2026!` | PLANT-002 |

**Services:** Frontend `:3000` · API `:8000/api/v1` · Neo4j `:7474` · Temporal UI `:8085` · Jaeger `:16686` · Grafana `:3001`

---

## Tech stack (brief)

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Zustand, Axios, Tailwind v4, lucide-react.
- **Backend:** Python + FastAPI, LangChain, a cost-aware model broker.
- **AI:** Google **Gemini 2.5 Flash** (all agents) · **Ollama** (`nomic-embed-text` embeddings, `llama3.2` offline fallback) · **pgvector** RAG · `json-repair` for robust LLM JSON.
- **Data:** **PostgreSQL/NeonDB + pgvector** (embeddings, memory, users, alerts, snapshots) · **Neo4j** (Industrial Knowledge Graph).
- **Infra/Obs:** Docker Compose · Temporal · OpenTelemetry → Jaeger / Prometheus / Grafana · Tesseract/Poppler OCR.

---

## ✅ Implemented features

### A. Core industrial platform
- **Public landing page** at `/`; the app lives at `/industrial` (the root no longer force-redirects).
- **Six AI "Brains":** Document Intelligence, Knowledge Graph Agent, Search/Copilot, Maintenance, Compliance, Lessons Learned — each emits structured output (reasoning, confidence, risk, citations).
- **Document ingestion pipeline:** upload (PDF/DOCX/image/text) → OCR/extract → entity extraction → embed into pgvector → **deterministically sync Equipment + Document nodes into Neo4j** (so uploads show up in every dashboard, not just Copilot), with live SSE progress.
- **Dashboards:** Plant Overview (KPIs, hierarchy, incidents), Equipment (list + detail + asset timeline + mock sensors), Industrial Copilot (hybrid graph+vector search with citations), Maintenance (RCA / failure prediction), Compliance (gap analysis / audit readiness), Lessons Learned (cross-asset warnings / patterns).
- **Knowledge Graph** (Neo4j: Plant → Area → Equipment → Incidents/WorkOrders/Inspections/Documents) + **semantic memory** (pgvector collections, episodic & reflection memory).
- **Observability:** distributed tracing, metrics, and per-call LLM cost estimation.

### B. Multi-location (Phases 1–5, all done — see `MULTI_LOCATION.md`)
- **Authentication:** `User`/`Location` models, JWT login, bcrypt hashing, `/auth/login|me|users`.
- **Enforcement:** `get_current_user` + `resolve_scope` on **every** industrial/HQ route — scope derives from the verified JWT, never from a client body field.
- **Roles:** Global **CTO** (all plants) · **Plant Manager** (locked to one plant) · Operator.
- **Full data isolation:** every Neo4j node carries a denormalized `plant_id` (reads filter by it); memory tables + uploads are plant-stamped; all six agents are plant-scoped. Cross-plant access → **403**.
- **HQ layer (CTO):** `/hq/overview` (roll-up + per-plant risk), `/hq/compare` (side-by-side), `/hq/benchmark` (reliability ranking), a **global Copilot** over all plants, and a **plant switcher** in the sidebar.
- **Location provisioning:** `POST /plants` — one-shot onboarding (plant + area skeleton + first manager) with a **Manage Locations** UI.

### C. Proactive & closed-loop operations (ROADMAP §1–3)
- **🔔 Alerts & Notifications:** deterministic generation from graph signals (unresolved severe incidents, failed inspections), sidebar **bell badge**, Alerts page with ack/resolve — plant-scoped, idempotent.
- **⚙️ Closed-loop Work Orders:** create a work order **directly from a Maintenance recommendation**, track it through a status pipeline (open → in_progress → completed) on the Work Orders page — plant-scoped.
- **🌅 Proactive Risk Digest:** `/alerts/digest` — a prioritized "morning briefing" with a recommended action per risk, surfaced atop the Alerts page.
- **🗂️ Document retention + viewer:** uploaded source files are retained and served **plant-isolated** via `/industrial/documents/{id}/file` (previously they were deleted after processing).

### D. Analytics & search (ROADMAP §1–2)
- **🧪 AI Quality & Cost panel:** `/system/ai-quality` + page — per-agent confidence, latency, cost, schema-validity, and human-approval flags, plus totals.
- **📊 KPI Trends:** `KpiSnapshot` + `/industrial/kpis/{snapshot,trends}` + a **Trends** page with per-metric line charts (2px marks, direct last-value labels, hover crosshair — built to the dataviz spec).
- **🔎 Global Search:** `/industrial/search` across equipment, incidents, documents, and lessons + a sidebar search box → results page (plant-scoped).
- **📄 CSV Export:** `/industrial/export/{equipment,incidents,work-orders}.csv` + download buttons.

### E. Notable fixes made this cycle
- **Robust LLM JSON parsing** (`core/json_utils.py` + `json-repair`) — `gemini-3.5-flash` intermittently emitted malformed JSON that silently broke Copilot/Compliance/Lessons/Doc-Intelligence; parsing now recovers it (0/5 → 6/6 in testing).
- **Model switch to `gemini-2.5-flash`** — the configured `gemini-3.5-flash` had a near-zero free-tier quota; 2.5-flash is stable with a generous quota.
- **Doc-upload → dashboard sync** — uploads now create queryable Equipment nodes so they appear in the Equipment/Maintenance/Compliance dropdowns, not only in Copilot's vector search.
- **Cache-invalidation + equipment-dedup + area-resolution** fixes surfaced during multi-plant testing.

---

## 🔨 What's left — and *why*

Nothing below is "forgotten." Each item is deferred for a concrete reason — mostly **it needs an external system, credential, or piece of infrastructure that can't be built or verified in this environment.** Building unrunnable stubs would be worse than being explicit.

| Feature | Why it's not built |
|---|---|
| **Email / Slack / Teams push** for alerts & digest | Needs real **webhook URLs / SMTP credentials**. In-app alerts are done; the push channel is a thin, credential-gated add-on. |
| **Scheduled (cron) digest & KPI snapshots** | Needs a **scheduler/deployment** (cron, Celery beat, or the `schedule` capability). Today snapshots are seeded and the digest is on-demand. |
| **Report export as branded PDF** | Needs a **PDF library** (`reportlab`/`weasyprint`) not installed. **CSV export is done** as the dependency-free equivalent. |
| **Real-time telemetry (MQTT / OPC-UA)** | Needs an actual **broker / real sensors**. Sensor data is currently mocked in `core/mcp.py`. |
| **Real CMMS / historian integration (SAP PM, Maximo, OSIsoft PI)** | Needs access to **enterprise systems + credentials**. The MCP layer is a mock. |
| **Durable async ingestion (Temporal)** | The Temporal container runs, but the live upload path is synchronous inline; wiring the existing workflow is a **larger, riskier refactor** better done deliberately. |
| **SSO / SAML** | Needs an **identity provider (Okta/Azure AD)**. JWT auth + RBAC is done as the foundation. |
| **Mobile / PWA for field operators** | A **separate, sizeable build** (offline capture, QR scan) beyond the current web app. |
| **Digital twin / P&ID view** | Needs **plant diagram assets** and a viewer to overlay live status. |
| **"View source" citation link in the UI** | Backend is ready (`/industrial/documents/{id}/file`); this is a **small remaining frontend wire-up**. |
| **Human-in-the-loop approvals UI** | The `requires_human_approval` field exists and is surfaced in the AI Quality panel; a full approval **workflow UI** is deferred. |
| **Cross-asset / cross-plant automated pattern-mining** | Partially available via the global Copilot; a **first-class always-on miner** is deferred. |
| **Predictive-maintenance scheduler, Energy/ESG module** | Net-new modules needing their **own data models**; deferred as larger feature work. |
| **Security hardening (encryption at rest, data residency, SOC2)** | **Deployment/ops concerns**, not application code — addressed at infra time. |

---

## Suggested next steps (highest leverage first)

1. **Slack/email alert push** — env-configurable (fires when a webhook is set, no-ops otherwise); makes the "proactive" story land with zero external dependency to *build*.
2. **Temporal async ingestion** — the container is already up; wiring it gives durable, retryable, non-blocking uploads.
3. **"View source" link** from Copilot citations — tiny change, closes the RAG credibility loop end-to-end.
4. **PDF report export** — add `reportlab`, template the agents' structured JSON.

---

*Status as of this build: all features in sections A–E are implemented and verified end-to-end (backend API + browser) against NeonDB + Neo4j, with two seeded plants (Karnataka / Delhi) and three users.*
