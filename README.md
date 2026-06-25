# 🤖 Multi-Agent AI Purchasing System

### Google ADK · CrewAI · LangGraph · AMD Instinct GPUs · A2A Protocol

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google_ADK-latest-4285F4?style=flat-square&logo=google)](https://google.github.io/adk-docs/)
[![CrewAI](https://img.shields.io/badge/CrewAI-latest-orange?style=flat-square)](https://crewai.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-green?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![vLLM](https://img.shields.io/badge/vLLM-latest-purple?style=flat-square)](https://vllm.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

A production-grade **Agent-to-Agent (A2A)** system demonstrating cross-framework AI agent interoperability. Three specialized agents — built on different frameworks — collaborate through Google's open A2A protocol to handle natural-language food ordering, all running locally on **AMD Instinct™ GPUs** with zero cloud API dependency.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User (Gradio Chat UI :8087)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Purchasing Concierge Agent (Root)                   │
│              Google ADK + LiteLLM + Ollama                      │
│              Orchestrates · Routes · Delegates                   │
└──────────────────┬──────────────────────────┬───────────────────┘
                   │   A2A Protocol (HTTP)     │   A2A Protocol (HTTP)
        ┌──────────▼──────────┐    ┌──────────▼──────────┐
        │   Burger Seller     │    │    Pizza Seller      │
        │   CrewAI + vLLM     │    │  LangGraph + Ollama  │
        │   Port :10001       │    │    Port :10000       │
        │   Auth: Basic       │    │    Auth: Bearer      │
        └─────────────────────┘    └──────────────────────┘
```

### Agent Breakdown

| Agent | Framework | LLM Backend | Port | Auth |
|-------|-----------|-------------|------|------|
| **Purchasing Concierge** | Google ADK | Ollama (Llama 3.1) | — | — |
| **Burger Seller** | CrewAI | vLLM (Llama 3.1 8B) | 10001 | Basic Auth |
| **Pizza Seller** | LangGraph | Ollama (Llama 3.1) | 10000 | Bearer Token |

---

## Key Features

- **Cross-framework interoperability** — ADK, CrewAI, and LangGraph agents communicate through a single open protocol without sharing code or vendor dependencies
- **100% local inference** — Dual LLM backends (vLLM + Ollama) on AMD GPUs; no OpenAI or cloud API required
- **Enterprise authentication** — Per-agent auth schemes (Basic Auth, Bearer tokens) with JWKS endpoints and push notification support
- **Deterministic tool execution** — LLMs decide intent; Pydantic-validated tools (`create_burger_order`, `create_pizza_order`) handle side effects
- **Structured response lifecycle** — Three-state machine (`input_required → completed / error`) enforced via Pydantic across all agents
- **Session & state management** — ADK's `InMemorySessionService` tracks conversation context; LangGraph's `MemorySaver` provides cross-turn memory
- **Real-time observability** — Gradio UI surfaces tool calls, tool responses, and final agent outputs in streaming fashion

---

## Project Structure

```
adk-multi-agent-system/
├── agents/
│   ├── burger_agent/
│   │   ├── __init__.py
│   │   ├── agent.py          # BurgerSellerAgent (CrewAI)
│   │   ├── tools.py          # create_burger_order tool
│   │   ├── server.py         # A2A server entrypoint
│   │   └── config.py         # Environment + menu config
│   ├── pizza_agent/
│   │   ├── __init__.py
│   │   ├── agent.py          # PizzaSellerAgent (LangGraph)
│   │   ├── tools.py          # create_pizza_order tool
│   │   ├── server.py         # A2A server entrypoint
│   │   └── config.py         # Environment + menu config
│   └── purchasing_agent/
│       ├── __init__.py
│       ├── agent.py          # PurchasingAgent (Google ADK)
│       ├── connections.py    # RemoteAgentConnections
│       └── app.py            # Gradio UI + ADK Runner
├── utils/                    # A2A protocol utilities
│   ├── a2a_types.py          # Shared type definitions
│   ├── client.py             # A2AClient
│   ├── server.py             # A2AServer base
│   ├── task_manager.py       # AgentTaskManager
│   ├── card_resolver.py      # Agent Card discovery
│   └── push_notification_auth.py
├── scripts/
│   ├── start_vllm.sh         # Launch vLLM with tool-calling
│   ├── start_ollama.sh       # Launch Ollama + pull model
│   └── start_all.sh          # Start full system
├── tests/
│   ├── test_burger_agent.py
│   ├── test_pizza_agent.py
│   └── test_purchasing_agent.py
├── docs/
│   ├── A2A_PROTOCOL.md       # A2A protocol deep dive
│   ├── AMD_GPU_SETUP.md      # AMD GPU configuration guide
│   └── ARCHITECTURE.md       # System design decisions
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI pipeline
├── .env.example
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Prerequisites

- **AMD Instinct GPU** (MI250, MI300 or similar) with ROCm 6.x
- Python 3.11+
- [Ollama](https://ollama.ai) installed
- [vLLM](https://vllm.ai) with ROCm support
- Hugging Face account + token (for Llama 3.1 access)

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-username/adk-multi-agent-system.git
cd adk-multi-agent-system
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your HF_TOKEN and any custom values
```

### 3. Start the LLM backends

**Terminal 1 — vLLM (Burger Agent backend):**
```bash
./scripts/start_vllm.sh
```

**Terminal 2 — Ollama (Pizza Agent + Root Agent backend):**
```bash
./scripts/start_ollama.sh
```

Or start everything at once:
```bash
./scripts/start_all.sh $HF_TOKEN
```

### 4. Launch the agents

**Terminal 3 — Burger Seller Agent:**
```bash
python -m agents.burger_agent.server
```

**Terminal 4 — Pizza Seller Agent:**
```bash
python -m agents.pizza_agent.server
```

**Terminal 5 — Purchasing Concierge + UI:**
```bash
python -m agents.purchasing_agent.app
```

### 5. Open the UI

Navigate to **http://localhost:8087** and try:
- *"What burgers do you have?"*
- *"I'd like 2 Pepperoni Pizzas and a Classic Cheeseburger"*
- *"Show me the full menu"*

---

## How It Works

### The A2A Protocol

Each seller agent publishes an **Agent Card** — a JSON metadata document at `/.well-known/agent.json` describing its identity, capabilities, skills, and authentication requirements.

```json
{
  "name": "burger_seller_agent",
  "description": "Helps with creating burger orders",
  "url": "http://localhost:10001/",
  "version": "1.0.0",
  "authentication": { "schemes": ["Basic"] },
  "skills": [{
    "id": "create_burger_order",
    "name": "Burger Order Creation Tool",
    "examples": ["I want to order 2 classic cheeseburgers"]
  }]
}
```

The root agent resolves these cards at startup, builds a registry, and routes user requests to the appropriate agent via HTTP `tasks/send`.

### Task Lifecycle

```
User message
    │
    ▼
PurchasingAgent.send_task()
    │  ── HTTP POST /tasks/send ──▶  SellerAgent A2A Server
    │                                       │
    │                                  Agent processes
    │                                       │
    │  ◀── TaskStatus response ────────────┘
    │        state: input_required | completed | failed
    │
    ▼
Response streamed to Gradio UI
```

### Tool Execution Pattern

LLMs handle reasoning; tools handle deterministic execution:

```python
# LLM decides: "user wants 2 cheeseburgers" → calls create_burger_order
# Tool executes deterministically:
@tool("create_order")
def create_burger_order(order_items: list[OrderItem]) -> str:
    order_id = str(uuid.uuid4())
    order = Order(order_id=order_id, status="created", order_items=order_items)
    return f"Order {order.model_dump()} has been created"
```

---

## Configuration

All configuration is via environment variables. See `.env.example` for full reference.

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_MODEL` | `hosted_vllm/meta-llama/Llama-3.1-8B-Instruct` | vLLM model string |
| `OPENAI_API_BASE` | `http://localhost:8088/v1` | vLLM server URL |
| `OLLAMA_MODEL` | `ollama_chat/llama3.1:latest` | Ollama model string |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `PIZZA_SELLER_AGENT_URL` | `http://localhost:10000` | Pizza agent endpoint |
| `BURGER_SELLER_AGENT_URL` | `http://localhost:10001` | Burger agent endpoint |
| `PIZZA_SELLER_AGENT_AUTH` | `pizza123` | Pizza agent API key |
| `BURGER_SELLER_AGENT_AUTH` | `burgeruser123:burgerpass123` | Burger agent Basic Auth |
| `HF_TOKEN` | — | HuggingFace token for model access |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Menus

**Burger Menu**
| Item | Price |
|------|-------|
| Classic Cheeseburger | IDR 85K |
| Double Cheeseburger | IDR 110K |
| Spicy Chicken Burger | IDR 80K |
| Spicy Cajun Burger | IDR 85K |

**Pizza Menu**
| Item | Price |
|------|-------|
| Margherita Pizza | IDR 100K |
| Pepperoni Pizza | IDR 140K |
| Hawaiian Pizza | IDR 110K |
| Veggie Pizza | IDR 100K |
| BBQ Chicken Pizza | IDR 130K |

---

## Security

- All inter-agent communication uses HTTP with authentication enforced at each server
- JWKS endpoint (`/.well-known/jwks.json`) supports push notification verification
- Credentials are environment-variable driven — never hardcoded
- Each agent enforces least-privilege access (burger agent cannot call pizza endpoints and vice versa)
- Production deployments should replace HTTP with HTTPS + valid TLS certificates

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push and open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) and ensure `pytest tests/` passes before submitting.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/)
- [Google A2A Protocol](https://github.com/google/a2a)
- [AMD ROCm Platform](https://rocm.docs.amd.com/)
- [vLLM Project](https://github.com/vllm-project/vllm)
- [CrewAI](https://github.com/crewAIInc/crewAI)
- [LangGraph](https://github.com/langchain-ai/langgraph)
