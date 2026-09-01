from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class WebSearchAgentTool(BaseAgentTool):

    #TODO:
    # Provide implementations of deployment_name (in core config), name, description and parameters.
    # Don't forget to mark them as @property
    # Parameters:
    #   - prompt: string. Required.
    #   - propagate_history: boolean
    @property
    def deployment_name(self) -> str:
        return "web-search-agent"

    @property
    def name(self) -> str:
        return "web_search_agent"

    @property
    def description(self) -> str:
        return (
            "WEB Search Agent. Performs research in WEB based on the user request. Equipped with: WEB search "
            "(DuckDuckGo via MCP) and is able to fetch WEB pages content."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The request/prompt to send to the WEB Search Agent.",
                },
                "propagate_history": {
                    "type": "boolean",
                    "description": "Whether to propagate the whole Per-To-Per communication history with this agent.",
                },
            },
            "required": ["prompt"],
        }
