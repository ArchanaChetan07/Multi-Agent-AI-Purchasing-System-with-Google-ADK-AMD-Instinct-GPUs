"""
Burger Seller Agent — A2A Server Entrypoint

Wraps the BurgerSellerAgent in an A2AServer so it is discoverable and callable
by the Purchasing Concierge (root agent) via the A2A protocol.

Run with:
    python -m agents.burger_agent.server

The server publishes an Agent Card at /.well-known/agent.json
and a JWKS endpoint at /.well-known/jwks.json.
"""

import logging
import sys
import threading
import time

from utils.a2a_types import AgentAuthentication, AgentCapabilities, AgentCard, AgentSkill
from utils.push_notification_auth import PushNotificationSenderAuth
from utils.server import A2AServer
from utils.task_manager import AgentTaskManager

from agents.burger_agent.agent import BurgerSellerAgent
from agents.burger_agent.config import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    SERVER_HOST,
    SERVER_PORT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("burger_agent.server")


def build_server(host: str, port: int) -> A2AServer:
    """Construct and configure the A2A server for the Burger Seller Agent."""
    capabilities = AgentCapabilities(pushNotifications=True)

    skill = AgentSkill(
        id="create_burger_order",
        name="Burger Order Creation Tool",
        description="Presents the burger menu, provides pricing, and handles order creation.",
        tags=["burger", "order", "food"],
        examples=[
            "What burgers do you have?",
            "I want to order 2 classic cheeseburgers",
            "How much is the Spicy Cajun Burger?",
        ],
    )

    agent_card = AgentCard(
        name="burger_seller_agent",
        description="Burger store agent — answers menu questions and creates orders.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        authentication=AgentAuthentication(schemes=["Basic"]),
        defaultInputModes=BurgerSellerAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=BurgerSellerAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    notification_auth = PushNotificationSenderAuth()
    notification_auth.generate_jwk()

    server = A2AServer(
        agent_card=agent_card,
        task_manager=AgentTaskManager(
            agent=BurgerSellerAgent(),
            notification_sender_auth=notification_auth,
        ),
        host=host,
        port=port,
        auth_username=AUTH_USERNAME,
        auth_password=AUTH_PASSWORD,
    )

    server.app.add_route(
        "/.well-known/jwks.json",
        notification_auth.handle_jwks_endpoint,
        methods=["GET"],
    )

    return server


def main() -> None:
    """Start the Burger Seller Agent A2A server (blocking)."""
    logger.info("Starting Burger Seller Agent on %s:%d", SERVER_HOST, SERVER_PORT)
    try:
        server = build_server(SERVER_HOST, SERVER_PORT)
        server.start()
    except Exception:
        logger.exception("Fatal error during server startup")
        sys.exit(1)


def start_in_thread() -> threading.Thread:
    """
    Start the server in a background daemon thread.
    Useful when running inside a Jupyter notebook alongside other agents.
    """
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    time.sleep(3)  # Allow server to initialise
    logger.info("Burger Agent server thread started on port %d", SERVER_PORT)
    return thread


if __name__ == "__main__":
    main()
