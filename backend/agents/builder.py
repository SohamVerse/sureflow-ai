"""
Agent Builder — maps a UI-defined node graph (from React Flow) into a LangGraph execution plan.
This allows users to visually construct custom agent pipelines in the frontend,
which are serialized as JSON and executed here.
"""
from typing import Any
import json


VALID_AGENTS = {"CEO", "CMO", "RESEARCH", "SDR", "AE", "ANALYST"}


class AgentGraphBuilder:
    """
    Parses a React Flow graph definition (nodes + edges) and builds
    a structured execution plan for LangGraph.

    React Flow format expected:
    {
      "nodes": [{"id": "1", "data": {"agent": "CMO", "instruction": "..."}, "type": "agentNode"}],
      "edges": [{"id": "e1", "source": "1", "target": "2"}]
    }
    """

    def __init__(self, graph_definition: dict):
        self.nodes = {n["id"]: n for n in graph_definition.get("nodes", [])}
        self.edges = graph_definition.get("edges", [])
        self.adjacency: dict[str, list[str]] = {}
        self._build_adjacency()

    def _build_adjacency(self):
        for edge in self.edges:
            src = edge["source"]
            tgt = edge["target"]
            self.adjacency.setdefault(src, []).append(tgt)

    def validate(self) -> list[str]:
        """Return list of validation errors. Empty list = valid."""
        errors = []
        for node_id, node in self.nodes.items():
            agent = node.get("data", {}).get("agent", "")
            if agent not in VALID_AGENTS:
                errors.append(f"Node {node_id} has invalid agent type: '{agent}'. Must be one of {VALID_AGENTS}")
            instruction = node.get("data", {}).get("instruction", "")
            if not instruction.strip():
                errors.append(f"Node {node_id} (agent: {agent}) has no instruction defined.")
        return errors

    def get_execution_order(self) -> list[str]:
        """Topological sort of node IDs for sequential execution."""
        visited = set()
        order = []

        def dfs(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            for neighbor in self.adjacency.get(node_id, []):
                dfs(neighbor)
            order.append(node_id)

        for node_id in self.nodes:
            dfs(node_id)

        return list(reversed(order))

    def to_execution_plan(self) -> list[dict]:
        """
        Returns ordered list of agent task dicts:
        [{"node_id": "1", "agent": "CMO", "instruction": "...", "depends_on": ["0"]}]
        """
        order = self.get_execution_order()
        plan = []
        # Build reverse adjacency for dependency tracking
        depends: dict[str, list[str]] = {}
        for edge in self.edges:
            depends.setdefault(edge["target"], []).append(edge["source"])

        for node_id in order:
            node = self.nodes[node_id]
            plan.append({
                "node_id": node_id,
                "agent": node["data"].get("agent", ""),
                "instruction": node["data"].get("instruction", ""),
                "config": node["data"].get("config", {}),
                "depends_on": depends.get(node_id, []),
            })
        return plan


def build_graph_from_json(graph_json: str) -> tuple[list[dict], list[str]]:
    """
    Parse a React Flow graph JSON string and return (execution_plan, errors).
    """
    try:
        graph_definition = json.loads(graph_json)
    except json.JSONDecodeError as e:
        return [], [f"Invalid JSON: {str(e)}"]

    builder = AgentGraphBuilder(graph_definition)
    errors = builder.validate()
    if errors:
        return [], errors

    plan = builder.to_execution_plan()
    return plan, []
