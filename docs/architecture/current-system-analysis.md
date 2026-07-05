# SureFlow OS — Current System Analysis

## 1. Architecture Overview
SureFlow OS is a generalized multi-agent operating system designed for company management, powered by local LLMs via Ollama, structured around a central "Company Brain." It utilizes a deterministic workflow engine (Temporal) to orchestrate non-deterministic AI agents.

The core paradigm is an "OS" for the company where different functions (CEO, CMO, Sales, Research) are specialized agents that follow a unified cognitive contract (`BrainOutput`) and share collective memory.

## 2. Folder Breakdown
- **`backend/`**: FastAPI python server acting as the intelligence layer.
  - **`agents/`**: Contains specialized agents (e.g., `orchestrator.py` [CEO], `research.py`, `sales.py`, `content.py`).
  - **`core/`**: The fundamental cognitive framework (`brain.py`, `memory.py`, `mcp.py`, `constitution.py`).
  - **`knowledge_graph/`**: Neo4j driver and extraction logic for maintaining strategic knowledge (competitors, trends).
  - **`rag/`**: Vector store implementations (pgvector) for semantic memory (vault).
  - **`workflows/`**: Temporal workflow orchestrations (`activities.py`, `worker.py`).
- **`frontend/`**: Next.js React application (using React Flow for visual graph representation, Recharts for analytics).
- **`observability/`**: Infrastructure for Jaeger, Prometheus, and Grafana.

## 3. Component Relationships
1. **Frontend to Backend**: Next.js communicates with FastAPI via REST endpoints (under `/api/v1`).
2. **Backend to Temporal**: FastAPI enqueues tasks and pipelines to the Temporal worker via the Temporal client.
3. **Temporal to Agents**: The `run_pipeline` activity invokes the CEO agent (Orchestrator), which then routes tasks to sub-agents (CMO, AE, etc.).
4. **Agents to Memory**: Agents use `core.memory.MemoryStore` to read/write Episodic, Reflection, and Semantic memory from PostgreSQL (pgvector).
5. **Agents to Knowledge Graph**: Agents (specifically Research) write extracted entities (Competitors, Trends) to Neo4j.

## 4. Agent Responsibilities
All agents inherit from `BaseBrain` and return a standard `BrainOutput`.
- **CEO (Orchestrator)**: Strategic goal decomposition, KPI routing, budget allocation, and task delegation.
- **Research**: Competitor intelligence, market trend extraction (writes to Neo4j).
- **CMO / Content**: Strategy, branding, marketing material generation.
- **Sales (SDR / AE)**: Lead qualification, email campaigns.
- **Risk**: Evaluating plans for catastrophic risk and opportunity cost.
- **Automation (Builder)**: Tool usage and external actions.

## 5. Memory Architecture
Unified through `MemoryStore` in PostgreSQL/pgvector:
- **Episodic Memory**: Past task runs and outcomes ("What did I do last time?").
- **Reflection Memory**: Failures and lessons learned (Self-correction loop).
- **Semantic Memory (Vault)**: pgvector RAG for ICP, Voice Profile, Content Pillars, and Research context.
- **Working Memory**: Current LangGraph AgentState.
- **Procedural Memory**: Standard Operating Procedures (SOPs) embedded in the vault.

## 6. Knowledge Architecture (Graph)
Implemented via Neo4j (`graph_store.py`). 
- Currently specialized for **Strategic Knowledge** (Competitors, Trends).
- Nodes represent `Competitor`, `Trend`, and `ResearchRun`.
- Relationships track which research runs identified which competitors/trends, creating a provenance-tracked graph of market beliefs.

## 7. Existing Strengths
- **Modular Cognitive Contract**: Every agent returning a standardized `BrainOutput` makes the system highly extensible.
- **Memory Tiers**: The split between Episodic, Reflection, and Semantic memory closely mirrors human cognition and prevents context window bloat.
- **Temporal Orchestration**: Extremely robust handling of long-running, multi-step agent workflows.
- **Local-First & Private**: Designed to run entirely on local LLMs (Ollama) and local infrastructure (Docker).

## 8. Existing Limitations
- **Narrow Graph Scope**: Neo4j is currently only used for market research (Competitors/Trends), not operational entity mapping.
- **RAG Specialization**: Semantic memory is partitioned into specific marketing/company domains (e.g., `01-voice`, `02-icp`), lacking universal document extraction and OCR pipelines for complex files (PDFs, P&IDs).
- **Generic Connectors**: External tool usage via MCP is mocked or limited to social media/emails rather than industrial IoT or CMMS systems.

## 9. Extension Points for Industrial Intelligence
- **Agent Framework**: We can add new agents (Maintenance Agent, Compliance Agent) by extending `BaseBrain` without touching existing agents.
- **MemoryStore**: We can add new semantic partitions (e.g., `10-asset-manuals`, `11-compliance-sops`) to pgvector.
- **GraphStore**: Neo4j can easily handle industrial ontology (Plant -> Area -> Equipment -> Incident) by just defining new node types and extraction logic.
- **Temporal Workflows**: We can add new workflows for `document_ingestion` and `maintenance_lifecycle` alongside the existing sales/marketing pipelines.
