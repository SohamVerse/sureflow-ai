"""
CompanyOS V2 LangGraph — Autonomous Business Brain Pipeline

Architecture:
  CEO Brain → routes to specialist brains in parallel
  RISK Brain → has veto power; can reject CMO outputs back for revision
  Constitution Layer → validates every output before it reaches the user
  Debate Engine → CEO resolves conflicts between departments
  Reflection Loop → failures are saved to memory for future runs

Flow:
  CEO → [CMO, RESEARCH, SDR] (parallel)
      → RISK (reviews CMO + RESEARCH outputs)
      → AE (after SDR)
      → EMAIL (after AE or SDR)
      → FINALIZE (CEO synthesis + DB persistence)
"""
import json
import uuid
from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

from agents.orchestrator import ceo_analyze
from agents.content import cmo_draft_content
from agents.research import research_analyze
from agents.sales import sdr_score_lead, ae_qualify_lead
from agents.email import email_agent_draft
from agents.risk import risk_analyze
from agents.builder import build_graph_from_json
from core.memory import MemoryStore
from core.constitution import constitution


# ─── State Schema V2 ──────────────────────────────────────────────────────────

class AgentState(TypedDict):
    """Shared state passed between all LangGraph nodes."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    run_id: str                          # Correlates every agent call from this run (Phase 6 tracing)
    goal: str                            # Original user goal
    ceo_plan: dict                       # CEO routing plan
    cmo_output: dict                     # CMO drafted content
    research_output: dict                # Market research insights
    sdr_output: dict                     # SDR lead score & outreach
    ae_output: dict                      # AE qualification result
    email_output: dict                   # EMAIL marketing draft
    risk_output: dict                    # RISK analysis with veto decision
    lead_data: dict                      # Lead info for SDR/AE
    errors: Annotated[list[str], operator.add]
    completed_agents: Annotated[list[str], operator.add]
    constitution_violations: Annotated[list[str], operator.add]
    cmo_revision_count: int              # Track CMO revisions from veto
    debate_log: Annotated[list[str], operator.add]  # CEO debate/synthesis notes
    approval_required: bool              # If any output needs human approval


# ─── Node Functions ────────────────────────────────────────────────────────────

def ceo_node(state: AgentState) -> AgentState:
    """CEO Brain: Analyzes goal, produces routing plan with confidence/risk."""
    print(f"[CEO 🧠] Analyzing: {state['goal'][:80]}...")
    try:
        plan = ceo_analyze(state["goal"], run_id=state.get("run_id"))
        print(f"[CEO 🧠] Confidence: {plan.get('confidence', '?')}% | Risk: {plan.get('risk_level', '?')}")
        return {
            "ceo_plan": plan,
            "completed_agents": ["CEO"],
            "messages": [AIMessage(content=f"CEO Plan: {json.dumps(plan)}")],
            "approval_required": plan.get("confidence", 100) < 50,
        }
    except Exception as e:
        return {
            "ceo_plan": {},
            "errors": [f"CEO error: {str(e)}"],
            "approval_required": True,
        }


def cmo_node(state: AgentState) -> AgentState:
    """CMO Brain: Content strategy with full Reel scripts and image prompts."""
    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    cmo_task = next((t for t in tasks if t["agent"] == "CMO"), None)
    if not cmo_task:
        return {"cmo_output": {}}

    instruction = cmo_task["instruction"]
    print(f"[CMO 🎨] Drafting content: {instruction[:60]}...")
    try:
        output = cmo_draft_content(instruction, run_id=state.get("run_id"))

        # Constitution check
        violations = constitution.validate(output, agent_id="CMO")
        violation_msgs = [f"CMO: {constitution.summarize([v])}" for v in violations if v.severity == "blocker"]

        print(f"[CMO 🎨] Confidence: {output.get('confidence', '?')}% | Reach: {output.get('estimated_reach', '?')}")
        return {
            "cmo_output": output,
            "completed_agents": ["CMO"],
            "messages": [AIMessage(content=f"CMO Output: {json.dumps(output)[:500]}")],
            "constitution_violations": violation_msgs,
        }
    except Exception as e:
        return {
            "cmo_output": {},
            "errors": [f"CMO error: {str(e)}"],
        }


def research_node(state: AgentState) -> AgentState:
    """Research Analyst Brain: McKinsey-depth market intelligence."""
    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    research_task = next((t for t in tasks if t["agent"] == "RESEARCH"), None)
    if not research_task:
        return {"research_output": {}}

    instruction = research_task["instruction"]
    print(f"[RESEARCH 🔬] Analyzing: {instruction[:60]}...")
    try:
        output = research_analyze(instruction, run_id=state.get("run_id"))
        print(f"[RESEARCH 🔬] Confidence: {output.get('confidence', '?')}% | Trends found: {len(output.get('key_trends', []))}")
        return {
            "research_output": output,
            "completed_agents": ["RESEARCH"],
            "messages": [AIMessage(content=f"Research: {json.dumps(output)[:500]}")],
        }
    except Exception as e:
        return {
            "research_output": {},
            "errors": [f"Research error: {str(e)}"],
        }


def risk_node(state: AgentState) -> AgentState:
    """Risk Analysis Brain: Evaluates CMO+Research outputs. Can VETO campaigns."""
    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    risk_task = next((t for t in tasks if t["agent"] == "RISK"), None)

    cmo_output = state.get("cmo_output", {})
    research_output = state.get("research_output", {})

    # Run risk analysis if we have CMO content to evaluate, or if explicitly tasked
    if not cmo_output and not risk_task:
        return {"risk_output": {}}

    campaign_context = {
        "cmo_content": cmo_output,
        "goal": state.get("goal", ""),
        "ceo_plan_summary": ceo_plan.get("ceo_brief_summary", ""),
    }

    instruction = risk_task["instruction"] if risk_task else "Evaluate this campaign for risks."
    print(f"[RISK ⚠️] Evaluating campaign risk...")
    try:
        output = risk_analyze(campaign_context, research_output, instruction, run_id=state.get("run_id"))
        veto = output.get("veto_decision", {})
        go_no_go = output.get("go_no_go", "CONDITIONAL_GO")
        print(f"[RISK ⚠️] Decision: {go_no_go} | Failure Prob: {output.get('risk_dimensions', {}).get('campaign_failure_probability', '?')}%")

        # If vetoed, add to debate log
        debate_entries = []
        if veto.get("vetoed"):
            debate_entries.append(f"RISK VETO: {veto.get('veto_reason', 'High risk detected')}. Conditions to lift: {veto.get('conditions_to_unveto', [])}")

        return {
            "risk_output": output,
            "completed_agents": ["RISK"],
            "messages": [AIMessage(content=f"Risk: {go_no_go}")],
            "debate_log": debate_entries,
            "approval_required": veto.get("vetoed", False) or state.get("approval_required", False),
        }
    except Exception as e:
        return {
            "risk_output": {},
            "errors": [f"Risk error: {str(e)}"],
        }


def sdr_node(state: AgentState) -> AgentState:
    """SDR Brain: Lead qualification with ICP scoring and potential REJECT decision."""
    lead_data = state.get("lead_data", {})
    if not lead_data:
        return {"sdr_output": {}}

    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    sdr_task = next((t for t in tasks if t["agent"] == "SDR"), None)
    instruction = sdr_task["instruction"] if sdr_task else ""

    print(f"[SDR 📊] Scoring lead: {lead_data.get('name', 'Unknown')}")
    try:
        output = sdr_score_lead(lead_data, instruction, run_id=state.get("run_id"))
        verdict = output.get("lead_verdict", "NURTURE")
        print(f"[SDR 📊] Verdict: {verdict} | ICP Score: {output.get('icp_score', '?')}/10")

        debate_entries = []
        if verdict == "REJECT":
            debate_entries.append(f"SDR REJECTED lead: {output.get('rejection_reason', 'ICP mismatch')}")

        return {
            "sdr_output": output,
            "completed_agents": ["SDR"],
            "messages": [AIMessage(content=f"SDR: {json.dumps(output)[:300]}")],
            "debate_log": debate_entries,
        }
    except Exception as e:
        return {
            "sdr_output": {},
            "errors": [f"SDR error: {str(e)}"],
        }


def ae_node(state: AgentState) -> AgentState:
    """AE Brain: Deep qualification, stakeholder mapping, proposal and pricing."""
    sdr_output = state.get("sdr_output", {})
    icp_score = sdr_output.get("icp_score", 0)
    verdict = sdr_output.get("lead_verdict", "NURTURE")

    # AE only runs if SDR escalates or score is >= 7.0
    if verdict == "REJECT" or (icp_score < 7.0 and verdict not in ("ESCALATE_TO_AE", "escalate_to_ae")):
        print(f"[AE 💼] Skipping — ICP {icp_score} below threshold or SDR rejected.")
        return {"ae_output": {"skipped": True, "reason": f"SDR verdict: {verdict}, ICP score: {icp_score}"}}

    lead_data = state.get("lead_data", {})
    print(f"[AE 💼] Qualifying lead: {lead_data.get('name', 'Unknown')}")
    try:
        output = ae_qualify_lead(lead_data, run_id=state.get("run_id"))
        print(f"[AE 💼] Close probability: {output.get('close_probability', '?')}%")
        return {
            "ae_output": output,
            "completed_agents": ["AE"],
            "messages": [AIMessage(content=f"AE: {json.dumps(output)[:300]}")],
        }
    except Exception as e:
        return {
            "ae_output": {},
            "errors": [f"AE error: {str(e)}"],
        }


def email_node(state: AgentState) -> AgentState:
    """Email Brain: Personalized outreach with A/B variants and follow-up sequences."""
    lead_data = state.get("lead_data", {})
    if not lead_data:
        return {"email_output": {"skipped": True, "reason": "No lead data"}}

    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    email_task = next((t for t in tasks if t["agent"] == "EMAIL"), None)
    instruction = email_task["instruction"] if email_task else ""

    print(f"[EMAIL ✉️] Drafting outreach for: {lead_data.get('name', 'Unknown')}")
    try:
        output = email_agent_draft(lead_data, instruction, run_id=state.get("run_id"))
        print(f"[EMAIL ✉️] Predicted open rate: {output.get('performance_predictions', {}).get('estimated_open_rate', '?')}")
        return {
            "email_output": output,
            "completed_agents": ["EMAIL"],
            "messages": [AIMessage(content=f"EMAIL: {json.dumps(output)[:300]}")],
        }
    except Exception as e:
        return {
            "email_output": {},
            "errors": [f"EMAIL error: {str(e)}"],
        }


def finalize_node(state: AgentState) -> AgentState:
    """CEO Synthesis: Collect all outputs, run debate engine, log reflections."""
    completed = state.get("completed_agents", [])
    errors = state.get("errors", [])
    debate_log = state.get("debate_log", [])
    violations = state.get("constitution_violations", [])
    risk = state.get("risk_output", {})

    print(f"\n[FINALIZE 🏁] Agents completed: {completed}")
    if debate_log:
        print(f"[DEBATE ENGINE] Entries: {len(debate_log)}")
        for d in debate_log:
            print(f"  → {d}")
    if errors:
        print(f"[ERRORS] {errors}")

    # Save reflections for failed runs
    memory = MemoryStore()
    if errors:
        for err in errors:
            agent_id = err.split(" ")[0].strip("[]") if err else "UNKNOWN"
            memory.save_reflection(agent_id, state.get("goal", ""), err, "Investigate error cause and add retry logic.")

    return {}


# ─── CEO Router ────────────────────────────────────────────────────────────────

def ceo_router(state: AgentState) -> list[str]:
    """
    After CEO runs, determines which specialist brains to invoke in parallel.
    V2: Now includes RISK routing.
    """
    ceo_plan = state.get("ceo_plan", {})
    tasks = ceo_plan.get("tasks", [])
    agents_needed = {t["agent"] for t in tasks}

    next_nodes = []
    if "CMO" in agents_needed:
        next_nodes.append("cmo")
    if "RESEARCH" in agents_needed:
        next_nodes.append("research")
    if "SDR" in agents_needed and state.get("lead_data"):
        next_nodes.append("sdr")
    if "EMAIL" in agents_needed and state.get("lead_data"):
        next_nodes.append("email")

    return next_nodes if next_nodes else [END]


def post_parallel_router(state: AgentState) -> list[str]:
    """
    After parallel CMO/Research, route to Risk analysis.
    Risk should always run if we have CMO output.
    """
    next_nodes = []
    if state.get("cmo_output") or state.get("research_output"):
        next_nodes.append("risk")
    return next_nodes if next_nodes else ["finalize"]


# ─── Graph Definition V2 ──────────────────────────────────────────────────────

def build_sureflow_graph() -> StateGraph:
    """Build and compile the CompanyOS V2 LangGraph with Debate Engine."""
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("ceo", ceo_node)
    workflow.add_node("cmo", cmo_node)
    workflow.add_node("research", research_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("sdr", sdr_node)
    workflow.add_node("ae", ae_node)
    workflow.add_node("email", email_node)
    workflow.add_node("finalize", finalize_node)

    # Entry
    workflow.set_entry_point("ceo")

    # CEO routes to parallel specialists
    workflow.add_conditional_edges("ceo", ceo_router, {
        "cmo": "cmo",
        "research": "research",
        "sdr": "sdr",
        "email": "email",
        END: END,
    })

    # CMO and Research both converge at RISK (Debate Engine step)
    workflow.add_edge("cmo", "risk")
    workflow.add_edge("research", "risk")

    # SDR transitions to AE
    workflow.add_edge("sdr", "ae")

    # All converge at finalize
    workflow.add_edge("risk", "finalize")
    workflow.add_edge("ae", "finalize")
    workflow.add_edge("email", "finalize")

    workflow.add_edge("finalize", END)

    return workflow.compile()


# Singleton compiled graph
sureflow_graph = build_sureflow_graph()


# ─── Pipeline Runners ──────────────────────────────────────────────────────────

async def run_pipeline(goal: str, lead_data: dict = None) -> AgentState:
    """Run the full V2 pipeline and return final state."""
    initial_state: AgentState = {
        "messages": [HumanMessage(content=goal)],
        "run_id": str(uuid.uuid4()),
        "goal": goal,
        "ceo_plan": {},
        "cmo_output": {},
        "research_output": {},
        "sdr_output": {},
        "ae_output": {},
        "email_output": {},
        "risk_output": {},
        "lead_data": lead_data or {},
        "errors": [],
        "completed_agents": [],
        "constitution_violations": [],
        "cmo_revision_count": 0,
        "debate_log": [],
        "approval_required": False,
    }
    return await sureflow_graph.ainvoke(initial_state)


async def stream_pipeline(goal: str, lead_data: dict = None):
    """
    Streaming pipeline that yields JSON events as each brain completes.
    Frontend consumes these as SSE events.
    """
    run_id = str(uuid.uuid4())
    initial_state: AgentState = {
        "messages": [HumanMessage(content=goal)],
        "run_id": run_id,
        "goal": goal,
        "ceo_plan": {},
        "cmo_output": {},
        "research_output": {},
        "sdr_output": {},
        "ae_output": {},
        "email_output": {},
        "risk_output": {},
        "lead_data": lead_data or {},
        "errors": [],
        "completed_agents": [],
        "constitution_violations": [],
        "cmo_revision_count": 0,
        "debate_log": [],
        "approval_required": False,
    }

    # Synthetic first event — astream() only yields per-node deltas, and
    # run_id is static input rather than a node output, so it would never
    # otherwise reach api/routes.py's accumulated final_state.
    yield {"event": "run_started", "run_id": run_id}

    async for step_output in sureflow_graph.astream(initial_state):
        for node_name, state_update in step_output.items():
            yield {
                "event": "agent_update",
                "node": node_name,
                "update": state_update,
            }


async def stream_custom_pipeline(graph_json: str, goal: str, lead_data: dict = None):
    """Stream a user-defined agent pipeline from a React Flow graph JSON."""
    plan, errors = build_graph_from_json(graph_json)
    if errors:
        yield {"event": "error", "errors": errors}
        return

    for step in plan:
        agent = step["agent"]
        instruction = step["instruction"]

        output = {}
        if agent == "CEO":
            output = ceo_analyze(instruction)
        elif agent == "CMO":
            output = cmo_draft_content(instruction)
        elif agent == "RESEARCH":
            output = research_analyze(instruction)
        elif agent == "RISK":
            output = risk_analyze({"goal": goal, "instruction": instruction}, {}, instruction)
        elif agent == "SDR" and lead_data:
            output = sdr_score_lead(lead_data, instruction)
        elif agent == "AE" and lead_data:
            output = ae_qualify_lead(lead_data)
        elif agent == "EMAIL" and lead_data:
            output = email_agent_draft(lead_data, instruction)
        else:
            output = {"skipped": True, "reason": "Missing required context"}

        key_map = {
            "CMO": "cmo_output",
            "RESEARCH": "research_output",
            "SDR": "sdr_output",
            "AE": "ae_output",
            "EMAIL": "email_output",
            "RISK": "risk_output",
        }

        state_update = {key_map[agent]: output} if agent in key_map else {}
        yield {
            "event": "agent_update",
            "node": agent.lower(),
            "update": state_update,
        }
