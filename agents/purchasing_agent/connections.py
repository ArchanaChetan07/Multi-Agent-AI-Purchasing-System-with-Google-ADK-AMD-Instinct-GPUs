"""
Purchasing Agent — Remote Agent Connections

Manages authenticated HTTP connections to remote A2A seller agents.
Handles task dispatch, metadata propagation, and callback routing.
"""

import uuid
from typing import Callable

from utils.a2a_types import (
    AgentCard,
    Task,
    TaskArtifactUpdateEvent,
    TaskSendParams,
    TaskStatusUpdateEvent,
)
from utils.client import A2AClient

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """
    Wraps an A2AClient for a single remote agent.

    Responsibilities:
    - Establish an authenticated connection using the agent's auth scheme
    - Send tasks and route callbacks
    - Track pending tasks and propagate session metadata
    """

    def __init__(self, agent_card: AgentCard, agent_url: str, auth: str | None) -> None:
        self.agent_client = A2AClient(agent_card, auth=auth, agent_url=agent_url)
        self.card = agent_card
        self.pending_tasks: set[str] = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_task(
        self,
        request: TaskSendParams,
        task_callback: TaskUpdateCallback | None,
    ) -> Task | None:
        """
        Dispatch a task to the remote agent and process the response.

        Merges metadata from the request into the response so the root agent
        can correlate messages across the multi-agent conversation.
        """
        response = await self.agent_client.send_task(request.model_dump())
        _merge_metadata(response.result, request)

        # Propagate metadata and assign a fresh message ID to status messages
        if (
            hasattr(response.result, "status")
            and hasattr(response.result.status, "message")
            and response.result.status.message
        ):
            _merge_metadata(response.result.status.message, request.message)
            msg = response.result.status.message
            if not msg.metadata:
                msg.metadata = {}
            if "message_id" in msg.metadata:
                msg.metadata["last_message_id"] = msg.metadata["message_id"]
            msg.metadata["message_id"] = str(uuid.uuid4())

        if task_callback:
            task_callback(response.result, self.card)

        return response.result


def _merge_metadata(target, source) -> None:
    """Merge metadata from source into target, if both support it."""
    if not hasattr(target, "metadata") or not hasattr(source, "metadata"):
        return
    if target.metadata and source.metadata:
        target.metadata.update(source.metadata)
    elif source.metadata:
        target.metadata = dict(**source.metadata)
