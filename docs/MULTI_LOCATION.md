# SureFlow AI — Multi-Location (Multi-Plant) Extension

Design & scope document for extending SureFlow AI from a single-plant tool into a **multi-location enterprise platform**: many plants, each with isolated logins and data, plus a global **HQ / CTO** view that spans, compares, and provisions all of them.

> Read the base platform first: [`README.md`](../README.md).

---

## 1. Problem Statement

Today SureFlow AI assumes **one plant**. A real industrial enterprise runs **many plants** across regions. We need:

1. **Per-location login & isolation** — each plant's staff log in and see **only their own** equipment, incidents, documents, and AI insights. No cross-plant data leakage.
2. **A global HQ / CTO role** — a headquarters user who can:
   - access **every** plant,
   - **compare** plants side-by-side (KPIs, incident rates, compliance posture, uptime),
   - **provision new locations** (onboard a plant, seed its structure, invite its users),
   - ask the Copilot questions **across all plants** ("which plant has the worst PSV compliance?").
3. **Shared intelligence, isolated data** — lessons learned at one plant can *optionally* inform HQ-level cross-plant pattern detection, while raw operational data stays plant-scoped.

---

## 2. Personas & Roles (RBAC)

| Role | Scope | Can do |
|------|-------|--------|
| **Plant Operator** | One plant | View dashboards, upload docs, run AI analyses for their plant. |
| **Plant Manager** | One plant | Everything an operator can + manage their plant's users & settings. |
| **Global CTO / HQ** | All plants | Everything, across every plant + **compare plants** + **create/onboard new locations** + global Copilot. |

**Rule of thumb:** every request carries an authenticated identity → a role → an *effective plant scope*. Plant users are hard-locked to their `plant_id`; HQ users may pass a `target_plant_id` (one plant) or omit it (global).

---

## 3. What Already Exists ✅ vs. What To Build 🔨

The single→multi-plant groundwork is **partially in place** already:

| Area | Status | Notes |
|------|--------|-------|
| `Plant` node in Neo4j (Plant→Area→Equipment) | ✅ | Multiple plants already representable in the graph. |
| Graph reads scoped by `plant_id` | ✅ | `get_plant_hierarchy/get_all_equipment/get_all_incidents/get_graph_stats(plant_id=…)`. |
| Vector (RAG) search filtered by `plant_id` | ✅ | `query_collection(...)` filters on `VaultDocument.meta_data["plant_id"]`. |
| Memory reads scoped by `plant_id` | ✅ | `MemoryStore.get_oem_manual/... (plant_id=…)`. |
| Copilot RBAC (plant_manager vs cto/global) | ✅ | `search_agent` computes `effective_plant_id` from `user_role`, `user_plant_id`, `target_plant_id`. |
| Upload tags docs with `plant_id` | ✅ | `/industrial/upload` accepts `plant_id`, stored in chunk metadata. |
| Login page (frontend) | ✅ | `login/page.tsx` wired to real `/auth/login` via `AuthContext`. |
| Cloud Postgres (NeonDB) | ✅ | `DATABASE_URL` points at Neon — ready for shared multi-tenant data. |
| **Real authentication** (users, passwords, sessions/JWT) | ✅ | `models/auth.py` (`User`/`Location`), `core/security.py` (bcrypt+JWT), `api/auth_routes.py` (`/auth/login`, `/me`, `/users`). |
| **Auth enforcement** on every route (dependency) | ✅ | `api/deps.py` `get_current_user` + `resolve_scope` enforced on all industrial/HQ routes; scope derives from the JWT, not the body. |
| **Plant scoping on the other agents & dashboards** | ✅ | `plant_id` threaded through Maintenance / Compliance / Lessons / Copilot + all graph/KPI/equipment routes. |
| **Upload → graph writes tagged with `plant_id`** | ✅ | Every Neo4j node carries a denormalized `plant_id`; reads filter by it; uploads stamp the uploader's plant. |
| **HQ global dashboard & cross-plant comparison** | ✅ | `api/hq_routes.py` (`/hq/overview`, `/hq/compare`, `/hq/benchmark`) + `/industrial/hq` dashboard, compare & ranking. |
| **Location provisioning (create new plant)** | ✅ | `POST /plants` one-shot onboarding (plant + areas + first manager) + `/industrial/hq/locations` UI. |
| **Plant switcher + role-based navigation** (frontend) | ✅ | CTO plant switcher + role-gated Headquarters nav in the Sidebar. |

---

## 4. Architecture Changes

### 4.1 Authentication (AuthN)
- Add a `User` table (Postgres): `id, email, hashed_password, role, plant_id (nullable for HQ), name, created_at`.
- Add a `Location` (Plant) table (Postgres): `plant_id, name, location, timezone, status, created_by, created_at` — the relational mirror of the Neo4j `Plant` node (source of truth for auth/listing; Neo4j stays the operational graph).
- `/api/v1/auth/login` → verify credentials → issue a **JWT** containing `{ user_id, role, plant_id }`.
- `/api/v1/auth/me` → current user + role + accessible plants.
- Password hashing: `passlib[bcrypt]`. Token: `python-jose` (or `fastapi-users` if you want batteries-included).

### 4.2 Authorization (AuthZ) — enforce, don't trust the client
- A FastAPI dependency `get_current_user()` decodes the JWT on **every** protected route.
- A helper `resolve_scope(user, target_plant_id)` returns the **effective `plant_id`**:
  - Plant user → forced to `user.plant_id` (any `target_plant_id` they send is ignored/rejected).
  - HQ user → `target_plant_id` if given, else `None` (= global).
- **Never** derive scope from a client-supplied `user_role`/`plant_id` body field again — that's the current stub and is spoofable. Derive it from the verified token.

### 4.3 Data Scoping (isolation)
Every data path must carry `plant_id`:

- **Neo4j** — add a `plant_id` property to `Area`, `Equipment`, `Incident`, `WorkOrder`, `Inspection`, `Document` nodes (they already hang off a `Plant`, but a denormalized `plant_id` makes filtering cheap). Update `_merge_*` writers + `_read_*` readers to set/filter it. Reads already take `plant_id`; extend the write side (upload sync, seed) to stamp it.
- **pgvector** — already filters on `meta_data.plant_id`. Ensure **every** ingest sets it (upload does; backfill/seed must too).
- **Postgres memory** — add a `plant_id` column to `EpisodicMemory` and `ReflectionMemory`; filter reads by it.
- **RAG collections** — keep the 6 collection names global, but always filter by `plant_id` metadata (already the pattern). Do **not** create per-plant collections — metadata filtering scales better.

### 4.4 Agent Layer
Thread `effective_plant_id` into **all** agents (Copilot already done):
- `maintenance_analyze`, `compliance_analyze`, `lessons_learned_analyze` → pass `plant_id` into their graph + memory context gathering.
- Cross-plant mode (HQ, `plant_id=None`) → agents may aggregate across plants for comparison prompts.

### 4.5 HQ / Global Layer (new)
- **Aggregation endpoints** that fan out across plants and return comparison-ready shapes.
- **Location provisioning** endpoint (CTO-only) that creates the `Location` row + Neo4j `Plant` node + seeds the initial Area skeleton + creates the first plant-manager user.

---

## 5. New / Changed API Surface

```
POST   /api/v1/auth/login              # → JWT
GET    /api/v1/auth/me                 # current user, role, accessible plants
POST   /api/v1/auth/users              # (manager/CTO) invite/create a user for a plant

GET    /api/v1/plants                  # list plants (HQ: all; plant user: just theirs)
POST   /api/v1/plants                  # (CTO only) create/onboard a new location
GET    /api/v1/plants/{plant_id}       # plant profile + summary KPIs

GET    /api/v1/hq/overview             # (CTO) roll-up KPIs across all plants
GET    /api/v1/hq/compare?plants=A,B   # (CTO) side-by-side comparison metrics
POST   /api/v1/hq/copilot              # (CTO) global/cross-plant Copilot query

# All existing industrial routes gain an enforced plant scope from the token:
#   /industrial/upload, /copilot, /maintenance/analyze, /compliance/audit,
#   /lessons-learned, /graph/*, /kpis  → filtered to the caller's effective plant.
```

**Auth model:** protected routes require `Authorization: Bearer <jwt>`; scope is derived server-side from the token, never from request body fields.

---

## 6. Frontend Changes

| Page / Component | Purpose |
|------------------|---------|
| `/login` (finish) | Real login → store JWT → redirect by role (plant user → `/industrial`, HQ → `/hq`). |
| **Auth guard** | Redirect unauthenticated users to `/login`; attach `Bearer` token to every Axios call. |
| **Plant switcher** (HQ only) | Dropdown in the sidebar to set `target_plant_id`; drives all dashboards. |
| `/hq` **HQ dashboard** | Global roll-up: total plants, aggregate KPIs, worst-performing assets/plants, alerts. |
| `/hq/compare` | Side-by-side plant comparison (uptime, incidents, compliance score, MTBF) with charts. |
| `/hq/locations` + **"Add Location"** | CTO onboarding flow: create plant → seed areas → invite manager. |
| Role-based sidebar | Plant users see plant nav; HQ users see HQ nav + plant switcher. |
| Store (`store.ts`) | Add `currentUser`, `role`, `activePlantId`, `plants[]`; scope existing fetches by `activePlantId`. |

> Charts for the comparison view: load the **`dataviz`** skill before building them for a consistent, accessible palette.

---

## 7. Security & Isolation Checklist

- [ ] Scope derived from **verified JWT**, never client body (`user_role`/`plant_id` body fields are advisory only).
- [ ] Plant user requesting another plant's `plant_id` → **403**, not silently served.
- [ ] Every Neo4j read/write filters/stamps `plant_id`.
- [ ] Every pgvector query filters `meta_data.plant_id`; every ingest stamps it.
- [ ] Memory tables carry and filter `plant_id`.
- [ ] Passwords hashed (bcrypt); JWT signed with a secret in env; short expiry + refresh.
- [ ] HQ aggregation endpoints gated to `role == cto`.
- [ ] Audit log of location creation & user invites.
- [ ] Secrets (`DATABASE_URL`, `GEMINI_API_KEY`, JWT secret) in `.env`, never committed.

---

## 8. Phased Roadmap

**Phase 1 — Auth & enforcement (foundation)** ✅ **DONE**
`User`/`Location` tables · `/auth/login` + JWT · `get_current_user` dependency · `resolve_scope` · guard existing routes. *Outcome: real logins, plant users locked to their plant.*

**Phase 2 — Full data scoping** ✅ **DONE**
Stamp `plant_id` on all Neo4j writes + memory tables · thread `plant_id` through Maintenance/Compliance/Lessons · backfill existing data. *Outcome: every section is plant-isolated end-to-end.*

**Phase 3 — HQ view** ✅ **DONE**
`/plants`, `/hq/overview`, `/hq/compare` · HQ dashboard + plant switcher + comparison charts. *Outcome: CTO sees and compares all plants.*

**Phase 4 — Location provisioning** ✅ **DONE**
`POST /plants` one-shot onboarding (plant + areas + first manager) · "Add Location" UI at `/industrial/hq/locations`. *Outcome: CTO self-serves new plants.*

**Phase 5 — Cross-plant intelligence** ✅ **DONE**
Global HQ Copilot over all plants (`hqApi.copilot`, forced global scope) · reliability benchmarking & ranking (`/hq/benchmark`) · cross-plant reasoning verified. *(Deeper automated pattern-mining remains a future enhancement.)*

> **Status: Phases 1–5 implemented & verified end-to-end** against NeonDB + Neo4j with two plants (Karnataka / Delhi) and three users (CTO + 2 managers). Demo logins: `cto@sureflow.ai / Sureflow_CTO_2026!`, `karnataka@sureflow.ai / Sureflow_Plant_2026!`, `delhi@sureflow.ai / Sureflow_Plant_2026!`.

---

## 9. What This README Should Ensure Gets Built (Summary Checklist)

- [x] `User` + `Location` models & migrations
- [x] `/auth/login`, `/auth/me`, JWT, password hashing
- [x] `get_current_user` + `resolve_scope` enforced on all routes
- [x] `plant_id` on all Neo4j nodes (write + read) and memory tables
- [x] Maintenance / Compliance / Lessons agents plant-scoped (Copilot already is)
- [x] `/plants` CRUD + `POST /plants` (CTO onboarding)
- [x] `/hq/overview` + `/hq/compare` (+ `/hq/benchmark`) aggregation endpoints
- [x] Frontend: finished login, auth guard, plant switcher, `/hq` dashboard, comparison view, "Add Location"
- [x] Role-based navigation & data isolation verified (plant user cannot reach another plant)
- [x] Security checklist (§7) satisfied (scope from JWT, 403 cross-plant, hashed passwords, HQ gated)

---

### Design principles
1. **Isolate by default, share by exception** — data is plant-scoped unless HQ explicitly aggregates.
2. **Trust the token, not the client** — scope always derives from the verified JWT.
3. **One graph, one vector store, metadata-scoped** — multi-tenancy via `plant_id` filtering, not per-plant databases (simpler, and enables HQ cross-plant queries for free).
4. **Build on what's there** — the graph/RAG/memory/Copilot layers are already `plant_id`-aware; this extension is mostly *auth + enforcement + HQ surface*, not a rewrite.
