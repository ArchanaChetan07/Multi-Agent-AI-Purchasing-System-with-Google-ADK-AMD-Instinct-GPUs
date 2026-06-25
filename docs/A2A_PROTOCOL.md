# A2A Protocol Deep Dive

## What is A2A?

The **Agent-to-Agent (A2A) protocol** is an open standard published by Google that defines how AI agents — regardless of the framework, vendor, or language they are built with — can discover, communicate with, and coordinate each other.

The specification lives at: https://github.com/google/a2a

---

## Core concepts

### Agent Card

An Agent Card is a JSON document served at `/.well-known/agent.json`. It is the agent's public identity — equivalent to a service manifest or OpenAPI spec for an AI agent.

```json
{
  "name": "burger_seller_agent",
  "description": "Burger store agent — answers menu questions and creates orders.",
  "url": "http://localhost:10001/",
  "version": "1.0.0",
  "authentication": {
    "schemes": ["Basic"]
  },
  "capabilities": {
    "pushNotifications": true
  },
  "defaultInputModes": ["text", "text/plain"],
  "defaultOutputModes": ["text", "text/plain"],
  "skills": [
    {
      "id": "create_burger_order",
      "name": "Burger Order Creation Tool",
      "description": "Presents the burger menu and handles order creation.",
      "tags": ["burger", "order", "food"],
      "examples": ["I want to order 2 classic cheeseburgers"]
    }
  ]
}
```

### Task

A Task is the unit of work in A2A. It carries a `Message` (with `Parts`) from the client to the server agent. The server processes the task and returns a `TaskStatus`.

```
Task {
  id: UUID
  sessionId: UUID
  message: Message {
    role: "user"
    parts: [TextPart { text: "I want to order a burger" }]
    metadata: { conversation_id, message_id }
  }
  acceptedOutputModes: ["text"]
}
```

### TaskState

The lifecycle of a task:

```
SUBMITTED → WORKING → COMPLETED
                   └→ INPUT_REQUIRED  (agent needs more info from user)
                   └→ FAILED
                   └→ CANCELED
                   └→ UNKNOWN
```

When the root agent receives `INPUT_REQUIRED`, it sets `tool_context.actions.escalate = True` to route the question back to the Gradio user.

---

## How it works in this project

### 1. Discovery

At startup, `PurchasingAgent` calls `A2ACardResolver(address).get_agent_card()` for each seller URL. This HTTP GET fetches the Agent Card and builds the connection registry.

### 2. Task dispatch

When the user sends a message, ADK invokes `send_task(agent_name, task)`:

```python
request = TaskSendParams(
    id=task_id,
    sessionId=session_id,
    message=Message(role="user", parts=[TextPart(text=task)], metadata=...),
    acceptedOutputModes=["text", "text/plain"],
)
response = await client.send_task(request)
```

### 3. Authentication

Each seller agent validates the incoming request before processing:

| Agent | Scheme | Header |
|-------|--------|--------|
| Burger Seller | Basic Auth | `Authorization: Basic <base64(user:pass)>` |
| Pizza Seller | Bearer Token | `Authorization: Bearer <api_key>` |

Credentials are stored in environment variables and injected by `RemoteAgentConnections` via `KNOWN_AUTH`.

### 4. Push notifications

Both seller agents expose `/.well-known/jwks.json` to support push notification auth. The `PushNotificationSenderAuth` class generates a JWK key pair and signs push messages. This enables real-time status updates without polling.

---

## Extending the system

To add a new seller agent:

1. Create `agents/new_agent/` with `agent.py`, `tools.py`, `server.py`, `config.py`
2. Implement `SUPPORTED_CONTENT_TYPES` and `invoke(query, session_id) -> dict`
3. Wrap it in `A2AServer` with an `AgentCard` and your chosen auth scheme
4. Add the agent URL to `PIZZA_SELLER_AGENT_URL` / env equivalent and register it in `start_all.sh`
5. The root agent will automatically discover it via Agent Card resolution at startup
