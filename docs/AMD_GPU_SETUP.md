# AMD GPU Setup Guide

## Supported hardware

This project is developed and tested on **AMD Instinct™** accelerators:

| GPU | VRAM | Notes |
|-----|------|-------|
| MI250X | 2× 64 GB HBM2e | Recommended for dual-model deployment |
| MI300X | 192 GB HBM3 | Excellent headroom for larger models |
| MI210 | 64 GB HBM2e | Supported |
| RX 7900 XTX | 24 GB GDDR6 | Consumer GPU, reduced headroom |

---

## ROCm installation

### Check existing ROCm version

```bash
rocminfo | grep "ROCm Version"
```

### Install ROCm 6.x (Ubuntu 22.04 / 24.04)

```bash
# Add AMD apt repository
wget https://repo.radeon.com/amdgpu-install/6.1/ubuntu/jammy/amdgpu-install_6.1.60101-1_all.deb
sudo dpkg -i amdgpu-install_6.1.60101-1_all.deb
sudo apt update

# Install ROCm
sudo amdgpu-install --usecase=rocm
sudo usermod -aG render,video $USER
# Log out and back in for group membership to take effect
```

### Verify GPU visibility

```bash
rocminfo
# Should list your GPU(s) as agents
```

---

## vLLM with ROCm

### Install vLLM (ROCm build)

```bash
pip install vllm --extra-index-url https://download.pytorch.org/whl/rocm6.1
```

### Verify GPU is detected by vLLM

```python
import torch
print(torch.cuda.is_available())   # Should be True (ROCm maps to CUDA API)
print(torch.cuda.get_device_name(0))
```

### GPU memory management

The system runs two LLM backends simultaneously:

| Backend | Model | Memory |
|---------|-------|--------|
| vLLM | Llama 3.1 8B (FP16) | ~60% GPU VRAM |
| Ollama | Llama 3.1 8B (Q4_K_M) | ~8 GB |

The `--gpu-memory-utilization 0.6` flag in `scripts/start_vllm.sh` reserves 40% for Ollama and system overhead.

**If you have a single GPU with less than 24 GB VRAM**, reduce the vLLM utilisation:

```bash
# In scripts/start_vllm.sh, change:
VLLM_GPU_MEM=0.45  # or lower
```

---

## Ollama on AMD GPU

Ollama automatically detects ROCm. No special configuration needed.

```bash
ollama serve
# Logs will show: "ROCm device detected"
```

To verify which device Ollama is using:

```bash
ollama ps
# Shows running models and device (e.g. GPU, 100%)
```

---

## Troubleshooting

### Out-of-Memory errors

1. Reduce vLLM GPU memory utilisation (`VLLM_GPU_MEM=0.45`)
2. Use a smaller/more quantized model (e.g. `Llama-3.1-8B-Instruct` in GGUF Q4)
3. Enable vLLM's CPU offload: add `--cpu-offload-gb 4` to the serve command

### vLLM tool-calling not working

Ensure you are using the correct Jinja template for your model. Llama 3.1 requires:

```
vllm/examples/tool_chat_template_llama3.1_json.jinja
```

The `--tool-call-parser llama3_json` flag must also be set.

### Ollama not found

```bash
which ollama       # Check binary is on PATH
ollama list        # List downloaded models
ollama pull llama3.1  # Pull if missing
```
