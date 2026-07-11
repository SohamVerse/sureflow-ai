# SureFlow OS — Industrial Intelligence Demo Script

A guided walkthrough for presenting the Industrial Intelligence Platform (Petrochemical Complex Alpha demo dataset). ~8-10 minutes end to end.

---

## 0. Setup Checklist (do this before the room fills up)

1. `docker-compose up -d` — PostgreSQL, Neo4j, Temporal, Jaeger.
2. `ollama pull nomic-embed-text` (once).
3. Backend: `cd backend && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`
4. Seed demo data (idempotent, safe to re-run): `.venv\Scripts\python.exe scripts/seed_industrial_data.py`
5. Frontend: `cd frontend && npm run dev` → `http://localhost:3000/industrial`
6. **OCR (optional but recommended for the upload demo):** install [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/). If Tesseract isn't on your PATH, set in `backend/.env`:
   ```
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   POPPLER_PATH=C:\poppler\Library\bin
   ```
   Without these installed, image/scanned-PDF uploads still work — they just fall back to placeholder text (a warning is logged), and PDF/TXT/DOCX/MD all extract normally regardless.
7. Have one real-world-looking test file ready to upload: a photographed/scanned page (`.jpg`/`.png`) or a short `.docx` — this is what makes the OCR + live pipeline feel real.

---

## 1. Open on the Knowledge Graph Explorer (`/industrial`)

**Say:** "This is a petrochemical plant's digital twin — Plant → Area → Equipment, backed by a live Neo4j graph, not a static mockup."

- Point out the plant hierarchy tree (1 plant, 5 areas, 12 pieces of equipment).
- Click into an area (e.g. **Pump House A**) and then equipment **P-101** to show its detail panel: manufacturer (Flowserve), install info, incident/work-order timeline.
- Mention the KPI tiles up top are read from the same graph, not hardcoded.

## 2. Upload a Document — live SSE pipeline (`/industrial/upload`)

**Say:** "Watch the pipeline run in real time — this isn't a fake progress bar, each step below lights up only once the backend has actually finished it."

- Drag in your test file (scanned image or `.docx`).
- Narrate each stage as it lights up: **Extracting text** (real OCR via Tesseract if installed, or native PDF/DOCX/text parsing) → **AI Document Analysis** (Gemini extracts entities/relationships) → **Embedding into Vector Store** (pgvector) → **Updating Knowledge Graph** (Neo4j).
- Point at the result card: entities found, chunks embedded, graph nodes created, and the AI-generated summary.

## 3. Ask the Industrial Copilot (`/industrial/copilot`)

**Say:** "This is the plant engineer's single point of entry — it fuses the knowledge graph, OEM manuals, SOPs, and past incidents into one cited answer."

Run these four, in order, and pause on each:

1. **Equipment lookup:** *"Show me the maintenance history for pump P-101"*
   → Answer should reference INC-001 (bearing failure) and WO-1001/WO-1004.
2. **Root cause / RCA:** *"Explain the root cause of the bearing failure on P-101"*
   → Point out inline citations, then **expand "AI Reasoning"** under the answer — show the chain-of-thought, confidence %, risk badge, and self-challenge critique. This is the same reasoning every agent produces, just finally visible.
3. **Compliance:** *"What are the compliance gaps in Pump House A?"*
4. **Cross-asset lesson:** *"What lessons have we learned from recent incidents?"*
   → Click one of the suggested **follow-up questions** chips to show the conversational loop.

While a query is running, call out the live stage label ("Querying knowledge graph…" → "Synthesizing answer…") — real progress feedback instead of a spinner.

## 4. Maintenance Intelligence (`/industrial/maintenance`)

- Select **P-101**, analysis type **Full**, click **Run Analysis**.
- Walk through: 5-Why root cause chain, failure probability gauge, estimated remaining life, MTBF.
- Expand **AI Reasoning** again — same contract, different agent, reinforcing this is a platform capability, not a one-off Copilot feature.

## 5. Compliance Dashboard (`/industrial/compliance`)

- Scope: **Facility-wide** → **Run Audit**.
- Show the audit-readiness ring, SOP compliance bar, and the gap list with severity badges.

## 6. Close on KPIs (`/industrial` dashboard)

- Return to the overview: lessons-learned count, safety incidents, graph size — tie it back to "everything you just saw is reflected here in real time."

---

## What's Real AI vs. Mocked (say this out loud — don't overclaim)

| Component | Status |
|---|---|
| Document Intelligence, Search/Copilot, Maintenance, Compliance, Lessons Learned, KG Agent | **Real** — Gemini-backed LLM calls with structured JSON contracts |
| Knowledge Graph (Neo4j), pgvector semantic search, Reflection/Episodic memory | **Real** — live database reads/writes |
| OCR (image files, scanned PDFs), DOCX parsing | **Real** if Tesseract/Poppler are installed locally; otherwise gracefully degrades to placeholder text with a logged warning |
| CMMS (SAP PM) work orders, IoT sensor readings | **Mocked** — deterministic mock data standing in for a real plant historian/SAP integration, clearly labeled as such in the API (`/industrial/mcp/*`) |

---

## Fallback Notes

- If Neo4j/Ollama is briefly unreachable, most read paths degrade gracefully (empty results + a logged warning) rather than crashing — safe to keep talking.
- If Gemini rate-limits mid-demo, `ModelBroker` automatically falls back to a local Ollama model — the demo keeps running, just with a shorter/plainer answer.
