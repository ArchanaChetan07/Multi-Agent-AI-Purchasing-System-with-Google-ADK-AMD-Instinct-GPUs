# Architecture

## System overview

This system implements a three-agent **Agent-to-Agent (A2A)** architecture built on Google's open A2A protocol. The design goal is to demonstrate that agents built on entirely different frameworks can collaborate in a shared task through a common communication standard.

```
User
 │
 ▼
Purchasing Concierge (Root Agent)
 │  Google ADK + LiteLLM + Ollama
 │
 ├──[A2A HTTP]──▶ Burger Seller Agent
 │                CrewAI + vLLM
 │                Port :10001, Basic Auth
 │
 └──[A2A HTTP]──▶ Pizza Seller Agent
                  LangGraph + Ollama
                  Port :10000, Bearer Auth
```

## Design decisions

### Why three different frameworks?

The primary purpose of this project is to demonstrate **cross-framework interoperability via the A2A protocol**. Using ADK, CrewAI, and LangGraph together shows that agents are not coupled to a single vendor or abstraction layer.

### Why vLLM for the Burger Agent?

The Burger Agent uses CrewAI, which relies on OpenAI-compatible tool-calling APIs. vLLM provides exactly this interface with support for custom Jinja chat templates needed to correctly format tool-call prompts for Llama 3.1.

### Why Ollama for the Pizza Agent?

Ollama is lighter weight and uses quantized models (GGUF), making it suitable for the Pizza Agent and the Root Agent which share a single Ollama instance. Memory pressure is managed by setting `--gpu-memory-utilization 0.6` on vLLM, leaving the remainder for Ollama.

### Why separate auth per agent?

Different real-world services use different auth schemes. Demonstrating Basic Auth (Burger) and Bearer token (Pizza) shows that the A2A protocol is auth-agnostic and that each agent can enforce its own security independently.

## Agent internals

### Burger Seller Agent (CrewAI)

```
User query
    │
    ▼
BurgerSellerAgent.invoke()
    │
    ▼
CrewAI: Agent + Task + Crew
    │
    ├── LLM decides: menu question → answer directly
    │
    └── LLM decides: order → calls create_burger_order tool
                                    │
                                    ▼
                               Order(order_id, items)
                                    │
                                    ▼
                          ResponseFormat(status, message)
                                    │
                                    ▼
                        A2A TaskStatus response
```

### Pizza Seller Agent (LangGraph)

```
User query
    │
    ▼
PizzaSellerAgent.invoke()
    │
    ▼
LangGraph ReAct graph (stateful, MemorySaver)
    │
    ├── Reason: understand request
    ├── Act:    call create_pizza_order if needed
    └── Observe: format ResponseFormat output
                    │
                    ▼
          A2A TaskStatus response
```

### Purchasing Concierge (Google ADK)

```
User message
    │
    ▼
ADK Runner → PurchasingAgent
    │
    ├── before_model_callback: init session state
    │
    ├── root_instruction: dynamic prompt with agent registry + active agent
    │
    └── LiteLLM → Llama 3.1 via Ollama
            │
            └── calls send_task(agent_name, task)
                    │
                    ├── resolve RemoteAgentConnections
                    ├── POST /tasks/send to remote A2A server
                    ├── handle TaskState (COMPLETED / INPUT_REQUIRED / FAILED)
                    └── stream parts back to Gradio UI
```

## A2A Protocol flow

```
Root Agent                     Seller Agent
    │                               │
    │── GET /agent.json ───────────▶│  (Agent Card discovery)
    │◀─ AgentCard JSON ─────────────│
    │                               │
    │── POST /tasks/send ──────────▶│  (Task dispatch)
    │   {id, sessionId, message}    │
    │                               │  Agent invokes LLM + tools
    │◀─ Task response ──────────────│
    │   {status: completed|         │
    │    input_required|failed,     │
    │    message, artifacts}        │
    │                               │
    │   (if input_required)         │
    │── escalate to user ──────────▶│  (user provides input)
    │   re-invoke send_task         │
```

## Session and state

ADK's `InMemorySessionService` maintains three state keys across turns:

| Key | Type | Purpose |
|-----|------|---------|
| `session_id` | `str` (UUID) | Correlation ID propagated to all remote agents |
| `session_active` | `bool` | Whether a seller agent task is in progress |
| `active_agent` | `str` | Name of the currently engaged seller agent |

LangGraph's `MemorySaver` checkpoints the Pizza Agent's full graph state by `thread_id` (= `session_id`), enabling it to remember earlier parts of the ordering conversation.

## Security model

| Layer | Mechanism |
|-------|-----------|
| Transport | HTTP (HTTPS recommended for production) |
| Burger Agent | HTTP Basic Auth (`Authorization: Basic <b64>`) |
| Pizza Agent | Bearer token (`Authorization: Bearer <token>`) |
| Push notifications | JWKS endpoint + signed JWT verification |
| Credentials | Environment variables only — never in source |
