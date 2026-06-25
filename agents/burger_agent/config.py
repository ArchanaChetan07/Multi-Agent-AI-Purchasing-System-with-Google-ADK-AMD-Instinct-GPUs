"""
Burger Seller Agent — Configuration

Centralises all environment-variable access and static menu data.
"""

import os

# ── LLM backend ──────────────────────────────────────────────────────────────
VLLM_MODEL: str = os.environ.get(
    "VLLM_MODEL", "hosted_vllm/meta-llama/Llama-3.1-8B-Instruct"
)
OPENAI_API_BASE: str = os.environ.get("OPENAI_API_BASE", "http://localhost:8088/v1")

# ── Server ────────────────────────────────────────────────────────────────────
SERVER_HOST: str = os.environ.get("BURGER_SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.environ.get("BURGER_SERVER_PORT", "10001"))

# ── Authentication ────────────────────────────────────────────────────────────
AUTH_USERNAME: str = os.environ.get("BURGER_AUTH_USERNAME", "burgeruser123")
AUTH_PASSWORD: str = os.environ.get("BURGER_AUTH_PASSWORD", "burgerpass123")

# ── Menu ──────────────────────────────────────────────────────────────────────
BURGER_MENU = {
    "Classic Cheeseburger": 85,
    "Double Cheeseburger": 110,
    "Spicy Chicken Burger": 80,
    "Spicy Cajun Burger": 85,
}

MENU_TEXT = "\n".join(
    f"- {name}: IDR {price}K" for name, price in BURGER_MENU.items()
)
