# SDK Generation Guide

Guide for generating and using client SDKs for the Task Assistant AI SaaS API.

## Table of Contents

- [Overview](#overview)
- [Python SDK](#python-sdk)
- [JavaScript/TypeScript SDK](#javascripttypescript-sdk)
- [OpenAPI Generator](#openapi-generator)
- [Manual SDK Usage](#manual-sdk-usage)

---

## Overview

Client SDKs can be automatically generated from the OpenAPI specification. The API provides a comprehensive OpenAPI 3.0 schema at `/openapi.json`.

### OpenAPI Specification

Download the OpenAPI specification:

```bash
curl https://api.taskassistant.ai/openapi.json > openapi.json
```

Or access it in your browser:

- **Swagger UI**: https://api.taskassistant.ai/docs
- **ReDoc**: https://api.taskassistant.ai/redoc
- **Raw JSON**: https://api.taskassistant.ai/openapi.json

---

## Python SDK

### Using OpenAPI Generator

Install the OpenAPI Generator:

```bash
# Using npm
npm install @openapitools/openapi-generator-cli -g

# Or download the JAR
wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.2.0/openapi-generator-cli-7.2.0.jar -O openapi-generator-cli.jar
```

Generate the Python SDK:

```bash
openapi-generator-cli generate \
  -i https://api.taskassistant.ai/openapi.json \
  -g python \
  -o ./taskassistant-python-sdk \
  --additional-properties=packageName=taskassistant,projectName=taskassistant-sdk,packageVersion=1.0.0
```

Or using the JAR:

```bash
java -jar openapi-generator-cli.jar generate \
  -i https://api.taskassistant.ai/openapi.json \
  -g python \
  -o ./taskassistant-python-sdk \
  --additional-properties=packageName=taskassistant,projectName=taskassistant-sdk,packageVersion=1.0.0
```

### Install Generated SDK

```bash
cd taskassistant-python-sdk
pip install -e .
```

### Python SDK Usage

```python
from taskassistant import ApiClient, Configuration, AuthenticationApi, TasksApi, ChatApi

# Configure API client
config = Configuration()
config.host = "https://api.taskassistant.ai/api/v1"

# Login to get token
auth_api = AuthenticationApi(ApiClient(config))
login_response = auth_api.login_api_v1_auth_login_post({
    "email": "user@example.com",
    "password": "password123"
})

# Set token for future requests
config.access_token = login_response.access_token

# Create API clients
tasks_api = TasksApi(ApiClient(config))
chat_api = ChatApi(ApiClient(config))

# Create a task
task = tasks_api.create_task_api_v1_tasks_post({
    "title": "Analyze sales data",
    "description": "Generate Q4 insights",
    "priority": "high"
})
print(f"Created task: {task.id}")

# Create conversation
conversation = chat_api.create_conversation_api_v1_chat_conversations_post({
    "title": "Sales Q&A",
    "provider": "openai",
    "model": "gpt-4"
})

# Send message
message = chat_api.send_message_api_v1_chat_conversations_conversation_id_messages_post(
    conversation_id=conversation.id,
    body={
        "message": "What are the key sales trends?",
        "temperature": 0.7
    }
)
print(f"AI Response: {message.content}")
```

---

## JavaScript/TypeScript SDK

### Generate TypeScript SDK

```bash
openapi-generator-cli generate \
  -i https://api.taskassistant.ai/openapi.json \
  -g typescript-fetch \
  -o ./taskassistant-ts-sdk \
  --additional-properties=npmName=@taskassistant/sdk,npmVersion=1.0.0,supportsES6=true
```

### Install Generated SDK

```bash
cd taskassistant-ts-sdk
npm install
npm run build
```

### TypeScript SDK Usage

```typescript
import {
  Configuration,
  AuthenticationApi,
  TasksApi,
  ChatApi,
  AgentsApi,
} from "@taskassistant/sdk";

// Configure API client
const config = new Configuration({
  basePath: "https://api.taskassistant.ai/api/v1",
});

// Login
const authApi = new AuthenticationApi(config);
const loginResponse = await authApi.loginApiV1AuthLoginPost({
  loginRequest: {
    email: "user@example.com",
    password: "password123",
  },
});

// Update config with token
const authenticatedConfig = new Configuration({
  basePath: "https://api.taskassistant.ai/api/v1",
  accessToken: loginResponse.access_token,
});

// Create API clients
const tasksApi = new TasksApi(authenticatedConfig);
const chatApi = new ChatApi(authenticatedConfig);
const agentsApi = new AgentsApi(authenticatedConfig);

// Create task
const task = await tasksApi.createTaskApiV1TasksPost({
  taskCreate: {
    title: "Analyze sales data",
    description: "Generate Q4 insights",
    priority: "high",
  },
});
console.log(`Created task: ${task.id}`);

// Execute agent
const result = await agentsApi.executeAgentApiV1AgentsAgentIdExecutePost({
  agentId: "agent-uuid",
  agentExecuteRequest: {
    input: "Analyze Q4 2025 sales performance",
  },
});
console.log(`Agent output: ${result.output}`);
```

---

## OpenAPI Generator

### Configuration File

Create `openapi-config.yaml`:

```yaml
# Python configuration
generatorName: python
outputDir: ./sdk/python
additionalProperties:
  packageName: taskassistant
  projectName: taskassistant-sdk
  packageVersion: 1.0.0
  library: asyncio


# TypeScript configuration
---
generatorName: typescript-fetch
outputDir: ./sdk/typescript
additionalProperties:
  npmName: "@taskassistant/sdk"
  npmVersion: 1.0.0
  supportsES6: true
  withInterfaces: true
```

Generate with config:

```bash
openapi-generator-cli generate \
  -i https://api.taskassistant.ai/openapi.json \
  -c openapi-config.yaml
```

### Available Generators

View all available generators:

```bash
openapi-generator-cli list
```

Popular generators:

- `python` - Python SDK
- `typescript-fetch` - TypeScript with fetch API
- `typescript-axios` - TypeScript with axios
- `javascript` - JavaScript SDK
- `go` - Go SDK
- `java` - Java SDK
- `csharp` - C# SDK
- `php` - PHP SDK
- `ruby` - Ruby SDK
- `rust` - Rust SDK

---

## Manual SDK Usage

If you prefer to create requests manually without a generated SDK:

### Python with Requests

```python
import requests

BASE_URL = "https://api.taskassistant.ai/api/v1"

class TaskAssistantClient:
    def __init__(self, email: str, password: str):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.token = self._login(email, password)
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    def _login(self, email: str, password: str) -> str:
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def create_task(self, title: str, description: str, priority: str = "medium"):
        response = self.session.post(
            f"{self.base_url}/tasks",
            json={
                "title": title,
                "description": description,
                "priority": priority
            }
        )
        response.raise_for_status()
        return response.json()

    def execute_agent(self, agent_id: str, input_text: str):
        response = self.session.post(
            f"{self.base_url}/agents/{agent_id}/execute",
            json={"input": input_text}
        )
        response.raise_for_status()
        return response.json()

    def send_chat_message(self, conversation_id: str, message: str):
        response = self.session.post(
            f"{self.base_url}/chat/conversations/{conversation_id}/messages",
            json={"message": message}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = TaskAssistantClient("user@example.com", "password123")

task = client.create_task(
    title="Analyze sales",
    description="Generate insights",
    priority="high"
)
print(f"Created task: {task['id']}")

result = client.execute_agent(
    agent_id="agent-uuid",
    input_text="Analyze Q4 sales"
)
print(f"Output: {result['output']}")
```

### JavaScript with Fetch

```javascript
class TaskAssistantClient {
  constructor(baseUrl = "https://api.taskassistant.ai/api/v1") {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.token = data.access_token;
    return this.token;
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        Authorization: `Bearer ${this.token}`,
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async createTask(title, description, priority = "medium") {
    return this.request("/tasks", {
      method: "POST",
      body: JSON.stringify({ title, description, priority }),
    });
  }

  async executeAgent(agentId, input) {
    return this.request(`/agents/${agentId}/execute`, {
      method: "POST",
      body: JSON.stringify({ input }),
    });
  }

  async sendChatMessage(conversationId, message) {
    return this.request(`/chat/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  }
}

// Usage
const client = new TaskAssistantClient();
await client.login("user@example.com", "password123");

const task = await client.createTask(
  "Analyze sales",
  "Generate insights",
  "high",
);
console.log(`Created task: ${task.id}`);

const result = await client.executeAgent("agent-uuid", "Analyze Q4 sales");
console.log(`Output: ${result.output}`);
```

---

## Best Practices

### Error Handling

Always handle errors properly:

```python
from taskassistant.exceptions import ApiException

try:
    task = tasks_api.create_task(...)
except ApiException as e:
    if e.status == 401:
        # Re-authenticate
        pass
    elif e.status == 429:
        # Rate limit exceeded, wait and retry
        time.sleep(60)
    else:
        # Log error
        logger.error(f"API error: {e}")
```

### Rate Limiting

Implement client-side rate limiting:

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=50):
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper
    return decorator

@rate_limit(calls_per_minute=50)
def api_call():
    return tasks_api.list_tasks()
```

### Token Refresh

Automatically refresh expired tokens:

```python
class AutoRefreshClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.token = None
        self.token_expiry = None
        self._refresh_token()

    def _refresh_token(self):
        # Login to get new token
        response = auth_api.login({"email": self.email, "password": self.password})
        self.token = response.access_token
        self.token_expiry = time.time() + response.expires_in

    def _ensure_valid_token(self):
        if time.time() >= self.token_expiry - 300:  # Refresh 5 min before expiry
            self._refresh_token()

    def make_request(self, func, *args, **kwargs):
        self._ensure_valid_token()
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            if e.status == 401:
                # Token invalid, refresh and retry
                self._refresh_token()
                return func(*args, **kwargs)
            raise
```

---

## Additional Resources

- **OpenAPI Specification**: https://api.taskassistant.ai/openapi.json
- **Interactive Docs**: https://api.taskassistant.ai/docs
- **ReDoc Documentation**: https://api.taskassistant.ai/redoc
- **OpenAPI Generator**: https://openapi-generator.tech
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## Support

For SDK issues or questions:

- **Email**: sdk-support@taskassistant.ai
- **GitHub Issues**: https://github.com/taskassistant/sdk/issues
- **Community Forum**: https://community.taskassistant.ai
