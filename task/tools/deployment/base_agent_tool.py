import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any

from aidial_client import AsyncDial
from aidial_sdk.chat_completion import Message, Role, CustomContent, Stage, Attachment, Status
from pydantic import StrictStr

from task.tools.base_tool import BaseTool
from task.tools.models import ToolCallParams
from task.utils.stage import StageProcessor


class BaseAgentTool(BaseTool, ABC):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    @property
    @abstractmethod
    def deployment_name(self) -> str:
        pass

    async def _execute(self, tool_call_params: ToolCallParams) -> str | Message:
        #TODO:
        # 1. All the agents that will used as tools will have two parameters in request:
        #   - `prompt` (the request to agent)
        #   - `propagate_history`, boolean whether we need to propagate the history of communication with called agent
        # 2. Use AsyncDial (api_version='2025-01-01-preview'), call the agent with steaming option.
        #    Here, actually, you can find one of the most powerful features of DIAL - Unified protocol. All the
        #    applications that provide `/chat/completions` endpoint and following Unified protocol - can `communicate`
        #    between each other though Unified protocol (that is OpenAI compatible), in other words, applications can
        #    `communicate` between each other like they communication with OpenAI models (Unified protocol is OpenAI compatible).
        #    The second powerful feature is that the application that makes the call provides with whole context and
        #    responsible to manage this context. So, like we calling the model and provide it with the whole history in
        #    the same way we are working with applications, the application that makes a call provide the conversation history.
        #    ⚠️ To provide proper message history you need to implement the `_prepare_messages` method!
        #    ⚠️ Don't forget to include as extra_headers `x-conversation-id`!
        # 3. Prepare:
        #   - `content` variable, here we will collect the streamed content
        #   - `custom_content: CustomContent` variable, here we will collect variable CustomContent from agent response
        #   - `stages_map: dict[int, Stage]` variable, here will be persisted propagated stages
        # 4. Iterate through chunks and:
        #   - Stream content to the Stage (from tool_call_params) for this tool call
        #   - For custom_content:
        #       - set `state` from response CustomContent to the `custom_content`
        #       - in attachments are found propagate them to choice
        #       - Optional:
        #           Stages propagation: convert response CustomContent to dict and if stages are present:
        #           - each Stage has it is `index`, it will be returned in each chunk. If stage by such index is present
        #             in `stages_map` then you need to propagate content, otherwise you need to create stage
        #           - propagate stage name from response to propagated stage name, the same story for `content` and `attachments`
        #           - if response stage has `status = completed` - we need to close such stage
        # 5. Ensure that stages are closed (just iterate through them and close safely with StageProcessor)
        # 6. Return Tool message
        #    ⚠️ Remember, tool message must have tool call id, also don't forget to add `custom_content` since we need
        #       to save properly tool history to choice state later
        client = AsyncDial(
            base_url=self.endpoint,
            api_key=tool_call_params.api_key,
            api_version='2025-01-01-preview'
        )

        chunks = await client.chat.completions.create(
            messages=self._prepare_messages(tool_call_params),
            stream=True,
            deployment_name=self.deployment_name,
            extra_headers={"x-conversation-id": tool_call_params.conversation_id},
        )

        content = ''
        custom_content: CustomContent = CustomContent(attachments=[])
        stages_map: dict[int, Stage] = {}

        chunks_iter = chunks.__aiter__()
        while True:
            try:
                chunk = await chunks_iter.__anext__()
            except StopAsyncIteration:
                break
            except Exception as e:
                # DIAL Core occasionally relays a keep-alive/partial chunk (e.g. missing
                # `id`/`created`) during long-running mesh calls; skip it instead of failing
                # the whole tool call, the stream continues right after.
                print(f"⚠️ Skipping malformed stream chunk from `{self.deployment_name}`. ", e)
                continue

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            if delta.content:
                tool_call_params.stage.append_content(delta.content)
                content += delta.content

            delta_custom_content = delta.custom_content
            if not delta_custom_content:
                continue

            if delta_custom_content.state is not None:
                custom_content.state = delta_custom_content.state

            if delta_custom_content.attachments:
                for delta_attachment in delta_custom_content.attachments:
                    attachment = Attachment(**delta_attachment.model_dump(exclude_none=True))
                    custom_content.attachments.append(attachment)
                    tool_call_params.choice.add_attachment(attachment=attachment)

            delta_custom_content_dict = delta_custom_content.model_dump(exclude_none=True)
            for stage_data in delta_custom_content_dict.get("stages", []) or []:
                index = stage_data.get("index")
                if index is None:
                    continue

                is_new_stage = index not in stages_map
                if is_new_stage:
                    stages_map[index] = StageProcessor.open_stage(
                        choice=tool_call_params.choice,
                        name=stage_data.get("name"),
                    )
                propagated_stage = stages_map[index]

                if stage_data.get("name") and not is_new_stage:
                    propagated_stage.append_name(stage_data["name"])

                if stage_data.get("content"):
                    propagated_stage.append_content(stage_data["content"])

                for stage_attachment in stage_data.get("attachments") or []:
                    propagated_stage.add_attachment(**stage_attachment)

                if stage_data.get("status") == Status.COMPLETED.value:
                    StageProcessor.close_stage_safely(propagated_stage)

        for stage in stages_map.values():
            StageProcessor.close_stage_safely(stage)

        return Message(
            role=Role.TOOL,
            name=StrictStr(tool_call_params.tool_call.function.name),
            tool_call_id=StrictStr(tool_call_params.tool_call.id),
            content=StrictStr(content),
            custom_content=custom_content,
        )

    def _prepare_messages(self, tool_call_params: ToolCallParams) -> list[dict[str, Any]]:
        #TODO:
        # In here we will manage the context for the agent that we are going to call.
        # We support two modes:
        #   - One-shot: only one user message to the Agent with prompt
        #   - Propagate whole Per-To-Per history between this Agent and the Agent that we are calling
        # ---
        # 1. Get: `prompt` and `propagate_history` params from tool call
        # 2. Prepare empty `messages` array, here we will collect history with Per-To-Per communication between this
        #    agent and the agent that we are colling
        # 3. Collect the proper history, iterate through messages and:
        #   - In Assistant messages presented the state with tool_call_history, we need to properly unpack it. If message
        #   from assistant and in custom content present state and in this state present history for this `self.name`
        #   (self.name is the key in state to get tool_call_history from the agent that we are going to call), then
        #   firstly add to `messages` user message that is going before the assistant message and then add assistant
        #   message. For assistant message you need to make a deepcopy and refactor the state for copied message, instead
        #   of the whole state you need to get from the state value by `self.name`
        # 4. Lastly, add the user message with `prompt` and don't forget about the custom_content
        arguments = json.loads(tool_call_params.tool_call.function.arguments)
        prompt: str = arguments["prompt"]
        propagate_history: bool = arguments.get("propagate_history", False)

        messages: list[dict[str, Any]] = []

        if propagate_history:
            for index, message in enumerate(tool_call_params.messages):
                if message.role != Role.ASSISTANT:
                    continue

                state = message.custom_content.state if message.custom_content else None
                if not (isinstance(state, dict) and self.name in state):
                    continue

                if index > 0:
                    messages.append(tool_call_params.messages[index - 1].dict(exclude_none=True))

                assistant_message = deepcopy(message)
                assistant_message.custom_content.state = state[self.name]
                messages.append(assistant_message.dict(exclude_none=True))

        attachments = None
        for message in reversed(tool_call_params.messages):
            if message.role == Role.USER:
                if message.custom_content and message.custom_content.attachments:
                    attachments = [
                        attachment.dict(exclude_none=True)
                        for attachment in message.custom_content.attachments
                    ]
                break

        messages.append(
            {
                "role": Role.USER.value,
                "content": prompt,
                "custom_content": {"attachments": attachments} if attachments else None,
            }
        )

        return messages