"""
Purchasing Concierge — Gradio Application

Launches the root agent with an interactive Gradio chat interface.
Streams tool calls, tool responses, and final agent outputs to the UI.

Run with:
    python -m agents.purchasing_agent.app

Then open: http://localhost:8087
"""

import logging
import os
from pprint import pformat
from typing import Any, AsyncIterator

import gradio as gr
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.purchasing_agent.agent import PurchasingAgent

# Suppress noisy OpenTelemetry context logs
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("purchasing_agent.app")

# ── Agent setup ───────────────────────────────────────────────────────────────
_root_agent = PurchasingAgent(
    remote_agent_addresses=[
        os.getenv("PIZZA_SELLER_AGENT_URL", "http://localhost:10000"),
        os.getenv("BURGER_SELLER_AGENT_URL", "http://localhost:10001"),
    ]
).create_agent()

# ── ADK Runner ────────────────────────────────────────────────────────────────
APP_NAME = "purchasing_concierge"
USER_ID = "default_user"
SESSION_ID = "default_session"

_session_service = InMemorySessionService()
_runner = Runner(
    agent=_root_agent,
    app_name=APP_NAME,
    session_service=_session_service,
)


async def _init_session() -> None:
    """Create the default session (idempotent)."""
    await _session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )


# ── Gradio handler ────────────────────────────────────────────────────────────
async def get_response_from_agent(
    message: str,
    history: list[dict[str, Any]],
):
    """
    Send a user message to the ADK runner and stream back chat messages.

    Intermediate tool calls and responses are surfaced as labelled assistant
    messages so the user can observe the full multi-agent coordination trace.
    """
    events_iterator: AsyncIterator[Event] = _runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(
            role="user", parts=[types.Part(text=message)]
        ),
    )

    responses: list[gr.ChatMessage] = []

    async for event in events_iterator:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    formatted = (
                        f"```python\n"
                        f"{pformat(part.function_call.model_dump(), indent=2, width=80)}\n"
                        f"```"
                    )
                    responses.append(
                        gr.ChatMessage(
                            role="assistant",
                            content=f"{part.function_call.name}:\n{formatted}",
                            metadata={"title": "🛠️ Tool Call"},
                        )
                    )
                elif part.function_response:
                    formatted = (
                        f"```python\n"
                        f"{pformat(part.function_response.model_dump(), indent=2, width=80)}\n"
                        f"```"
                    )
                    responses.append(
                        gr.ChatMessage(
                            role="assistant",
                            content=formatted,
                            metadata={"title": "⚡ Tool Response"},
                        )
                    )

        if event.is_final_response():
            final_text = ""
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""
            elif event.actions and event.actions.escalate:
                final_text = (
                    f"Agent escalated: {event.error_message or 'No specific message.'}"
                )
            responses.append(gr.ChatMessage(role="assistant", content=final_text))
            yield responses
            break

        yield responses


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> None:
    await _init_session()
    logger.info("Session initialised. Launching Gradio UI...")

    demo = gr.ChatInterface(
        fn=get_response_from_agent,
        title="🛒 Purchasing Concierge",
        description=(
            "Ask about burgers, pizzas, or place an order. "
            "The concierge will route your request to the right seller agent."
        ),
        examples=[
            "What's on the menu?",
            "Show me the burger options",
            "I'd like 2 Pepperoni Pizzas please",
            "Order 1 Classic Cheeseburger and 1 Hawaiian Pizza",
        ],
        type="messages",
    )

    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("UI_PORT", "8087")),
        share=False,
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
