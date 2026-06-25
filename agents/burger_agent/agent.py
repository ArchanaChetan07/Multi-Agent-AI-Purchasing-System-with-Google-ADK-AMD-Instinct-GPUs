"""
Burger Seller Agent

Built with CrewAI following the Agent → Task → Crew → Output pipeline.
Serves as an A2A-compatible remote agent for the Purchasing Concierge.

Responsibilities:
- Answer questions about the burger menu and pricing
- Confirm orders with the user before creation
- Call create_burger_order tool for deterministic order creation
- Return structured ResponseFormat output consumed by the A2A server
"""

from crewai import Agent as CrewAgent
from crewai import Crew, LLM, Process, Task

from agents.burger_agent.config import MENU_TEXT, OPENAI_API_BASE, VLLM_MODEL
from agents.burger_agent.tools import ResponseFormat, create_burger_order


_TASK_INSTRUCTION = f"""
# INSTRUCTIONS

You are a specialized assistant for a burger store.
Your sole purpose is to answer questions about what is available on the burger
menu and price, and to handle order creation.

If the user asks about anything unrelated to the burger menu or orders, politely
decline and redirect them to burger-related topics.

# CONTEXT

Received user query: {{user_prompt}}
Session ID: {{session_id}}

Available burger menu and prices:
{MENU_TEXT}

# RULES

When the user wants to place an order:
1. Always confirm the order and total price with the user first.
   (The user may have already confirmed in their message — check carefully.)
2. Call the `create_burger_order` tool to create the order.
3. Return a response with the itemised order, price breakdown, total, and order ID.

Status values:
- input_required — awaiting user confirmation
- error — something went wrong
- completed — order successfully placed

Never invent menu items or prices. Only use what is listed above.
"""


class BurgerSellerAgent:
    """
    CrewAI-based burger ordering agent exposed via the A2A protocol.

    Uses a sequential Crew with a single task. The LLM is served via vLLM
    with tool-calling enabled.
    """

    SUPPORTED_CONTENT_TYPES: list[str] = ["text", "text/plain"]

    def invoke(self, query: str, session_id: str) -> dict:
        """
        Process a user query and return a structured response dict.

        Args:
            query: The user's natural-language request.
            session_id: Unique identifier for the current A2A session.

        Returns:
            dict with keys: is_task_complete, require_user_input, content
        """
        agent = CrewAgent(
            role="Burger Seller Agent",
            goal="Help users understand the burger menu and handle order creation.",
            backstory="You are an expert, friendly burger seller agent.",
            verbose=False,
            allow_delegation=False,
            tools=[create_burger_order],
            llm=LLM(model=VLLM_MODEL, api_base=OPENAI_API_BASE),
        )

        task = Task(
            description=_TASK_INSTRUCTION,
            output_pydantic=ResponseFormat,
            agent=agent,
            expected_output=(
                "A JSON object with 'status' and 'message' fields. "
                "status is one of: input_required, error, completed."
            ),
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False,
            process=Process.sequential,
        )

        result = crew.kickoff(inputs={"user_prompt": query, "session_id": session_id})
        return self._build_response(result)

    def _build_response(self, crew_result) -> dict:
        """Map CrewAI Pydantic output to the A2A response envelope."""
        response_obj = crew_result.pydantic

        if response_obj and isinstance(response_obj, ResponseFormat):
            if response_obj.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": response_obj.message,
                }
            if response_obj.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": response_obj.message,
                }
            if response_obj.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": response_obj.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "Unable to process your request at the moment. Please try again.",
        }
