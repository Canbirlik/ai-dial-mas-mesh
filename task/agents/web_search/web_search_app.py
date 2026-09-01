import os
from contextlib import asynccontextmanager

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.web_search.web_search_agent import WebSearchAgent
from task.tools.base_tool import BaseTool
from task.tools.deployment.calculations_agent_tool import CalculationsAgentTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.mcp.mcp_client import MCPClient
from task.tools.mcp.mcp_tool import MCPTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME

_DDG_MCP_URL = os.getenv('DDG_MCP_URL', "http://localhost:8051/mcp")

#TODO:
# 1. Create WebSearchApplication class and extend ChatCompletion
# 2. As a tools for WebSearchAgent you need to provide:
#   - MCP tools by _DDG_MCP_URL
#   - CalculationsAgentTool (MAS Mesh)
#   - ContentManagementAgentTool (MAS Mesh)
# 3. Override the chat_completion method of ChatCompletion, create Choice and call WebSearchAgent
# ---
# 4. Create DIALApp with deployment_name `web-search-agent` (the same as in the core config) and impl is instance
#    of the WebSearchApplication
# 5. Add starter with DIALApp, port is 5003 (see core config)


class WebSearchApplication(ChatCompletion):

    def __init__(self, app: DIALApp):
        self.app = app

    async def chat_completion(self, request: Request, response: Response) -> None:
        agent = WebSearchAgent(endpoint=DIAL_ENDPOINT, tools=self.app.state.tools)

        with response.create_single_choice() as choice:
            await agent.handle_request(
                deployment_name=DEPLOYMENT_NAME,
                choice=choice,
                request=request,
                response=response,
            )


@asynccontextmanager
async def _lifespan(app: DIALApp):
    # The MCP client's connection (task group/streams) must be created in the same
    # event loop that will serve requests, so it's opened here (uvicorn's own loop)
    # instead of via a short-lived asyncio.run() before uvicorn starts.
    mcp_client = await MCPClient.create(_DDG_MCP_URL)
    mcp_tool_models = await mcp_client.get_tools()

    tools: list[BaseTool] = [
        MCPTool(client=mcp_client, mcp_tool_model=mcp_tool_model)
        for mcp_tool_model in mcp_tool_models
    ]
    tools.append(CalculationsAgentTool(endpoint=DIAL_ENDPOINT))
    tools.append(ContentManagementAgentTool(endpoint=DIAL_ENDPOINT))

    app.state.tools = tools
    try:
        yield
    finally:
        await mcp_client.close()


def _create_app() -> DIALApp:
    app = DIALApp(lifespan=_lifespan)
    app.add_chat_completion(
        deployment_name="web-search-agent",
        impl=WebSearchApplication(app=app),
    )
    return app


if __name__ == "__main__":
    app = _create_app()
    uvicorn.run(app, host="0.0.0.0", port=5003)
