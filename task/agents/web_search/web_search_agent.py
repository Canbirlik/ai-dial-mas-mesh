from task.agents.base_agent import BaseAgent
from task.agents.web_search._prompts import SYSTEM_PROMPT
from task.tools.base_tool import BaseTool

#TODO:
# Just simply extend the BaseAgent and provide the constructor

class WebSearchAgent(BaseAgent):

    def __init__(self, endpoint: str, tools: list[BaseTool]):
        super().__init__(endpoint=endpoint, system_prompt=SYSTEM_PROMPT, tools=tools)
