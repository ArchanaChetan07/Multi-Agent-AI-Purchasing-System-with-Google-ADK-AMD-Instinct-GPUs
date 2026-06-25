"""
Tests for BurgerSellerAgent

These are integration-style unit tests that mock the CrewAI LLM call
so no live vLLM server is required during CI.
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.burger_agent.agent import BurgerSellerAgent
from agents.burger_agent.tools import OrderItem, ResponseFormat, create_burger_order


# ── Tool tests ────────────────────────────────────────────────────────────────


def test_create_burger_order_returns_order_string():
    items = [OrderItem(name="Classic Cheeseburger", quantity=1, price=85)]
    result = create_burger_order.invoke({"order_items": items})
    assert "order_id" in result
    assert "Classic Cheeseburger" in result


def test_create_burger_order_multiple_items():
    items = [
        OrderItem(name="Classic Cheeseburger", quantity=2, price=85),
        OrderItem(name="Spicy Cajun Burger", quantity=1, price=85),
    ]
    result = create_burger_order.invoke({"order_items": items})
    assert "order_id" in result
    assert "status" in result


# ── Agent response mapping tests ──────────────────────────────────────────────


def _make_crew_result(status: str, message: str):
    """Helper: build a mock CrewAI kickoff result."""
    result = MagicMock()
    result.pydantic = ResponseFormat(status=status, message=message)
    return result


def test_agent_maps_input_required():
    agent = BurgerSellerAgent()
    crew_result = _make_crew_result("input_required", "Please confirm your order.")
    response = agent._build_response(crew_result)
    assert response["is_task_complete"] is False
    assert response["require_user_input"] is True
    assert "confirm" in response["content"]


def test_agent_maps_completed():
    agent = BurgerSellerAgent()
    crew_result = _make_crew_result("completed", "Your order #abc has been placed.")
    response = agent._build_response(crew_result)
    assert response["is_task_complete"] is True
    assert response["require_user_input"] is False


def test_agent_maps_error():
    agent = BurgerSellerAgent()
    crew_result = _make_crew_result("error", "Something went wrong.")
    response = agent._build_response(crew_result)
    assert response["is_task_complete"] is False
    assert response["require_user_input"] is True


def test_agent_fallback_on_none_pydantic():
    agent = BurgerSellerAgent()
    crew_result = MagicMock()
    crew_result.pydantic = None
    response = agent._build_response(crew_result)
    assert response["is_task_complete"] is False
    assert "Unable to process" in response["content"]
