# Industrial Knowledge Graph Extension

The current system implements a Neo4j Knowledge Graph Store (`graph_store.py`) used by the Research Agent to track Competitors and Trends. 

To fulfill the hackathon requirements, we will extend this module to become the **Industrial Knowledge Graph (IKG)**. The IKG is crucial for enabling the Copilot to answer complex multi-hop queries (e.g., "Which operator performed maintenance on the valve that caused the incident in Area 5?").

## 1. Extension of `graph_store.py`

We will add a new class `IndustrialGraphStore` or extend the existing `KnowledgeGraphStore`.

### New Write Methods
- `record_document_ingestion(doc_id, entities, relationships)`: Called by the Document Intelligence Agent. Given a newly OCR'd manual, it writes nodes (Equipment, Vendor) and edges (HAS_MANUAL, MANUFACTURED_BY).
- `record_maintenance_event(work_order, equipment_tag, operator)`: Called when CMMS data is ingested.
- `record_incident(incident_report, equipment_tag)`: Called by the Lessons Learned Agent when parsing safety reports.

### New Read Methods
- `get_asset_timeline(equipment_tag)`: Traverses the graph to return all incidents, work orders, and inspections linked to a specific asset in chronological order.
- `get_compliance_gaps(area_id, regulation_id)`: Traverses `(Area)-[:GOVERNED_BY]->(Regulation)` and cross-references `(Inspection)-[:COVERED]->(Area)` to find missing checks.

## 2. Integration with the Search Agent (RAG + Graph)

The new **Search Agent** will implement a Hybrid Retrieval approach:
1. **Graph Traversal (Cypher)**: When the user asks "Show me the maintenance history for P-101", the Search Agent generates a Cypher query using `IndustrialGraphStore.get_asset_timeline('P-101')` to get the structured history.
2. **Vector Search (pgvector)**: Simultaneously, it queries the Semantic Memory to find unstructured notes about "P-101 vibration issues" in recent logs.
3. **Synthesis**: The Agent combines the structured graph data and unstructured RAG data to formulate a comprehensive answer with citations.

## 3. Graceful Degradation
Following the existing system's philosophy, if Neo4j goes down, the system should gracefully degrade to pgvector semantic search only, ensuring the Copilot remains online (albeit with reduced structural reasoning capabilities).
