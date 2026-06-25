"""
Pizza Seller Agent — A2A Server Entrypoint

Run with:
    python -m agents.pizza_agent.server
"""

import logging
import sys
import threading
import time

from utils.a2a_types import AgentAuthentication, AgentCapabilities, AgentCard, AgentSkill
from utils.push_notification_auth import PushNotificationSenderAuth
from utils.server import A2AServer
from utils.task_manager import AgentTaskManager

from agents.pizza_agent.agent import PizzaSellerAgent
from agents.pizza_agent.config import API_KEY, SERVER_HOST, SERVER_PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pizza_agent.server")


def build_server(host: str, port: int) -> A2AServer:
    """Construct and configure the A2A server for the Pizza Seller Agent."""
    capabilities = AgentCapabilities(pushNotifications=True)

    skill = AgentSkill(
        id="create_pizza_order",
        name="Pizza Order Creation Tool",
        description="Presents the pizza menu, provides pricing, and handles order creation.",
        tags=["pizza", "order", "food"],
        examples=[
            "What pizzas do you have?",
            "I want to order 2 Pepperoni Pizzas",
            "How much is the BBQ Chicken Pizza?",
        ],
    )

    agent_card = AgentCard(
        name="pizza_seller_agent",
        description="Pizza store agent — answers menu questions and creates orders.",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        authentication=AgentAuthentication(schemes=["Bearer"]),
        defaultInputModes=PizzaSellerAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=PizzaSellerAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

    notification_auth = PushNotificationSenderAuth()
    notification_auth.generate_jwk()

    server = A2AServer(
        agent_card=agent_card,
        task_manager=AgentTaskManager(
            agent=PizzaSellerAgent(),
            notification_sender_auth=notification_auth,
        ),
        host=host,
        port=port,
        api_key=API_KEY,
    )

    server.app.add_route(
        "/.well-known/jwks.json",
        notification_auth.handle_jwks_endpoint,
        methods=["GET"],
    )

    return server


def main() -> None:
    logger.info("Starting Pizza Seller Agent on %s:%d", SERVER_HOST, SERVER_PORT)
    try:
        server = build_server(SERVER_HOST, SERVER_PORT)
        server.start()
    except Exception:
        logger.exception("Fatal error during server startup")
        sys.exit(1)


def start_in_thread() -> threading.Thread:
    """Start server in a background daemon thread (useful for Jupyter)."""
    thread = threading.Thread(target=main, daemon=True)
    thread.start()
    time.sleep(3)
    logger.info("Pizza Agent server thread started on port %d", SERVER_PORT)
    return thread


if __name__ == "__main__":
    main()
