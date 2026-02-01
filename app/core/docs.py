"""
OpenAPI Documentation Configuration
====================================

Custom OpenAPI schema configuration with detailed descriptions,
examples, and enterprise-grade documentation.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


# API Tags with descriptions
tags_metadata = [
    {
        "name": "Authentication",
        "description": """
**Authentication & Authorization**

Secure endpoints for user authentication, registration, and token management.
All endpoints except `/auth/register` and `/auth/login` require Bearer token authentication.

**Authentication Flow:**
1. Register new user: `POST /auth/register`
2. Login: `POST /auth/login` → Receive access token
3. Use token in header: `Authorization: Bearer <token>`
4. Refresh token before expiry: `POST /auth/refresh`
        """,
    },
    {
        "name": "Tasks",
        "description": """
**Task Management**

CRUD operations for tasks with AI-powered processing.
Tasks can be created, updated, and executed with AI agents.

**Features:**
- Create tasks with natural language descriptions
- AI-powered task execution via agents
- Batch operations (bulk create, update, delete)
- Task status tracking (PENDING, RUNNING, COMPLETED, FAILED)
- Usage tracking and cost calculation
        """,
    },
    {
        "name": "Chat",
        "description": """
**Chat & Conversations**

Real-time chat interface for AI conversations with multi-turn context.

**Features:**
- Multi-turn conversations with context memory
- Streaming responses (SSE)
- Multiple AI provider support (OpenAI, Anthropic, Google, Groq, Ollama)
- Dynamic model selection
- Token usage tracking
- Conversation history export
        """,
    },
    {
        "name": "WebSocket",
        "description": """
**Real-Time WebSocket**

WebSocket endpoints for real-time communication and live updates.

**Features:**
- Real-time message streaming
- Connection health monitoring
- Automatic reconnection support
- Tenant-isolated connections
        """,
    },
    {
        "name": "Tenants",
        "description": """
**Multi-Tenant Management**

Tenant provisioning, configuration, and management.

**Features:**
- Tenant CRUD operations
- Subscription management
- Usage quotas and limits
- Billing configuration
- Tenant isolation guarantees
        """,
    },
    {
        "name": "Agents",
        "description": """
**AI Agent Management**

Database-driven AI agents with custom tools and configurations.

**Features:**
- Create custom AI agents with specific instructions
- Tool registration and execution
- Agent execution tracking
- Performance analytics
- Cost per agent tracking
        """,
    },
    {
        "name": "Providers",
        "description": """
**AI Provider Management**

Manage AI provider integrations and credentials.

**Supported Providers:**
- OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo)
- Anthropic (Claude 2, Claude 3 Opus/Sonnet/Haiku)
- Google (Gemini Pro, Gemini Pro Vision)
- Groq (Llama 2, Mixtral)
- Ollama (Local models)

**Features:**
- Encrypted credential storage
- Provider health checks
- Model listing and capabilities
- Cost tracking per provider
        """,
    },
    {
        "name": "Usage & Billing",
        "description": """
**Usage Tracking & Billing**

Monitor resource usage, costs, and generate billing reports.

**Features:**
- Real-time token usage tracking
- Cost calculation per provider/model
- Usage quotas and alerts
- Monthly/daily aggregation
- Export reports (CSV, JSON, PDF)
        """,
    },
    {
        "name": "Webhooks",
        "description": """
**Webhook Management**

Event-driven webhook notifications for external integrations.

**Supported Events:**
- `agent.completed` - Agent execution finished
- `agent.failed` - Agent execution failed
- `conversation.started` - New conversation
- `conversation.completed` - Conversation ended
- `usage.quota_exceeded` - Quota limit reached
- `subscription.expiring` - Subscription expiring soon

**Features:**
- Event subscriptions
- Automatic retry with exponential backoff
- HMAC signature verification
- Delivery tracking and logs
        """,
    },
    {
        "name": "Admin",
        "description": """
**Administration**

Platform administration and monitoring endpoints.

**Features:**
- System health checks
- User management (CRUD, role assignment)
- Tenant management (suspend, activate)
- Audit logs
- Performance metrics
- Database statistics
        """,
    },
    {
        "name": "Health",
        "description": """
**Health & Monitoring**

System health checks and monitoring endpoints.

**Endpoints:**
- `/health` - Overall system health
- `/health/database` - Database connectivity
- `/health/redis` - Redis connectivity
- `/health/celery` - Background workers status
- `/metrics` - Prometheus-compatible metrics
        """,
    },
]


# Custom OpenAPI schema
def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        OpenAPI schema dictionary
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Task Assistant AI SaaS API",
        version="1.0.0",
        description="""
# 🚀 Task Assistant AI - Enterprise AI SaaS Platform

A production-grade, multi-tenant AI SaaS platform with advanced orchestration,
provider abstraction, and enterprise features.

## 🌟 Key Features

- **Multi-Tenant Architecture**: Complete tenant isolation with row-level security
- **AI Provider Abstraction**: Unified interface for 5+ AI providers
- **Database-Driven Agents**: Create and manage AI agents via API
- **Real-Time Chat**: WebSocket and SSE streaming support
- **Advanced Orchestration**: Tool execution, conversation management, usage tracking
- **Enterprise Features**: Rate limiting, caching, webhooks, monitoring
- **RBAC**: Fine-grained role-based access control with wildcards
- **Production-Ready**: Celery background jobs, Sentry monitoring, Redis caching

## 🔐 Authentication

All API endpoints (except registration and login) require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
     https://api.taskassistant.ai/api/v1/tasks
```

### Getting Started

1. **Register**: `POST /api/v1/auth/register`
2. **Login**: `POST /api/v1/auth/login` → Get access token
3. **Use API**: Include token in `Authorization` header

Tokens expire after 24 hours. Use `/api/v1/auth/refresh` to get a new token.

## 📊 Rate Limits

Default rate limits per tenant:
- **100 requests/minute**
- **1,000 requests/hour**

Per user:
- **50 requests/minute**

Authentication endpoints:
- **10 requests/15 minutes**

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Timestamp when limit resets

## 🔗 Base URLs

- **Production**: `https://api.taskassistant.ai`
- **Staging**: `https://staging-api.taskassistant.ai`
- **Development**: `http://localhost:8000`

## 📚 SDKs

Official SDKs available:
- **Python**: `pip install taskassistant-sdk`
- **JavaScript/TypeScript**: `npm install @taskassistant/sdk`
- **Go**: `go get github.com/taskassistant/sdk-go`

## 🆘 Support

- **Documentation**: https://docs.taskassistant.ai
- **Support**: support@taskassistant.ai
- **GitHub**: https://github.com/taskassistant/platform

## 📜 License

Enterprise License - Contact sales@taskassistant.ai
        """,
        routes=app.routes,
        tags=tags_metadata,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication",
        },
    }

    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []},
    ]

    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "https://api.taskassistant.ai",
            "description": "Production server",
        },
        {
            "url": "https://staging-api.taskassistant.ai",
            "description": "Staging server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
    ]

    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "Task Assistant Support",
        "email": "support@taskassistant.ai",
        "url": "https://taskassistant.ai/support",
    }

    openapi_schema["info"]["license"] = {
        "name": "Enterprise License",
        "url": "https://taskassistant.ai/license",
    }

    # Add external docs
    openapi_schema["externalDocs"] = {
        "description": "Full Documentation",
        "url": "https://docs.taskassistant.ai",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Common response examples
example_responses = {
    "validation_error": {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {
                            "loc": ["body", "email"],
                            "msg": "value is not a valid email address",
                            "type": "value_error.email",
                        }
                    ]
                }
            }
        },
    },
    "authentication_error": {
        "description": "Authentication Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Could not validate credentials"
                }
            }
        },
    },
    "authorization_error": {
        "description": "Authorization Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Insufficient permissions"
                }
            }
        },
    },
    "rate_limit_error": {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Rate limit exceeded. Try again in 60 seconds.",
                    "retry_after": 60,
                }
            }
        },
    },
    "not_found_error": {
        "description": "Resource Not Found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Resource not found"
                }
            }
        },
    },
    "server_error": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An unexpected error occurred. Please try again later.",
                    "error_id": "err_abc123def456",
                }
            }
        },
    },
}


def add_response_examples(responses: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    Add common response examples to endpoint responses.
    
    Args:
        responses: Existing responses dictionary
        
    Returns:
        Updated responses with examples
    """
    common_responses = {
        401: example_responses["authentication_error"],
        403: example_responses["authorization_error"],
        404: example_responses["not_found_error"],
        422: example_responses["validation_error"],
        429: example_responses["rate_limit_error"],
        500: example_responses["server_error"],
    }
    
    return {**responses, **common_responses}


# Request body examples
example_requests = {
    "register": {
        "email": "user@example.com",
        "password": "SecureP@ssw0rd123",
        "full_name": "John Doe",
        "tenant_name": "Acme Corp",
    },
    "login": {
        "email": "user@example.com",
        "password": "SecureP@ssw0rd123",
    },
    "create_task": {
        "title": "Analyze quarterly sales data",
        "description": "Generate insights from Q4 2025 sales data and create summary",
        "priority": "high",
        "due_date": "2026-02-15T00:00:00Z",
        "metadata": {
            "department": "sales",
            "quarter": "Q4",
        },
    },
    "chat_message": {
        "message": "What are the key trends in our sales data?",
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 500,
    },
    "create_agent": {
        "name": "Sales Analyst",
        "description": "Analyzes sales data and generates insights",
        "instructions": "You are a sales analyst. Analyze data and provide actionable insights.",
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.5,
        "tools": ["calculator", "search"],
    },
    "create_webhook": {
        "url": "https://myapp.com/webhooks/taskassistant",
        "event_types": ["agent.completed", "usage.quota_exceeded"],
        "secret": "webhook_secret_key_123",
        "is_active": True,
    },
}


__all__ = [
    "tags_metadata",
    "custom_openapi",
    "example_responses",
    "example_requests",
    "add_response_examples",
]
