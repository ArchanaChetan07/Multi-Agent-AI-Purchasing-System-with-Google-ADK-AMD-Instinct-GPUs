"""
Purchasing Concierge Agent (Root Agent)

Built with Google ADK + LiteLLM, backed by Ollama (Llama 3.1).

Responsibilities:
- Discover remote seller agents by resolving their Agent Cards
- Maintain a registry of RemoteAgentConnections
- Route user purchase requests to the appropriate seller agent via send_task()
- Track session state (active agent, session ID) across turns
- Stream responses back to the Gradio UI
"""

import json
import uuid
from typing import Callable, List

import httpx
import os

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext

from utils.a2a_types import (
    AgentCard,
    Message,
    Part,
    Task,
    TaskSendParams,
    TaskState,
    TextPart,
)
from utils.card_resolver import A2ACardResolver

from agents.purchasing_agent.connections import (
    RemoteAgentConnections,
    TaskCallbackArg,
    TaskUpdateCallback,
)

# ── Environment ───────────────────────────────────────────────────────────────
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "ollama_chat/llama3.1:latest")

_KNOWN_AUTH: dict[str, str] = {
    "pizza_seller_agent": os.getenv("PIZZA_SELLER_AGENT_AUTH", "pizza123"),
    "burger_seller_agent": os.getenv("BURGER_SELLER_AGENT_AUTH", "burgeruser123:burgerpass123"),
}


class PurchasingAgent:
    """
    Google ADK root agent that orchestrates the multi-agent purchasing system.

    On initialisation it resolves Agent Cards from all known seller URLs,
    builds a connection registry, and creates the ADK Agent with the send_task
    tool as its primary capability.
    """

    def __init__(
        self,
        remote_agent_addresses: List[str],
        task_callback: TaskUpdateCallback | None = None,
    ) -> None:
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}

        for address in remote_agent_addresses:
            self._register_agent(address)

        agent_info = [json.dumps(ra) for ra in self.list_remote_agents()]
        self.agents_summary = "\n".join(agent_info)

    def _register_agent(self, address: str) -> None:
        """Resolve an agent card and register the connection."""
        resolver = A2ACardResolver(address)
        try:
            card = resolver.get_agent_card()
            auth = _KNOWN_AUTH.get(card.name)
            connection = RemoteAgentConnections(
                agent_card=card, agent_url=address, auth=auth
            )
            self.remote_agent_connections[card.name] = connection
            self.cards[card.name] = card
            print(f"[PurchasingAgent] Registered agent: {card.name} @ {address}")
        except httpx.ConnectError:
            print(f"[PurchasingAgent] ERROR: Could not reach agent at {address}")

    def create_agent(self) -> Agent:
        """Build and return the Google ADK Agent instance."""
        return Agent(
            model=LiteLlm(model=_OLLAMA_MODEL),
            name="purchasing_agent",
            instruction=self._root_instruction,
            before_model_callback=self._before_model_callback,
            description=(
                "Orchestrates user purchase requests by delegating tasks "
                "to the appropriate remote seller agents."
            ),
            tools=[self.send_task],
        )

    def _root_instruction(self, context: ReadonlyContext) -> str:
        """Dynamic system prompt that includes current agent registry and active agent."""
        active = self._check_active_agent(context)["active_agent"]
        return f"""You are an expert purchasing delegator. Your job is to route the
user's food inquiry or purchase request to the correct remote seller agent.

Execution rules:
- Use `send_task` to assign work to a remote agent.
- Never ask the user for permission before connecting to a remote agent.
- If a remote agent asks for confirmation and the user has already confirmed
  in this conversation, confirm on their behalf.
- Always relay the full response from the seller agent to the user.
- Do not pass pizza context to the burger agent or vice versa.
- Never make up menu items, prices, or order IDs.
- Focus on the most recent part of the conversation.

Available agents:
{self.agents_summary}

Current active seller agent: {active}
"""

    def _check_active_agent(self, context: ReadonlyContext) -> dict:
        state = context.state
        if (
            state.get("session_id")
            and state.get("session_active")
            and state.get("active_agent")
        ):
            return {"active_agent": state["active_agent"]}
        return {"active_agent": "None"}

    def _before_model_callback(self, callback_context: CallbackContext, llm_request) -> None:
        """Initialise session state on the first turn."""
        state = callback_context.state
        if not state.get("session_active"):
            if "session_id" not in state:
                state["session_id"] = str(uuid.uuid4())
            state["session_active"] = True

    def list_remote_agents(self) -> list[dict]:
        """Return name + description for each registered remote agent."""
        return [
            {"name": card.name, "description": card.description}
            for card in self.cards.values()
        ]

    async def send_task(
        self,
        agent_name: str,
        task: str,
        tool_context: ToolContext,
    ) -> list[str]:
        """
        Delegate a task to a named remote seller agent via the A2A protocol.

        Args:
            agent_name: Name matching the remote agent's Agent Card.
            task: Full context summary and goal for the remote agent.
            tool_context: ADK tool context providing state access.

        Returns:
            List of text response parts from the remote agent.

        Raises:
            ValueError: If the named agent is not registered.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(
                f"Agent '{agent_name}' not found. "
                f"Available: {list(self.remote_agent_connections)}"
            )

        state = tool_context.state
        state["active_agent"] = agent_name

        client = self.remote_agent_connections[agent_name]
        task_id = state.get("task_id", str(uuid.uuid4()))
        session_id = state["session_id"]

        # Build metadata for message correlation
        metadata: dict = {}
        message_id = ""
        if input_meta := state.get("input_message_metadata"):
            metadata.update(input_meta)
            message_id = input_meta.get("message_id", "")
        if not message_id:
            message_id = str(uuid.uuid4())
        metadata.update({"conversation_id": session_id, "message_id": message_id})

        request = TaskSendParams(
            id=task_id,
            sessionId=session_id,
            message=Message(
                role="user",
                parts=[TextPart(text=task)],
                metadata=metadata,
            ),
            acceptedOutputModes=["text", "text/plain"],
            metadata={"conversation_id": session_id},
        )

        completed_task: Task = await client.send_task(request, self.task_callback)

        # Update session state based on task outcome
        state["session_active"] = completed_task.status.state not in [
            TaskState.COMPLETED,
            TaskState.CANCELED,
            TaskState.FAILED,
            TaskState.UNKNOWN,
        ]

        if completed_task.status.state == TaskState.INPUT_REQUIRED:
            tool_context.actions.escalate = True
        elif completed_task.status.state == TaskState.COMPLETED:
            state["active_agent"] = "None"

        # Collect text parts from status message and artifacts
        response_parts: list[str] = []
        if completed_task.status.message:
            response_parts.extend(
                _extract_text_parts(completed_task.status.message.parts)
            )
        for artifact in (completed_task.artifacts or []):
            response_parts.extend(_extract_text_parts(artifact.parts))

        return response_parts


def _extract_text_parts(parts: list[Part]) -> list[str]:
    """Extract text content from A2A Part objects."""
    return [p.text for p in parts if p.type == "text"]
