# Future Roadmap: Beyond the Hackathon

While the hackathon focuses on core Document Intelligence, Graph mapping, and Maintenance predictability, the long-term vision for SureFlow Industrial OS expands into a complete autonomous facility manager.

## Q3 2026: Edge Computing & IoT Integration
- **Local Edge Agents**: Deploying lightweight Rust-based agents directly onto PLCs or edge gateways.
- **Real-time Stream Processing**: Moving from batch Work Order ingestion to real-time IoT time-series anomaly detection. The `Maintenance Agent` will subscribe to Kafka topics rather than just REST APIs.

## Q4 2026: Spatial & Vision Intelligence
- **Computer Vision Agent**: Ingesting live CCTV feeds to detect safety violations (e.g., missing hardhats, leaks) and automatically tying them to the Knowledge Graph `Area` nodes.
- **Digital Twin Integration**: Moving beyond 2D React Flow graphs to rendering 3D CAD/BIM models in the browser, overlaid with the agent's insights.

## Q1 2027: Autonomous Action (Closing the Loop)
Currently, SureFlow OS is an "Intelligence" and "Recommendation" platform (Human-in-the-loop). 
- **Auto-Procurement**: If the `Maintenance Agent` predicts a bearing failure, the `Builder Agent` uses the SAP MCP connector to automatically draft the Purchase Order for the replacement part.
- **Auto-Scheduling**: Integrating directly with the CMMS to assign Work Orders to specific technicians based on their `Operator Memory` (past performance and certifications).

## Scale and Architecture
- **Distributed Brains**: Scaling Temporal workers across Kubernetes clusters, allowing massive parallel processing of millions of documents simultaneously.
- **Federated Graphs**: Connecting multiple Plant Neo4j instances into a global Enterprise Graph, allowing the `Lessons Learned Agent` to share insights across continents.
