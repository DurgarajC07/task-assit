# API Documentation

Complete API reference for Task Assistant AI SaaS platform.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limits](#rate-limits)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Tasks](#task-endpoints)
  - [Chat](#chat-endpoints)
  - [Agents](#agent-endpoints)
  - [Webhooks](#webhook-endpoints)
- [WebSocket](#websocket)
- [Examples](#examples)

---

## Authentication

All API endpoints require Bearer token authentication (except `/auth/register` and `/auth/login`).

### Getting an Access Token

1. **Register a new account**:

```bash
curl -X POST https://api.taskassistant.ai/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ssw0rd123",
    "full_name": "John Doe",
    "tenant_name": "Acme Corp"
  }'
```

2. **Login to get access token**:

```bash
curl -X POST https://api.taskassistant.ai/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ssw0rd123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

3. **Use token in subsequent requests**:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://api.taskassistant.ai/api/v1/tasks
```

### Token Expiration

- Access tokens expire after **24 hours**
- Use the `/auth/refresh` endpoint to get a new token before expiry
- Expired tokens return `401 Unauthorized`

---

## Rate Limits

Rate limits are enforced per tenant and per user:

| Scope              | Limit                                      |
| ------------------ | ------------------------------------------ |
| **Tenant**         | 100 requests/minute<br>1,000 requests/hour |
| **User**           | 50 requests/minute                         |
| **Auth Endpoints** | 10 requests/15 minutes                     |

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706788800
```

### Rate Limit Exceeded

When limit is exceeded, you'll receive a `429 Too Many Requests` response:

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "retry_after": 60
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message here",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2026-02-01T10:30:00Z"
}
```

### HTTP Status Codes

| Code  | Meaning               | Description                              |
| ----- | --------------------- | ---------------------------------------- |
| `200` | OK                    | Request successful                       |
| `201` | Created               | Resource created successfully            |
| `204` | No Content            | Successful delete/update with no content |
| `400` | Bad Request           | Invalid request parameters               |
| `401` | Unauthorized          | Missing or invalid authentication        |
| `403` | Forbidden             | Insufficient permissions                 |
| `404` | Not Found             | Resource not found                       |
| `422` | Validation Error      | Request validation failed                |
| `429` | Too Many Requests     | Rate limit exceeded                      |
| `500` | Internal Server Error | Server error (reported to monitoring)    |

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Endpoints

### Authentication Endpoints

#### POST `/api/v1/auth/register`

Register a new user and create a tenant.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd123",
  "full_name": "John Doe",
  "tenant_name": "Acme Corp"
}
```

**Response (201):**

```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "tenant_id": "tenant-uuid",
  "created_at": "2026-02-01T10:30:00Z"
}
```

---

#### POST `/api/v1/auth/login`

Login and receive access token.

**Request:**

```json
{
  "email": "user@example.com",
  "password": "SecureP@ssw0rd123"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

#### POST `/api/v1/auth/refresh`

Refresh access token.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

### Task Endpoints

#### GET `/api/v1/tasks`

List all tasks for the current tenant.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**

- `status` (optional): Filter by status (`pending`, `completed`, `failed`)
- `priority` (optional): Filter by priority (`low`, `medium`, `high`)
- `limit` (optional): Max results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response (200):**

```json
{
  "items": [
    {
      "id": "uuid-here",
      "title": "Analyze sales data",
      "description": "Generate Q4 2025 insights",
      "status": "completed",
      "priority": "high",
      "due_date": "2026-02-15T00:00:00Z",
      "created_at": "2026-02-01T10:30:00Z",
      "completed_at": "2026-02-01T12:45:00Z"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

---

#### POST `/api/v1/tasks`

Create a new task.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "title": "Analyze quarterly sales data",
  "description": "Generate insights from Q4 2025 sales data",
  "priority": "high",
  "due_date": "2026-02-15T00:00:00Z",
  "metadata": {
    "department": "sales",
    "quarter": "Q4"
  }
}
```

**Response (201):**

```json
{
  "id": "uuid-here",
  "title": "Analyze quarterly sales data",
  "description": "Generate insights from Q4 2025 sales data",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-02-15T00:00:00Z",
  "created_at": "2026-02-01T10:30:00Z"
}
```

---

#### GET `/api/v1/tasks/{task_id}`

Get task details.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200):**

```json
{
  "id": "uuid-here",
  "title": "Analyze sales data",
  "description": "Generate Q4 2025 insights",
  "status": "completed",
  "priority": "high",
  "due_date": "2026-02-15T00:00:00Z",
  "result": {
    "insights": ["Sales increased 15%", "Top product: Widget A"],
    "charts": ["chart_url_1", "chart_url_2"]
  },
  "created_at": "2026-02-01T10:30:00Z",
  "completed_at": "2026-02-01T12:45:00Z"
}
```

---

### Chat Endpoints

#### POST `/api/v1/chat/conversations`

Create a new conversation.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "title": "Sales Analysis Q&A",
  "provider": "openai",
  "model": "gpt-4",
  "system_prompt": "You are a helpful sales analyst.",
  "metadata": {
    "department": "sales"
  }
}
```

**Response (201):**

```json
{
  "id": "uuid-here",
  "title": "Sales Analysis Q&A",
  "provider": "openai",
  "model": "gpt-4",
  "created_at": "2026-02-01T10:30:00Z"
}
```

---

#### POST `/api/v1/chat/conversations/{conversation_id}/messages`

Send a message in a conversation.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "message": "What are the key trends in our Q4 sales?",
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false
}
```

**Response (200):**

```json
{
  "id": "message-uuid",
  "conversation_id": "conversation-uuid",
  "role": "assistant",
  "content": "Based on the Q4 data, here are the key trends:\n\n1. Sales increased by 15% YoY\n2. Top product: Widget A (35% of revenue)\n3. Regional growth: West Coast +25%, East Coast +10%",
  "tokens_used": 87,
  "cost": 0.00261,
  "created_at": "2026-02-01T10:31:00Z"
}
```

---

#### POST `/api/v1/chat/conversations/{conversation_id}/messages` (Streaming)

Stream AI response in real-time.

**Request:**

```json
{
  "message": "Explain the sales trends in detail",
  "stream": true
}
```

**Response (200 - Server-Sent Events):**

```
data: {"type": "start", "message_id": "uuid"}

data: {"type": "token", "content": "Based"}

data: {"type": "token", "content": " on"}

data: {"type": "token", "content": " the"}

data: {"type": "done", "tokens_used": 87, "cost": 0.00261}
```

---

### Agent Endpoints

#### POST `/api/v1/agents`

Create a new AI agent.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "name": "Sales Analyst",
  "description": "Analyzes sales data and generates insights",
  "instructions": "You are a sales analyst. Analyze data and provide actionable insights with specific numbers.",
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.5,
  "tools": ["calculator", "search"],
  "metadata": {
    "department": "sales"
  }
}
```

**Response (201):**

```json
{
  "id": "uuid-here",
  "name": "Sales Analyst",
  "description": "Analyzes sales data and generates insights",
  "provider": "openai",
  "model": "gpt-4",
  "is_active": true,
  "created_at": "2026-02-01T10:30:00Z"
}
```

---

#### POST `/api/v1/agents/{agent_id}/execute`

Execute an agent with input.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "input": "Analyze the sales performance for Product X in Q4 2025",
  "metadata": {
    "product": "Product X",
    "quarter": "Q4 2025"
  }
}
```

**Response (200):**

```json
{
  "run_id": "run-uuid",
  "status": "completed",
  "output": "Product X had strong Q4 performance:\n- Revenue: $2.5M (+18% YoY)\n- Units sold: 15,000 (+22% YoY)\n- Top region: West Coast (45%)\n- Recommendation: Increase inventory for Q1 2026",
  "tokens_used": 320,
  "cost": 0.0096,
  "execution_time_ms": 2300,
  "tools_used": ["calculator"],
  "created_at": "2026-02-01T10:30:00Z",
  "completed_at": "2026-02-01T10:30:02Z"
}
```

---

### Webhook Endpoints

#### POST `/api/v1/webhooks`

Create a webhook subscription.

**Headers:**

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request:**

```json
{
  "url": "https://myapp.com/webhooks/taskassistant",
  "event_types": [
    "agent.completed",
    "usage.quota_exceeded",
    "subscription.expiring"
  ],
  "secret": "webhook_secret_key_123",
  "description": "Production webhook",
  "is_active": true
}
```

**Response (201):**

```json
{
  "id": "webhook-uuid",
  "url": "https://myapp.com/webhooks/taskassistant",
  "event_types": ["agent.completed", "usage.quota_exceeded"],
  "is_active": true,
  "created_at": "2026-02-01T10:30:00Z"
}
```

---

## WebSocket

### Connection

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket("wss://api.taskassistant.ai/api/v1/ws");

ws.onopen = () => {
  // Authenticate
  ws.send(
    JSON.stringify({
      type: "auth",
      token: "YOUR_ACCESS_TOKEN",
    }),
  );
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};
```

### Message Types

**Authentication:**

```json
{
  "type": "auth",
  "token": "YOUR_ACCESS_TOKEN"
}
```

**Chat Message:**

```json
{
  "type": "chat",
  "conversation_id": "uuid",
  "message": "Hello, how can I help?"
}
```

**Agent Execution:**

```json
{
  "type": "agent_execute",
  "agent_id": "uuid",
  "input": "Analyze sales data"
}
```

---

## Examples

### Python Example

```python
import requests

BASE_URL = "https://api.taskassistant.ai/api/v1"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = response.json()["access_token"]

# Create headers
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Create task
response = requests.post(f"{BASE_URL}/tasks", headers=headers, json={
    "title": "Analyze sales data",
    "description": "Generate Q4 insights",
    "priority": "high"
})
task = response.json()
print(f"Created task: {task['id']}")

# Execute agent
response = requests.post(
    f"{BASE_URL}/agents/{agent_id}/execute",
    headers=headers,
    json={"input": "Analyze Q4 sales"}
)
result = response.json()
print(f"Agent output: {result['output']}")
```

### JavaScript Example

```javascript
const BASE_URL = "https://api.taskassistant.ai/api/v1";

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
  }),
});
const { access_token } = await loginResponse.json();

// Create conversation
const conversationResponse = await fetch(`${BASE_URL}/chat/conversations`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${access_token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    title: "Sales Q&A",
    provider: "openai",
    model: "gpt-4",
  }),
});
const conversation = await conversationResponse.json();

// Send message
const messageResponse = await fetch(
  `${BASE_URL}/chat/conversations/${conversation.id}/messages`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${access_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: "What are the key sales trends?",
    }),
  },
);
const message = await messageResponse.json();
console.log("AI Response:", message.content);
```

### cURL Examples

**Create Agent:**

```bash
curl -X POST https://api.taskassistant.ai/api/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Analyst",
    "description": "Analyzes sales data",
    "instructions": "You are a sales analyst.",
    "provider": "openai",
    "model": "gpt-4"
  }'
```

**Execute Agent:**

```bash
curl -X POST https://api.taskassistant.ai/api/v1/agents/{agent_id}/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Analyze Q4 2025 sales performance"
  }'
```

**Create Webhook:**

```bash
curl -X POST https://api.taskassistant.ai/api/v1/webhooks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://myapp.com/webhooks",
    "event_types": ["agent.completed"],
    "secret": "my_secret_key"
  }'
```

---

## Next Steps

- [SDK Generation Guide](SDK_GENERATION.md)
- [Webhook Integration Guide](WEBHOOK_INTEGRATION.md)
- [Rate Limiting Details](RATE_LIMITING.md)
- [Error Handling Best Practices](ERROR_HANDLING.md)
