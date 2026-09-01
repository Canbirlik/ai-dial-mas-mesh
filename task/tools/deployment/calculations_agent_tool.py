from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class CalculationsAgentTool(BaseAgentTool):

    #TODO:
    # Provide implementations of deployment_name (in core config), name, description and parameters.
    # Don't forget to mark them as @property
    # Parameters:
    #   - prompt: string. Required.
    #   - propagate_history: boolean
    @property
    def deployment_name(self) -> str:
        return "calculations-agent"

    @property
    def name(self) -> str:
        return "calculations_agent"

    @property
    def description(self) -> str:
        return (
            "Calculations Agent. Primary goal to to work with calculations. Capable to make plotly graphics and "
            "chart bars. Equipped with: Python Code Interpreter (via MCP), and Simple calculator."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request/prompt to send to the Calculations Agent.",
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the whole Per-To-Per communication history with this agent.",
                },
            },
            "required": ["prompt"],
        }

