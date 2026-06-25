"""
Tests for PizzaSellerAgent

Mocks LangGraph graph invocation so no live Ollama server is required during CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.pizza_agent.agent import PizzaSellerAgent
from agents.pizza_agent.tools import OrderItem, ResponseFormat, create_pizza_order


# ── Tool tests ────────────────────────────────────────────────────────────────


def test_create_pizza_order_returns_order_string():
    items = [OrderItem(name="Pepperoni Pizza", quantity=2, price=140)]
    result = create_pizza_order.invoke({"order_items": items})
    assert "order_id" in result
    assert "Pepperoni Pizza" in result


def test_create_pizza_order_multiple_items():
    items = [
        OrderItem(name="Margherita Pizza", quantity=1, price=100),
        OrderItem(name="BBQ Chicken Pizza", quantity=1, price=130),
    ]
    result = create_pizza_order.invoke({"order_items": items})
    assert "order_id" in result


# ── Agent response mapping tests ──────────────────────────────────────────────


def _make_graph_state(status: str, message: str):
    """Helper: build a mock LangGraph get_state response."""
    state = MagicMock()
    state.values = {"structured_response": ResponseFormat(status=status, message=message)}
    return state


@patch("agents.pizza_agent.agent.create_agent")
@patch("agents.pizza_agent.agent.ChatOllama")
def test_pizza_agent_maps_input_required(mock_ollama, mock_create_agent):
    mock_graph = MagicMock()
    mock_create_agent.return_value = mock_graph
    mock_graph.get_state.return_value = _make_graph_state(
        "input_required", "Please confirm your pizza order."
    )

    agent = PizzaSellerAgent()
    config = {"configurable": {"thread_id": "test-session"}}
    response = agent._build_response(config)

    assert response["is_task_complete"] is False
    assert response["require_user_input"] is True


@patch("agents.pizza_agent.agent.create_agent")
@patch("agents.pizza_agent.agent.ChatOllama")
def test_pizza_agent_maps_completed(mock_ollama, mock_create_agent):
    mock_graph = MagicMock()
    mock_create_agent.return_value = mock_graph
    mock_graph.get_state.return_value = _make_graph_state(
        "completed", "Order placed! Order ID: xyz"
    )

    agent = PizzaSellerAgent()
    config = {"configurable": {"thread_id": "test-session"}}
    response = agent._build_response(config)

    assert response["is_task_complete"] is True
    assert response["require_user_input"] is False


@patch("agents.pizza_agent.agent.create_agent")
@patch("agents.pizza_agent.agent.ChatOllama")
def test_pizza_agent_fallback_on_missing_structured_response(mock_ollama, mock_create_agent):
    mock_graph = MagicMock()
    mock_create_agent.return_value = mock_graph
    mock_graph.get_state.return_value = MagicMock(values={})

    agent = PizzaSellerAgent()
    config = {"configurable": {"thread_id": "test-session"}}
    response = agent._build_response(config)

    assert "Unable to process" in response["content"]
