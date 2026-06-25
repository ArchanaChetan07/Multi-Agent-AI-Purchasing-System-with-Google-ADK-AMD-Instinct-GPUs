"""
Pizza Seller Agent — Tools

Defines the create_pizza_order tool used by the PizzaSellerAgent.
"""

import uuid
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel


class ResponseFormat(BaseModel):
    """Structured response format returned by the PizzaSellerAgent."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class OrderItem(BaseModel):
    """A single line item in a pizza order."""

    name: str
    quantity: int
    price: int  # Price in IDR (thousands)


class Order(BaseModel):
    """A completed pizza order with a unique ID."""

    order_id: str
    status: str
    order_items: list[OrderItem]


@tool
def create_pizza_order(order_items: list[OrderItem]) -> str:
    """
    Creates a new pizza order with the given order items.

    Args:
        order_items: List of order items to be added to the order.

    Returns:
        str: Confirmation message with the created order details.
    """
    try:
        order_id = str(uuid.uuid4())
        order = Order(order_id=order_id, status="created", order_items=order_items)
        print("=" * 40)
        print(f"[PizzaAgent] Order created: {order}")
        print("=" * 40)
    except Exception as e:
        print(f"[PizzaAgent] Error creating order: {e}")
        return f"Error creating order: {e}"

    return f"Order {order.model_dump()} has been created"
