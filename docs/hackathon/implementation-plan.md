# Engineering Implementation Plan

This document outlines the step-by-step engineering tasks required to evolve SureFlow OS into the Industrial Intelligence Platform.

## Phase 1: Core Framework Extensions
1. **Extend `BaseBrain`**: Modify `backend/core/brain.py` if needed to support specific industrial output schemas, though the existing `BrainOutput` is highly flexible.
2. **Setup Vector DB Partitions**: Update `backend/core/database.py` and Alembic to ensure `10-oem-manuals`, `11-compliance-regs`, and `12-sops` pgvector collections exist.
3. **Extend Neo4j Driver**: Create `backend/knowledge_graph/industrial_store.py` (inheriting/wrapping `graph_store.py`) with the new Cypher schemas for Plant/Area/Equipment.

## Phase 2: Agent Development
Create the following files in `backend/agents/`:
1. `document_intelligence.py`: Implements OCR wrapping and layout extraction.
2. `search_agent.py`: Implements the hybrid Cypher + pgvector query generation.
3. `maintenance.py`: Agent for analyzing work orders and predicting failures.
4. `compliance.py`: Agent for cross-referencing audits with regulations.
5. `lessons_learned.py`: Agent for parsing incidents and updating Reflection Memory.

## Phase 3: Temporal Workflows
Create new activities in `backend/workflows/activities.py`:
1. `ocr_extract_activity`
2. `update_industrial_graph_activity`
3. `maintenance_analysis_activity`

Create the workflows in `backend/workflows/industrial_workflows.py`:
1. `DocumentIngestionWorkflow`
2. `MaintenanceLifecycleWorkflow`

## Phase 4: API & Connectors
1. **File Upload Endpoint**: Add a FastAPI route in `backend/api/routes.py` to accept PDF/Image uploads and trigger the `DocumentIngestionWorkflow`.
2. **MCP Extension**: Update `backend/core/mcp.py` to mock CMMS (e.g., SAP/Maximo) and IoT sensor endpoints instead of just LinkedIn/Hubspot.

## Phase 5: Frontend Refactoring
1. **Global CSS**: Update `frontend/src/globals.css` to the dark industrial theme.
2. **React Flow Integration**: Build the `KnowledgeGraphExplorer` component in `frontend/src/components/knowledge-graph/` to render Neo4j nodes.
3. **Copilot Component**: Enhance the existing chat interface to render `VisualizationBundle` charts natively using Recharts.
