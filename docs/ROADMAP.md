# SureFlow AI — Product Roadmap & Future Enhancements

What to build next to make SureFlow AI a more complete, credible, and differentiated industrial-intelligence product. Prioritized by **impact vs. effort**, and grounded in the current codebase (see [`README.md`](../README.md)). Multi-plant is tracked separately in [`MULTI_LOCATION.md`](./MULTI_LOCATION.md).

> **The lens:** SureFlow's promise is *proactive* intelligence ("Downtime Down, Uptime Up"). Today the product is mostly **reactive & pull-based** (you open a dashboard and ask). The highest-value additions move it toward **proactive & push-based** (it tells *you*), and close the loop from *insight → action*.

> **✅ Shipped so far**, all plant-scoped to the multi-location model:
> - **Alerts & Notifications** — `models/alert.py`, `core/alerts.py`, `api/alert_routes.py`; sidebar bell badge + `/industrial/alerts` page (ack/resolve).
> - **Closed-loop Work Orders** — plant-scoped list/create/status + "Create Work Order" from a Maintenance recommendation + `/industrial/work-orders` page.
> - **Proactive Risk Digest** — `/alerts/digest` prioritized morning briefing, surfaced on the Alerts page.
> - **Document retention + viewer** — uploads retained + served plant-isolated via `/industrial/documents/{id}/file`.
> - **AI Quality & Cost panel** — `/system/ai-quality` + an AI Quality page (per-agent confidence/latency/cost).
> - **KPI Trends** — `KpiSnapshot` + `/industrial/kpis/trends` + a Trends page with line charts (dataviz spec).
> - **Global Search** — `/industrial/search` across equipment/incidents/documents/lessons + sidebar search box.
> - **CSV export** — `/industrial/export/*.csv` + download buttons.
>
> **Not built (need external systems / larger infra):** real MQTT/OPC-UA telemetry, SAP/Maximo CMMS, SSO/SAML, mobile PWA, digital-twin/P&ID view, Temporal async pipeline, and pushing alerts/digest to email/Slack (needs credentials + a scheduler).

---

## 0. Real gaps found in the current build (fix these first)

These are concrete, not hypothetical — observed in the code/tests:

| Gap | Where | Status |
|-----|-------|--------|
| **Uploaded document is deleted after processing** | `industrial_routes.py` → `os.unlink(tmp_path)` | ✅ **Fixed** — files retained under `backend/uploads/<plant>/`, served plant-isolated via `/industrial/documents/{id}/file`. |
| **No alerting / notifications** | — | ✅ **Fixed** — deterministic Alert generation (severe unresolved incidents, failed inspections) + in-app bell/page. Email/Slack push is the remaining channel work. |
| **Sensor data is mocked** | `core/mcp.py` (`iot_sensors` → random values) | 🔨 Open — one real MQTT/OPC-UA feed would make "live monitoring" real. |
| **Agent evaluation runs but is invisible** | `evaluation/evaluator.py` | 🔨 Open — data is collected; still needs an "AI quality & cost" panel. |
| **Ingestion runs synchronously inline** | upload route (Temporal exists but unused) | 🔨 Open — wire the existing Temporal workflow for durable async ingestion. |

---

## 1. Quick Wins — high impact, low effort (P0)

- **🔔 Alerts & Notifications.** ✅ **Done (in-app).** Deterministic generation from graph signals + sidebar bell + Alerts page (ack/resolve), plant-scoped. *Remaining:* email/Slack/Teams push channels.
- **📄 Report / data export.** ✅ **Done (CSV).** `/industrial/export/{equipment,incidents,work-orders}.csv` (plant-scoped) + "Export CSV" buttons on the Equipment and Work Orders pages. *Remaining:* branded PDF of an audit/RCA (needs a PDF lib).
- **📊 Trends over time.** ✅ **Done.** `KpiSnapshot` + `/industrial/kpis/{snapshot,trends}` + a **KPI Trends** page with per-metric line charts (2px marks, direct last-value labels, hover crosshair — built to the `dataviz` spec). *Remaining:* a real cron to capture snapshots (currently seeded/on-demand).
- **🗂️ Original document viewer.** ✅ **Done (backend).** Uploads retained + `/industrial/documents/{id}/file` serves the source, plant-isolated. *Remaining:* a "view source" link from citations in the UI.
- **🧪 AI Quality & Cost panel.** ✅ **Done.** `/system/ai-quality` aggregates the evaluator's per-agent confidence/latency/cost/schema-validity + an **AI Quality** page (totals, per-agent cards, recent runs).

---

## 2. Product-credibility features (P1)

- **⚙️ Closed-loop Work Orders.** ✅ **Done.** Create a work order from a Maintenance recommendation → track status (open→in_progress→completed) on the Work Orders page; plant-scoped. *Remaining:* feed completion back as an auto-lesson.
- **📅 Predictive maintenance scheduler.** Convert failure predictions into a **maintenance calendar** + spare-parts forecast. This is the tangible payoff of the prediction engine.
- **🔌 Real integrations (replace mock MCP).** Connectors for a real CMMS (SAP PM / IBM Maximo) and a historian (OSIsoft PI). Even one real connector changes the credibility story.
- **📡 Real-time telemetry.** MQTT / OPC-UA ingestion → live sensor streams → **streaming anomaly detection** → auto-raise incidents. Pairs with Alerts.
- **✅ Human-in-the-loop approvals.** High-risk agent recommendations require a manager's approval before action (the `requires_human_approval` field already exists in `BrainOutput` — surface it).
- **🔎 Global search.** ✅ **Done.** `/industrial/search` across equipment, incidents, documents, and lessons (plant-scoped) + a sidebar search box → results page.

---

## 3. Differentiators — make it stand out (P2)

- **🤖 Proactive Agent (autonomous daily scan).** ✅ **Done (on-demand).** `/alerts/digest` produces a **prioritized risk digest** with recommended actions ("Today's Risk Briefing" on the Alerts page). *Remaining:* run it on a schedule (cron) and push the digest by email.
- **🗺️ Digital twin / P&ID view.** Interactive plant map — click equipment on a diagram to see its live status, timeline, and AI insights. Highly demo-able.
- **🧠 Cross-asset & cross-plant pattern mining.** "3 pumps from the same OEM failed the same way in 6 months" → systemic recommendation. The lessons agent hints at this; make it a first-class, always-on capability.
- **🌱 Energy & ESG / sustainability module.** Energy consumption per asset, emissions estimates, ESG reporting — increasingly mandatory in industrial, and a fresh angle.
- **📈 Benchmarking.** ✅ **Done.** `/hq/benchmark` ranks plants by a reliability score (see [`MULTI_LOCATION.md`](./MULTI_LOCATION.md)). *Remaining:* asset/area-level ranking within a plant.

---

## 4. Enterprise & platform hardening (P3)

- **🔐 Auth, RBAC, SSO/SAML, audit log** — foundation for multi-plant (see [`MULTI_LOCATION.md`](./MULTI_LOCATION.md)).
- **🧱 Durable async pipeline** — activate Temporal for ingestion (retries, backpressure, progress).
- **🔒 Security & compliance** — encryption at rest/in transit, secrets management, data residency, SOC2-readiness.
- **📱 Mobile / PWA for field operators** — offline incident capture, photo upload, QR-scan an asset to see its history.
- **🌐 Data-ingestion breadth** — email-to-ticket, bulk spreadsheet import, entity-resolution review UI for messy data.
- **♻️ Observability for AI** — dashboards for agent cost, latency, failure/repair rates (Jaeger/Prometheus/Grafana already wired).

---

## 5. Suggested sequencing

```
Now (hackathon polish):   Alerts · Report export · Trends · Doc viewer · AI-quality panel
Next (credibility):       Closed-loop Work Orders · PdM scheduler · one real integration
Then (differentiate):     Proactive daily-digest agent · Digital-twin view · pattern mining
Platform (scale):         Auth/RBAC (multi-plant) · Temporal async · security hardening
```

**If you only add three things:** ① **Alerts/notifications**, ② **closed-loop work orders**, ③ the **proactive daily-digest agent**. Together they complete the loop — *detect → notify → act → learn* — which is the whole product thesis.

---

## 6. Mapping to the current architecture

| Enhancement | Reuses / touches |
|-------------|------------------|
| Alerts | new `alerts` service + agent thresholds; email/Slack SDK |
| Report export | agents' structured JSON → PDF template (`weasyprint`/`reportlab`) |
| Trends | new `kpi_snapshots` table; scheduled snapshot job; `dataviz` charts |
| Doc viewer | stop `os.unlink`; add blob storage + `Document.file_url` |
| Work-order loop | existing `WorkOrder` graph model + `/work-orders` route + UI |
| Real telemetry | replace `core/mcp.py` mock with MQTT/OPC-UA client |
| Proactive agent | new scheduled agent over `get_all_equipment` + existing brains |
| Human-in-loop | surface existing `requires_human_approval` in `BrainOutput` |
| Async pipeline | existing `workflows/` Temporal activities (currently bypassed) |
