"""
Burger Seller Agent — Tools

Defines the create_burger_order tool used by the BurgerSellerAgent.
LLMs determine intent; this tool handles deterministic, auditable order creation.
"""

import uuid
from typing import Literal

from crewai.tools import tool
from pydantic import BaseModel


class ResponseFormat(BaseModel):
    """Structured response format returned by the BurgerSellerAgent."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class OrderItem(BaseModel):
    """A single line item in an order."""

    name: str
    quantity: int
    price: int  # Price in IDR (thousands)


class Order(BaseModel):
    """A completed order with a unique ID."""

    order_id: str
    status: str
    order_items: list[OrderItem]


@tool("create_order")
def create_burger_order(order_items: list[OrderItem]) -> str:
    """
    Creates a new burger order with the given order items.

    Args:
        order_items: List of order items to be added to the order.

    Returns:
        str: Confirmation message with the created order details.
    """
    try:
        order_id = str(uuid.uuid4())
        order = Order(order_id=order_id, status="created", order_items=order_items)
        print("=" * 40)
        print(f"[BurgerAgent] Order created: {order}")
        print("=" * 40)
    except Exception as e:
        print(f"[BurgerAgent] Error creating order: {e}")
        return f"Error creating order: {e}"

    return f"Order {order.model_dump()} has been created"
