import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from core.brain import BaseBrain, BrainOutput
from core.mcp import mcp_client

logger = logging.getLogger("automation")

class AutomationBrain(BaseBrain):
    """
    V2 Automation Brain:
    Responsible for executing scheduled tasks, monitoring system cron jobs, 
    and integrating directly with the MCP server to trigger external workflows.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="AUTOMATION",
            role="Scheduled Task & Workflow Executor",
            philosophy="Reliability and precision are paramount. Automation should run silently but log transparently."
        )

    def process(self, context: Dict[str, Any], instruction: str) -> BrainOutput:
        """Process an automation task."""
        # Check what external tool needs to be called
        platform = context.get("platform")
        action = context.get("action")
        params = context.get("params", {})
        
        # Risk assessment: Automation has low risk generally unless sending mass emails
        risk_score = 10
        if platform == "gmail" and action == "send_email":
            risk_score = 40
            
        # Execute via MCP
        mcp_result = {}
        if platform and action:
            mcp_result = mcp_client.execute_tool(platform, action, params)
            
        output_content = f"Executed {action} on {platform} via MCP. Result: {mcp_result}"
        
        return self._create_output(
            content=output_content,
            confidence_score=95,
            risk_score=risk_score,
            reasoning=f"Automation task triggered via schedule. Executed MCP tool {action} on {platform}.",
            alternatives=["Manual execution", "Delayed execution"],
            metadata={"mcp_result": mcp_result}
        )

# Singleton instance
automation_brain = AutomationBrain()

def trigger_automation(context: Dict[str, Any], instruction: str) -> dict:
    """Entry point for the automation brain."""
    output = automation_brain.process(context, instruction)
    return output.to_dict()
