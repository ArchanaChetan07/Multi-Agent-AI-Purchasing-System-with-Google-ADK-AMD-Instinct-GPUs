#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start the full multi-agent system
#
# Usage:
#   ./scripts/start_all.sh [HF_TOKEN]
#
# Starts (in order):
#   1. Ollama server + model pull
#   2. vLLM server
#   3. Burger Seller Agent (port 10001)
#   4. Pizza Seller Agent  (port 10000)
#   5. Purchasing Concierge + Gradio UI (port 8087)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

if [ -n "${1:-}" ]; then
  export HF_TOKEN="$1"
fi

: "${HF_TOKEN:?HF_TOKEN is required. Pass it as argument: ./scripts/start_all.sh <token>}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Load .env if present
if [ -f .env ]; then
  echo "[start_all] Loading .env"
  set -o allexport
  source .env
  set +o allexport
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Multi-Agent AI Purchasing System — Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Ollama
echo ""
echo "▶ [1/5] Starting Ollama..."
./scripts/start_ollama.sh &
sleep 8

# 2. vLLM
echo ""
echo "▶ [2/5] Starting vLLM..."
./scripts/start_vllm.sh &
sleep 15  # vLLM takes longer to load the model

# 3. Burger Agent
echo ""
echo "▶ [3/5] Starting Burger Seller Agent (port 10001)..."
python -m agents.burger_agent.server &
BURGER_PID=$!
sleep 3

# 4. Pizza Agent
echo ""
echo "▶ [4/5] Starting Pizza Seller Agent (port 10000)..."
python -m agents.pizza_agent.server &
PIZZA_PID=$!
sleep 3

# 5. Purchasing Concierge + UI
echo ""
echo "▶ [5/5] Starting Purchasing Concierge + Gradio UI (port 8087)..."
python -m agents.purchasing_agent.app &
CONCIERGE_PID=$!

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ All agents started"
echo "  🌐 Open: http://localhost:8087"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Keep script alive; Ctrl-C kills everything
trap "echo 'Shutting down...'; kill $BURGER_PID $PIZZA_PID $CONCIERGE_PID 2>/dev/null" INT TERM
wait
