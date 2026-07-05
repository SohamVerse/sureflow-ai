# Company Brain Evolution: Industrial Organizational Memory

The `core.memory.MemoryStore` in SureFlow OS is currently segmented into Episodic (runs), Reflection (failures), and Semantic (vaults). We will evolve this into an **Industrial Organizational Memory**.

## 1. Episodic Memory -> Asset & Incident Memory
Currently, Episodic Memory tracks `task`, `output_summary`, `confidence`, and `risk_level` for agent runs.

**Extension**: We will add domain-specific context. When the Maintenance Agent runs, the "episode" is tied to a specific `equipment_tag`. 
- **Asset Memory**: What did the Maintenance Agent conclude the last time it reviewed P-101?
- **Incident Memory**: What were the exact reasoning steps taken during the RCA of the last major outage?

## 2. Reflection Memory -> Lessons Learned Memory
Currently, Reflection Memory tracks `failure_reason` and `lesson` to correct agent behavior.

**Extension**: This becomes the core of the **Lessons Learned Intelligence**. Instead of just agent failures, it will store operational failures.
- **Failure Reason**: "Bearing failure on Pump-001 due to missed lubrication schedule."
- **Lesson**: "Always verify lubrication checklists for centrifugal pumps in Area 5 before signing off on weekly inspections."
- **Injection**: When the Compliance Agent or Copilot is asked about Area 5, this lesson is automatically injected into the prompt.

## 3. Semantic Memory -> Procedure & Compliance Memory
Currently, the Vault contains Marketing ICPs and Voice Profiles.

**Extension**: We will create new specialized collections in `pgvector`:
- `10-oem-manuals`: Dense, technical documentation.
- `11-compliance-regs`: OSHA, ISO, Factory Act text.
- `12-sops`: Internal Standard Operating Procedures.

## 4. Multi-Agent Interconnectivity
The true power of this evolution is that *all agents share this brain*.
- If the **Lessons Learned Agent** writes a new reflection about a safety incident...
- The **CEO Orchestrator** will see it in its `reflection_memory` prompt context...
- And will automatically factor it in when deciding how to route a new user request about safety audits.
