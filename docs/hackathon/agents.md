# New Agent Ecosystem

By extending `core.brain.BaseBrain`, we will introduce the following specialized agents to SureFlow OS. They will all inherit the `BrainOutput` schema, allowing the existing CEO Orchestrator to natively manage them, track their confidence, and enforce human approval rules.

## 1. Document Intelligence Agent
- **Purpose**: Process raw industrial files into structured knowledge.
- **Inputs**: PDFs, DOCX, CSVs, P&IDs, Images.
- **Outputs**: Parsed Markdown, extracted entities, and vector embeddings.
- **Responsibilities**: 
  - Manage OCR processing.
  - Chunk documents intelligently (e.g., keeping table structures intact).
  - Extract metadata (Dates, Authors, Asset Tags).
- **Memory Usage**: Writes to Semantic Memory (pgvector).

## 2. Knowledge Graph Agent
- **Purpose**: Maintain the semantic relationships between industrial entities.
- **Inputs**: Extracted text and entities from the Document Intelligence Agent.
- **Outputs**: Cypher queries and updated Neo4j nodes/edges.
- **Responsibilities**:
  - Build the Industrial Ontology.
  - Deduplicate entities (e.g., recognizing "Pump-001" and "P-001" are the same asset).
  - Evolve the graph as new operational data arrives.
- **Memory Usage**: Direct read/write to `KnowledgeGraphStore`.

## 3. Industrial Copilot (Search Agent)
- **Purpose**: Provide the conversational interface and RAG reasoning.
- **Inputs**: User natural language queries.
- **Outputs**: Formatted responses with citations, confidence scores, and source links.
- **Responsibilities**:
  - Perform Hybrid Search (Vector + Metadata + Graph).
  - Synthesize answers from multiple sources (e.g., combining an OEM manual with a recent inspection report).
- **Memory Usage**: Reads from Semantic Memory and Knowledge Graph.

## 4. Maintenance Intelligence Agent
- **Purpose**: Act as the reliability engineering expert.
- **Inputs**: Maintenance logs, IoT sensor data, Equipment history.
- **Outputs**: Maintenance schedules, Failure predictions, Root Cause Analysis (RCA).
- **Responsibilities**:
  - Identify failure patterns across similar assets.
  - Recommend preventative maintenance before failure occurs.
- **Memory Usage**: Reads Episodic Memory (past work orders) and Knowledge Graph.

## 5. Compliance Agent
- **Purpose**: Ensure operations meet regulatory standards (ISO, OSHA, PESO).
- **Inputs**: Internal SOPs, Inspection records, External regulations.
- **Outputs**: Compliance gaps, Audit reports, Evidence packs.
- **Responsibilities**:
  - Automatically map inspection reports against required regulatory checklists.
  - Highlight missing documentation or expired certifications.
- **Memory Usage**: Reads Semantic Memory (Regulations) and Knowledge Graph (Inspections).

## 6. Lessons Learned Agent
- **Purpose**: Prevent historical mistakes from repeating.
- **Inputs**: Incidents, Near Misses, CAPA reports.
- **Outputs**: Proactive alerts, risk pattern reports.
- **Responsibilities**:
  - Mine unstructured incident logs to find recurring failures or problematic vendors.
  - Inject warnings into workflows (e.g., if a user creates a work order for a valve that has failed 3 times this month).
- **Memory Usage**: Reads and writes to Reflection Memory (Operational failures).
