import os
from contextlib import asynccontextmanager

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.calculations.calculations_agent import CalculationsAgent
from task.agents.calculations.tools.simple_calculator_tool import SimpleCalculatorTool
from task.tools.base_tool import BaseTool
from task.agents.calculations.tools.py_interpreter.python_code_interpreter_tool import PythonCodeInterpreterTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.deployment.web_search_agent_tool import WebSearchAgentTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME


#TODO:
# 1. Create CalculationsApplication class and extend ChatCompletion
# 2. As a tools for CalculationsAgent you need to provide:
#   - SimpleCalculatorTool
#   - PythonCodeInterpreterTool
#   - ContentManagementAgentTool (MAS Mesh)
#   - WebSearchAgentTool (MAS Mesh)
# 3. Override the chat_completion method of ChatCompletion, create Choice and call CalculationsAgent
# ---
# 4. Create DIALApp with deployment_name `calculations-agent` (the same as in the core config) and impl is instance of
#    the CalculationsApplication
# 5. Add starter with DIALApp, port is 5001 (see core config)

_PYINTERPRETER_MCP_URL = os.getenv('PYINTERPRETER_MCP_URL', "http://localhost:8050/mcp")


class CalculationsApplication(ChatCompletion):

    def __init__(self, app: DIALApp):
        self.app = app

    async def chat_completion(self, request: Request, response: Response) -> None:
        agent = CalculationsAgent(endpoint=DIAL_ENDPOINT, tools=self.app.state.tools)

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
    python_interpreter_tool = await PythonCodeInterpreterTool.create(
        mcp_url=_PYINTERPRETER_MCP_URL,
        tool_name="execute_code",
        dial_endpoint=DIAL_ENDPOINT,
    )

    app.state.tools = [
        SimpleCalculatorTool(),
        python_interpreter_tool,
        ContentManagementAgentTool(endpoint=DIAL_ENDPOINT),
        WebSearchAgentTool(endpoint=DIAL_ENDPOINT),
    ]
    try:
        yield
    finally:
        await python_interpreter_tool._mcp_client.close()


def _create_app() -> DIALApp:
    app = DIALApp(lifespan=_lifespan)
    app.add_chat_completion(
        deployment_name="calculations-agent",
        impl=CalculationsApplication(app=app),
    )
    return app


if __name__ == "__main__":
    app = _create_app()
    uvicorn.run(app, host="0.0.0.0", port=5001)