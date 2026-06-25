#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start vLLM with tool-calling enabled (Burger Agent backend)
#
# Usage:
#   ./scripts/start_vllm.sh
#
# Prerequisites:
#   - HF_TOKEN exported in your shell
#   - vLLM installed with ROCm support
#   - vllm/ repository cloned (for the Jinja chat template)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

: "${HF_TOKEN:?HF_TOKEN must be set. Run: export HF_TOKEN=<your_token>}"

MODEL="${VLLM_MODEL_ID:-meta-llama/Llama-3.1-8B-Instruct}"
PORT="${VLLM_PORT:-8088}"
GPU_MEM="${VLLM_GPU_MEM:-0.6}"
TEMPLATE="vllm/examples/tool_chat_template_llama3.1_json.jinja"

if [ ! -f "$TEMPLATE" ]; then
  echo "[start_vllm] Cloning vLLM for chat template..."
  git clone --depth 1 https://github.com/vllm-project/vllm.git
fi

echo "[start_vllm] Starting vLLM on port $PORT with model $MODEL"
echo "[start_vllm] GPU memory utilisation: $GPU_MEM"

vllm serve "$MODEL" \
  --enable-auto-tool-choice \
  --tool-call-parser llama3_json \
  --port "$PORT" \
  --chat-template "$TEMPLATE" \
  --gpu-memory-utilization "$GPU_MEM"
