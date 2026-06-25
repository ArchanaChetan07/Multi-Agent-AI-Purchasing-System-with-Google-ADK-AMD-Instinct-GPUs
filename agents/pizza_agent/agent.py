"""
Pizza Seller Agent

Built with LangGraph using the ReAct pattern (Reason → Act → Observe).
Serves as an A2A-compatible remote agent for the Purchasing Concierge.

The agent maintains cross-turn conversation memory via LangGraph's MemorySaver,
allowing it to recall what the user ordered earlier in the same session.

Responsibilities:
- Answer questions about the pizza menu and pricing
- Confirm orders with the user before creation
- Call create_pizza_order tool for deterministic order creation
- Return structured ResponseFormat output consumed by the A2A server
"""

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from agents.pizza_agent.config import MENU_TEXT, OLLAMA_MODEL
from agents.pizza_agent.tools import ResponseFormat, create_pizza_order

# ── Memory ────────────────────────────────────────────────────────────────────
# JsonPlusSerializer allows ResponseFormat Pydantic objects to be serialised
# across checkpoints so structured state survives multi-turn conversations.
_memory = MemorySaver(
    serde=JsonPlusSerializer(
        allowed_msgpack_modules=[("agents.pizza_agent.tools", "ResponseFormat")]
    )
)

_SYSTEM_INSTRUCTION = f"""
# INSTRUCTIONS

You are a specialized assistant for a pizza store.
Your sole purpose is to answer questions about the pizza menu, pricing, and
to handle order creation.

If the user asks about anything unrelated to pizza, politely decline and
redirect them to pizza-related topics.

# MENU

{MENU_TEXT}

# RULES

When the user wants to place an order:
1. Always confirm the order and total price with the user first.
   (The user may have already confirmed in their message — check carefully.)
2. Call the `create_pizza_order` tool to create the order.
3. Return a response with the itemised order, price breakdown, total, and order ID.

Status values:
- input_required — awaiting user confirmation
- error — something went wrong
- completed — order successfully placed

Never invent menu items or prices. Only use what is listed above.
"""


class PizzaSellerAgent:
    """
    LangGraph-based pizza ordering agent exposed via the A2A protocol.

    Uses a ReAct graph with persistent MemorySaver checkpointing.
    The underlying LLM is Ollama-hosted Llama 3.1.
    """

    SUPPORTED_CONTENT_TYPES: list[str] = ["text", "text/plain"]

    def __init__(self) -> None:
        model = ChatOllama(model=OLLAMA_MODEL)
        self.graph = create_agent(
            model,
            tools=[create_pizza_order],
            checkpointer=_memory,
            system_prompt=_SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )

    def invoke(self, query: str, session_id: str) -> dict:
        """
        Process a user query and return a structured response dict.

        Args:
            query: The user's natural-language request.
            session_id: Thread ID used by LangGraph MemorySaver for state continuity.

        Returns:
            dict with keys: is_task_complete, require_user_input, content
        """
        config = {"configurable": {"thread_id": session_id}}
        self.graph.invoke({"messages": [("user", query)]}, config)
        return self._build_response(config)

    def _build_response(self, config: dict) -> dict:
        """Extract structured response from LangGraph state and map to A2A envelope."""
        current_state = self.graph.get_state(config)
        structured = current_state.values.get("structured_response")

        if structured and isinstance(structured, ResponseFormat):
            if structured.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured.message,
                }
            if structured.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured.message,
                }
            if structured.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to process your request at the moment. Please try again.",
        }
