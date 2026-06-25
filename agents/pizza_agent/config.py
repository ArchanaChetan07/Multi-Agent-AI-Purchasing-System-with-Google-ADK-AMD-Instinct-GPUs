"""
Pizza Seller Agent — Configuration
"""

import os

# ── LLM backend ──────────────────────────────────────────────────────────────
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Server ────────────────────────────────────────────────────────────────────
SERVER_HOST: str = os.environ.get("PIZZA_SERVER_HOST", "0.0.0.0")
SERVER_PORT: int = int(os.environ.get("PIZZA_SERVER_PORT", "10000"))

# ── Authentication ────────────────────────────────────────────────────────────
API_KEY: str = os.environ.get("API_KEY", "pizza123")

# ── Menu ──────────────────────────────────────────────────────────────────────
PIZZA_MENU = {
    "Margherita Pizza": 100,
    "Pepperoni Pizza": 140,
    "Hawaiian Pizza": 110,
    "Veggie Pizza": 100,
    "BBQ Chicken Pizza": 130,
}

MENU_TEXT = "\n".join(
    f"- {name}: IDR {price}K" for name, price in PIZZA_MENU.items()
)
