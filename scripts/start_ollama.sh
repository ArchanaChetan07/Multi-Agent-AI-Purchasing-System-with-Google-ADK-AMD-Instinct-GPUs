#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start Ollama server and pull the Llama 3.1 model
#
# Usage:
#   ./scripts/start_ollama.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

MODEL="${OLLAMA_MODEL_ID:-llama3.1}"

echo "[start_ollama] Starting Ollama server..."
nohup ollama serve > /tmp/ollama.log 2>&1 &

echo "[start_ollama] Waiting for Ollama to initialise..."
sleep 5

echo "[start_ollama] Pulling model: $MODEL"
ollama pull "$MODEL"

echo "[start_ollama] Ollama ready. Model $MODEL available."
echo "[start_ollama] Logs: tail -f /tmp/ollama.log"
