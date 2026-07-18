# 📚 SureFlow OS — Documentation

Everything written about the project, organized by what you're trying to do.
For the product overview and quick start, go back to the **[root README](../README.md)**.

---

## 🚦 Start here

| If you want to... | Read |
|---|---|
| **Get it running** | [GETTING_STARTED.md](./GETTING_STARTED.md) |
| **Fix something that broke** | [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) |
| **Present or demo the project** | [DEMO_SCRIPT.md](./DEMO_SCRIPT.md) |
| **Know exactly what's built** | [PROJECT_STATUS.md](./PROJECT_STATUS.md) |

---

## 📖 Core documentation

### [GETTING_STARTED.md](./GETTING_STARTED.md)
Complete setup. Covers both the **Docker path** (everything containerized, recommended) and the
**local-dev path** (backend on the host with hot-reload). Includes environment configuration,
database seeding, and how to verify each piece is actually working.

### [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
Concrete fixes for the failures you're most likely to hit — Docker build errors on OneDrive-synced
folders, port conflicts, login redirect loops, Gemini quota exhaustion, and empty dashboards.

### [PROJECT_STATUS.md](./PROJECT_STATUS.md)
The honest feature inventory: everything implemented, plus a table of what **isn't** built and the
specific reason each item was deferred. Read this before judging scope.

### [MULTI_LOCATION.md](./MULTI_LOCATION.md)
The multi-plant architecture: the `User`/`Location` model, JWT-derived scope resolution, how
`plant_id` denormalization enforces isolation at the graph level, and the HQ roll-up layer.

### [ROADMAP.md](./ROADMAP.md)
What to build next, prioritized by impact vs. effort and grounded in the current codebase.

### [DEMO_SCRIPT.md](./DEMO_SCRIPT.md)
A guided 8–10 minute walkthrough for presenting the platform against the seeded demo dataset.

### [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md)
The detailed phase-by-phase implementation guide (Phases 1–5).

---

## 🏛 Deep dives

### [`architecture/`](./architecture/)
- **[current-system-analysis.md](./architecture/current-system-analysis.md)** — full system analysis

### [`hackathon/`](./hackathon/)
Design documents produced while building:

| Document | Covers |
|---|---|
| [architecture.md](./hackathon/architecture.md) · [technical-architecture.md](./hackathon/technical-architecture.md) | System and technical design |
| [agents.md](./hackathon/agents.md) | The six-agent design |
| [knowledge-graph.md](./hackathon/knowledge-graph.md) · [ontology.md](./hackathon/ontology.md) | Graph schema and ontology |
| [workflow-design.md](./hackathon/workflow-design.md) | Pipeline and workflow design |
| [gap-analysis.md](./hackathon/gap-analysis.md) | Where the product falls short |
| [ui-recommendations.md](./hackathon/ui-recommendations.md) | Interface direction |
| [implementation-plan.md](./hackathon/implementation-plan.md) · [roadmap.md](./hackathon/roadmap.md) · [future-roadmap.md](./hackathon/future-roadmap.md) | Planning |
| [demo-script.md](./hackathon/demo-script.md) | Earlier demo draft |

---

## 🗺 Documentation map

```
sureflow-ai/
├── README.md                      ← product overview + quick start
└── docs/
    ├── README.md                  ← you are here
    ├── GETTING_STARTED.md         ← full setup
    ├── TROUBLESHOOTING.md         ← when things break
    ├── DEMO_SCRIPT.md             ← presenting it
    ├── PROJECT_STATUS.md          ← what's built / what isn't
    ├── MULTI_LOCATION.md          ← multi-plant design
    ├── ROADMAP.md                 ← what's next
    ├── IMPLEMENTATION_STATUS.md   ← phase-by-phase guide
    ├── architecture/              ← system analysis
    └── hackathon/                 ← design documents
```
