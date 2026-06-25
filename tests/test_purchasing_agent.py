"""
Tests for PurchasingAgent

Verifies agent registration, routing logic, and task dispatch without
requiring live remote agents.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.purchasing_agent.agent import PurchasingAgent, _extract_text_parts
from utils.a2a_types import Part


# ── Helper tests ──────────────────────────────────────────────────────────────


def test_extract_text_parts_filters_non_text():
    parts = [
        MagicMock(type="text", text="Hello"),
        MagicMock(type="image"),
        MagicMock(type="text", text="World"),
    ]
    result = _extract_text_parts(parts)
    assert result == ["Hello", "World"]


def test_extract_text_parts_empty():
    assert _extract_text_parts([]) == []


# ── Agent registration tests ──────────────────────────────────────────────────


@patch("agents.purchasing_agent.agent.A2ACardResolver")
def test_agent_skips_unreachable_address(mock_resolver_class):
    import httpx
    mock_resolver = MagicMock()
    mock_resolver.get_agent_card.side_effect = httpx.ConnectError("refused")
    mock_resolver_class.return_value = mock_resolver

    agent = PurchasingAgent(remote_agent_addresses=["http://localhost:9999"])

    assert len(agent.remote_agent_connections) == 0
    assert len(agent.cards) == 0


@patch("agents.purchasing_agent.agent.A2ACardResolver")
def test_agent_registers_reachable_address(mock_resolver_class):
    mock_card = MagicMock()
    mock_card.name = "burger_seller_agent"
    mock_card.description = "Burger agent"

    mock_resolver = MagicMock()
    mock_resolver.get_agent_card.return_value = mock_card
    mock_resolver_class.return_value = mock_resolver

    with patch("agents.purchasing_agent.agent.RemoteAgentConnections"):
        agent = PurchasingAgent(
            remote_agent_addresses=["http://localhost:10001"]
        )

    assert "burger_seller_agent" in agent.cards


@patch("agents.purchasing_agent.agent.A2ACardResolver")
def test_list_remote_agents_returns_name_description(mock_resolver_class):
    mock_card = MagicMock()
    mock_card.name = "pizza_seller_agent"
    mock_card.description = "Pizza agent"

    mock_resolver = MagicMock()
    mock_resolver.get_agent_card.return_value = mock_card
    mock_resolver_class.return_value = mock_resolver

    with patch("agents.purchasing_agent.agent.RemoteAgentConnections"):
        agent = PurchasingAgent(remote_agent_addresses=["http://localhost:10000"])

    agents = agent.list_remote_agents()
    assert len(agents) == 1
    assert agents[0]["name"] == "pizza_seller_agent"
    assert agents[0]["description"] == "Pizza agent"
