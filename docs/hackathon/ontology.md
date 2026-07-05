# Industrial Ontology

To support the Industrial Knowledge Graph, we are expanding the existing Neo4j schema from purely strategic concepts (Competitors, Trends) to concrete industrial operations.

## Core Entities (Nodes)

### Spatial & Organizational
- **`Plant`**: The physical manufacturing or processing facility.
- **`Area`**: A specific zone or unit within the plant (e.g., "Cooling Tower Area").

### Asset
- **`AssetClass`**: The category of the equipment (e.g., `Pump`, `Valve`, `Motor`).
- **`Equipment`**: A specific physical instance of an asset (e.g., `P-101`).
- **`Sensor`**: An IoT device attached to equipment (e.g., `TempSensor-A`).
- **`Part`**: A component of an equipment (e.g., `Bearing-XYZ`).

### Documentation
- **`Document`**: The root document (e.g., `Manual`, `SOP`, `Regulation`, `Drawing`).
- **`DocumentChunk`**: A specific section of a document, linked to vector embeddings.

### Operational Events
- **`WorkOrder`**: A maintenance task.
- **`Inspection`**: A routine check or audit.
- **`Incident`**: A failure, near-miss, or safety event.
- **`Audit`**: A compliance check against a regulation.

### Personnel & External
- **`Operator` / `Engineer`**: Internal staff members.
- **`Vendor` / `OEM`**: Original Equipment Manufacturers or external suppliers.

---

## Core Relationships (Edges)

### Structural hierarchy
- `(Plant)-[:CONTAINS]->(Area)`
- `(Area)-[:CONTAINS]->(Equipment)`
- `(Equipment)-[:HAS_PART]->(Part)`
- `(Equipment)-[:HAS_SENSOR]->(Sensor)`

### Documentation Mapping
- `(Equipment)-[:HAS_MANUAL]->(Document)`
- `(Area)-[:GOVERNED_BY]->(Document {type: 'Regulation'})`
- `(Document)-[:CONTAINS_CHUNK]->(DocumentChunk)`

### Event Tracking
- `(Incident)-[:INVOLVED]->(Equipment)`
- `(Incident)-[:REPORTED_BY]->(Operator)`
- `(WorkOrder)-[:PERFORMED_ON]->(Equipment)`
- `(WorkOrder)-[:RESOLVED]->(Incident)`
- `(Inspection)-[:FOUND_DEFECT_IN]->(Equipment)`

### Vendor Relations
- `(Equipment)-[:MANUFACTURED_BY]->(OEM)`
- `(Part)-[:SUPPLIED_BY]->(Vendor)`
