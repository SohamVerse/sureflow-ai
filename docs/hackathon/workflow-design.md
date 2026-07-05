# Industrial Workflow Engine (Temporal)

SureFlow OS currently uses Temporal for orchestration (Layer 0), specifically to run the multi-agent pipeline (`run_pipeline`). We will introduce new deterministic Temporal workflows to handle the industrial lifecycle.

## 1. Document Ingestion Workflow
Triggered when a user uploads an industrial document.

```python
@workflow.defn
class DocumentIngestionWorkflow:
    @workflow.run
    async def run(self, file_path: str, doc_type: str):
        # 1. OCR and chunking (Non-deterministic, done in activity)
        raw_text = await workflow.execute_activity(
            ocr_extract_activity, file_path, start_to_close_timeout=timedelta(minutes=5)
        )
        
        # 2. Extract Entities and Metadata via Document Intelligence Agent
        entities = await workflow.execute_activity(
            agent_extraction_activity, raw_text, start_to_close_timeout=timedelta(minutes=2)
        )
        
        # 3. Store in Vector Vault (pgvector)
        await workflow.execute_activity(
            embed_and_store_activity, (raw_text, doc_type)
        )
        
        # 4. Update Knowledge Graph (Neo4j)
        await workflow.execute_activity(
            update_graph_activity, entities
        )
        
        return "Ingestion Complete"
```

## 2. Maintenance Lifecycle Workflow
Triggered when a new Work Order is created in the CMMS.

```python
@workflow.defn
class MaintenanceWorkflow:
    @workflow.run
    async def run(self, work_order_data: dict):
        # 1. Update Episodic Memory and Graph
        await workflow.execute_activity(record_work_order_activity, work_order_data)
        
        # 2. Invoke Maintenance Agent for RCA or Predictions
        prediction = await workflow.execute_activity(
            maintenance_agent_predict, work_order_data['equipment_tag']
        )
        
        # 3. If high risk, trigger notification/approval
        if prediction['risk_level'] in ['high', 'critical']:
            await workflow.execute_activity(alert_reliability_engineer, prediction)
```

## 3. Lessons Learned Pipeline
Triggered on a cron schedule (e.g., nightly) to review the day's incidents.
- Fetches all new incidents from the graph.
- Invokes the **Lessons Learned Agent**.
- Writes findings to **Reflection Memory**, ensuring the CEO and Copilot are aware of these new risks for future decision-making.
