# Architecture Guide

## System Overview

The Task Assistant is built using a clean, modular multi-agent architecture with separation of concerns across multiple layers.

## Architecture Layers

### 1. **API Layer** (`app/api/`)
Handles HTTP requests and WebSocket connections.

**Components**:
- `auth.py`: Authentication endpoints (register, login, refresh, logout)
- `tasks.py`: CRUD endpoints for task management
- `chat.py`: Natural language interface
- `websocket.py`: Real-time WebSocket connections

**Responsibilities**:
- Request validation
- Route handling
- Response formatting
- Error handling

### 2. **Service Layer** (`app/services/`)
Business logic orchestration.

**Components**:
- `auth_service.py`: Authentication logic
- `task_service.py`: Task operations
- `chat_service.py`: Chat processing

**Responsibilities**:
- Service initialization
- Agent delegation
- Business rule enforcement
- Transaction management

### 3. **Agent Layer** (`app/agents/`)
Multi-agent system for intelligent task processing.

```
┌─────────────────────────────────────────────┐
│          AgentOrchestrator                   │
│  (Coordinates agent execution)               │
└────┬────────┬────────────┬────────────┬─────┘
     │        │            │            │
     ▼        ▼            ▼            ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Intent  │ │ Task     │ │ Conversa │ │ Memory   │
│ Agent   │ │ Management│ │tion     │ │ Agent    │
│         │ │ Agent    │ │ Agent    │ │          │
└─────────┘ └──────────┘ └──────────┘ └──────────┘
```

#### **Intent Agent**
- **Input**: User message
- **Process**: Analyzes and classifies intent
- **Output**: Intent type, confidence, extracted entities
- **Intents**: CREATE_TASK, LIST_TASKS, UPDATE_TASK, COMPLETE_TASK, DELETE_TASK, SEARCH_TASKS, GET_STATISTICS, UNCLEAR

#### **Task Management Agent**
- **Input**: Task operation parameters
- **Process**: Executes CRUD operations with validation
- **Output**: Task data or operation result
- **Handles**: Validation, permissions, audit logging

#### **Conversation Agent**
- **Input**: Intent, action result, user context
- **Process**: Generates natural language response
- **Output**: Friendly conversational message
- **Handles**: Tone, context awareness, error messaging

#### **Memory Agent**
- **Input**: Conversation data or query
- **Process**: Stores/retrieves conversation history and context
- **Output**: Historical data or user context
- **Handles**: Session management, user preferences, audit trail

### 4. **Core Layer** (`app/core/`)
Shared utilities and infrastructure.

**Components**:
- `security.py`: JWT, password hashing
- `exceptions.py`: Custom exceptions
- `dependencies.py`: FastAPI dependency injection
- `websocket_manager.py`: WebSocket connection management

### 5. **Data Layer**
ORM models and database operations.

**Components**:
- `models/`: SQLAlchemy ORM models
- `database.py`: Database connection and session management
- `schemas/`: Pydantic validation schemas

### 6. **Utility Layer** (`app/utils/`)
Helper functions.

**Components**:
- `date_parser.py`: Natural language date parsing
- `validators.py`: Input validation
- `formatters.py`: Response formatting

## Data Flow

### Chat Processing Flow

```
User Message
    │
    ▼
┌─────────────────────────┐
│ Store in Conversation   │
│ History (MemoryAgent)   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Intent Detection        │
│ (IntentAgent)           │
└────────┬────────────────┘
         │
    ┌────┴─────────────────────┐
    │ Confidence > 60%?         │
    │ Clarification needed?     │
    └────┬────────────────┬─────┘
         │ YES            │ NO
         ▼                ▼
    Ask User    ┌──────────────────────┐
    for         │ Execute Operation    │
    Details     │ (TaskAgent)          │
                └────────┬─────────────┘
                         │
                         ▼
               ┌──────────────────────┐
               │ Generate Response    │
               │ (ConversationAgent)  │
               └────────┬─────────────┘
                        │
                        ▼
               ┌──────────────────────┐
               │ Store Response       │
               │ (MemoryAgent)        │
               └────────┬─────────────┘
                        │
                        ▼
                  Return to User
```

### Task Creation via Chat

```
User: "Add task to buy milk tomorrow"
           │
           ▼
IntentAgent: "CREATE_TASK"
           │
           ▼
TaskAgent:
  1. Validate title
  2. Parse due date
  3. Insert into database
  4. Log audit trail
           │
           ▼
ConversationAgent: "✓ Task created!"
           │
           ▼
MemoryAgent: Store interaction
           │
           ▼
Response to user
```

## Database Schema Design

### User-centric data model

```
users (1) ─────────────────── (N) tasks
  │                              │
  │                              │ (soft delete)
  ├─────── (1:N) ──────────────│ task_audit_log
  │
  ├─────── (1:N) ────────── conversation_history
  │
  └─────── (1:N) ────────── user_sessions
```

### Key Indexes

- **tasks**: (user_id, status), (user_id, due_date), (user_id, priority)
- **conversation_history**: (user_id, session_id), (user_id, created_at)
- **task_audit_log**: (task_id, action), (user_id, created_at)
- **user_sessions**: (user_id, expires_at)

## Security Architecture

### Authentication Flow

```
┌─────────────┐
│   User      │
└────┬────────┘
     │ POST /register or /login
     ▼
┌──────────────────────┐
│ AuthService          │
│ - Hash password      │
│ - Create JWT tokens  │
└────┬─────────────────┘
     │ Store session
     ▼
┌──────────────────────┐
│ JWT Tokens           │
│ - access (15min)     │
│ - refresh (7days)    │
└────┬─────────────────┘
     │
     ├─► Access Token (API requests)
     └─► Refresh Token (get new access token)
```

### Authorization Model

**Row-Level Security**:
```python
# Every query filters by user_id
SELECT * FROM tasks WHERE user_id = current_user_id

# Verified at multiple layers
1. Database query filtering
2. Service layer checks
3. API dependency injection
4. Explicit assertions
```

## Error Handling Strategy

### Exception Hierarchy

```
Exception
└── TaskAssistantException
    ├── TaskNotFoundException
    ├── UserNotFoundException
    ├── UnauthorizedAccessException
    ├── ValidationException
    ├── IntentUnclearException
    ├── DuplicateResourceException
    └── InternalServerException
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly message",
    "details": "Technical details or suggestion"
  }
}
```

## Performance Considerations

### Database Optimization

1. **Indexes**: Strategic indexes on frequently queried columns
2. **Query Optimization**: Avoid N+1 queries
3. **Connection Pooling**: SQLAlchemy handles automatically
4. **Pagination**: Implement for large result sets
5. **Soft Deletes**: Avoid costly hard deletes

### Async/Await

- All I/O operations are async
- Non-blocking request handling
- Concurrent user support
- Database session per request

### Caching Opportunities

- User preferences (local memory)
- Recent tasks (session-based)
- Conversation context (request-scoped)

## Scalability Architecture

### Horizontal Scaling

```
┌─────────────────────────────────────────┐
│ Load Balancer (nginx/HAProxy)           │
├──────┬──────────┬──────────┬────────────┤
│      │          │          │            │
▼      ▼          ▼          ▼            ▼
API-1  API-2      API-3      API-4      API-N
```

### Database Scaling

**Current**: SQLite (single-file)
**Upgrade Path**: PostgreSQL with read replicas

```
Master (write)
    │
    ├─► Replica 1 (read)
    ├─► Replica 2 (read)
    └─► Replica N (read)
```

### Message Queue (Future)

```
API ──► Celery Queue ──► Workers
        (Redis/RabbitMQ)
```

## Deployment Architecture

### Development

```
Local Machine
├── SQLite database
├── FastAPI dev server
└── Hot reload enabled
```

### Docker Container

```
Docker Container
├── Python 3.11 slim image
├── SQLite or mounted DB
├── FastAPI with Gunicorn
└── Health checks enabled
```

### Production

```
Load Balancer (AWS ALB / nginx)
    │
    ├─► App Instance 1 (ECS / Kubernetes)
    ├─► App Instance 2
    └─► App Instance N
         │
         └─► PostgreSQL (RDS)
         │
         └─► S3 (file storage)
         │
         └─► CloudWatch (logging)
```

## Component Dependencies

```
FastAPI
├── SQLAlchemy (ORM)
│   └── SQLite/PostgreSQL
├── Pydantic (validation)
├── python-jose (JWT)
├── passlib (password hashing)
└── anthropic (Claude API)

Agents
├── IntentAgent → Anthropic
├── TaskManagementAgent → SQLAlchemy
├── ConversationAgent → Anthropic
└── MemoryAgent → SQLAlchemy
```

## Testing Architecture

### Unit Tests
- Test individual agents
- Test service logic
- Mock external dependencies (Claude API)
- Use in-memory SQLite

### Integration Tests
- Test API endpoints
- Test agent orchestration
- Test database operations
- Use test database

### Load Tests
- Concurrent user simulation
- Request throughput
- Database connection limits
- Memory usage profiling

## Future Enhancements

### Notification System
```
Task Events
    │
    ├─► Email Service
    ├─► SMS Service
    ├─► Push Notifications
    └─► In-app Notifications
```

### Task Collaboration
```
Task ──────────┐
               ├─ Shared with
               ├─ Comments
Permissions ───┴─ Activity log
```

### Analytics & Dashboard
```
Task Data
    │
    ├─ Aggregations
    ├─ Time series
    ├─ Trends
    └─ Visualizations
```

## Monitoring & Observability

### Logging
- Structured logging with JSON output
- Different levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging
- Audit trail logging

### Metrics
- Request count
- Response time
- Error rate
- Database query performance

### Health Checks
- API health endpoint
- Database connectivity
- External service (Claude) status
- System resources (memory, disk)

---

This architecture supports:
- ✅ Easy testing and maintenance
- ✅ Horizontal scaling
- ✅ Security and isolation
- ✅ Real-time updates
- ✅ Intelligent task management
- ✅ Natural language processing
