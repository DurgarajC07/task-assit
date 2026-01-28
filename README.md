# Task Assistant - Smart Multi-Agent AI Personal Assistant

A production-ready, intelligent personal task assistant powered by multi-agent AI architecture with advanced natural language understanding, context awareness, and memory. Uses free tier Grok AI (xAI) by default.

## ⭐ What Makes This Special

This isn't just a task manager - it's your **personal AI assistant** that:

🧠 **Understands Natural Language**

- "create a meeting for tomorrow at 29th jan on 2pm" → Creates task with exact date/time
- "show my tasks" → Lists your tasks with context
- "delete the meeting" → Knows which meeting from conversation
- "mark it complete" → Understands "it" from context

💬 **Remembers Everything**

- Conversation history across sessions
- Recent tasks and preferences
- Context from previous interactions
- Personal task patterns

🎯 **Smart & Contextual**

- Infers priorities from urgency ("urgent" → high priority)
- Extracts tags automatically ("client meeting" → tags: client, meeting)
- Handles complex date/time formats ("29th jan at 2pm", "tomorrow at 14:00")
- Asks clarifying questions when needed

🆓 **Free Tier AI**

- Uses Grok AI llama-3.1-8b-instant (free)
- No credits needed for basic usage
- Fast and efficient
- Easy to switch to other providers

## Features

✨ **Advanced Multi-Agent Architecture**

- **Intent Agent**: Deep understanding of user requests with reasoning
- **Task Agent**: Smart CRUD operations with validation and logging
- **Conversation Agent**: Context-aware natural responses
- **Memory Agent**: Conversation history and user context management
- **Orchestrator**: Coordinates agents with reasoning chain

🤖 **AI Integration**

- **Grok AI (xAI)**: Default free tier with llama-3.1-8b-instant
- **Multiple Providers**: Claude, OpenAI, Gemini also supported
- **Context-Aware**: Uses conversation history for better responses
- **Smart Extraction**: Entities, dates, times, priorities from natural language

📋 **Intelligent Task Management**

- Natural language task creation
- Smart date/time parsing (29th jan, tomorrow at 2pm, etc.)
- Priority inference from context
- Tag extraction from descriptions
- Full CRUD with conversation interface
- Advanced search and filtering

🔐 **Security & Privacy**

- JWT token authentication with refresh tokens
- Per-user data isolation (row-level security)
- Password hashing with bcrypt
- Secure API key management
- Complete audit trail

🔄 **Real-Time Features**

- WebSocket support for live updates
- Real-time chat interface
- Connection management with heartbeat
- Session management

📊 **Analytics & Insights**

- Task statistics and productivity metrics
- Conversation history analysis
- Audit logs for all operations
- User preferences tracking

## Technology Stack

- **Framework**: FastAPI (async-first)
- **Database**: SQLAlchemy ORM with SQLite (PostgreSQL ready)
- **AI**: Grok (xAI) - llama-3.1-8b-instant (free tier)
- **Authentication**: JWT with bcrypt
- **WebSocket**: FastAPI WebSocket
- **Validation**: Pydantic v2
- **Testing**: pytest with async support

## Quick Start

### Prerequisites

- Python 3.11+
- pip or poetry
- Grok API key (free tier) - Get from [x.ai](https://x.ai)

### Installation

1. **Clone the repository**

```bash
cd c:/laragon/www/task-assit
```

2. **Create virtual environment**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Grok AI (Free Tier)**

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your Grok API key
notepad .env
```

Set these values in `.env`:

```env
LLM_PROVIDER=grok
LLM_MODEL=llama-3.1-8b-instant
GROK_API_KEY=xai-your-key-here
```

**Get Your Free Grok API Key:**

1. Visit [console.x.ai](https://console.x.ai)
2. Sign up for free account
3. Create API key
4. Copy key starting with `xai-`

See [GROK_SETUP.md](GROK_SETUP.md) for detailed setup guide.

5. **Run the application**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
multiagent/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   │
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic validation schemas
│   ├── agents/              # Multi-agent system
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic
│   ├── core/                # Security and utilities
│   └── utils/               # Helper functions
│
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
└── README.md               # This file
```

## API Endpoints

### Authentication

```
POST   /api/auth/register      # Register new user
POST   /api/auth/login         # Login and get tokens
POST   /api/auth/refresh       # Refresh access token
POST   /api/auth/logout        # Logout user
GET    /api/auth/me            # Get current user info
```

### Tasks

```
POST   /api/tasks              # Create task
GET    /api/tasks              # List tasks (with filters)
GET    /api/tasks/{id}         # Get single task
PUT    /api/tasks/{id}         # Update task
PATCH  /api/tasks/{id}/complete  # Mark as complete
DELETE /api/tasks/{id}         # Delete task
GET    /api/tasks/search?q=    # Search tasks
GET    /api/tasks/stats        # Get statistics
```

### Chat (Natural Language)

```
POST   /api/chat               # Process NL command
GET    /api/chat/history       # Get conversation history
WS     /api/ws                 # WebSocket for real-time updates
```

### Health

```
GET    /api/health             # Health check
GET    /                       # API info
```

## Usage Examples

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password_123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password_123"
  }'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. Create Task via Natural Language

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to buy groceries tomorrow at 5pm, high priority"
  }'
```

Response:

```json
{
  "success": true,
  "message": "✓ Task 'buy groceries' created successfully!",
  "intent": "CREATE_TASK",
  "data": {
    "id": "uuid-here",
    "title": "buy groceries",
    "status": "pending",
    "priority": "high",
    ...
  }
}
```

### 4. List Tasks

```bash
curl -X GET "http://localhost:8000/api/tasks?filter_type=today" \
  -H "Authorization: Bearer {access_token}"
```

### 5. Natural Language Task Management

```bash
# "Show me my high priority tasks"
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "message": "Show me my high priority tasks"
  }'

# "Mark the grocery task as complete"
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "message": "Mark the grocery task as complete"
  }'

# "What's my completion rate this week?"
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "message": "What's my completion rate this week?"
  }'
```

## Natural Language Intents Supported

The system understands and processes:

### Task Creation

- "Add a task to buy milk tomorrow"
- "Create a meeting with John on Friday at 2pm, high priority"
- "Remind me to call mom next week"

### Task Listing

- "Show me my tasks for today"
- "What do I need to do this week?"
- "List all high priority tasks"

### Task Completion

- "Mark the grocery task as complete"
- "I finished buying groceries"
- "Complete my meeting tomorrow"

### Task Search

- "Find tasks related to work"
- "Search for meetings"
- "Show tasks tagged with personal"

### Task Updates

- "Change the grocery task to high priority"
- "Move the meeting to Thursday"
- "Update the report due date to Friday"

### Statistics

- "How many tasks do I have pending?"
- "What's my completion rate?"
- "Show me a summary of my tasks"

## Database Schema

### Users Table

- `id` (UUID, PK)
- `username` (string, unique)
- `email` (string, unique)
- `password_hash` (string)
- `preferences` (JSON)
- `created_at`, `updated_at` (timestamps)

### Tasks Table

- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `title`, `description` (strings)
- `status` (enum: pending, in_progress, completed, cancelled)
- `priority` (enum: low, medium, high, urgent)
- `due_date` (datetime, nullable)
- `tags` (JSON array)
- `completed_at`, `deleted_at` (timestamps)
- `created_at`, `updated_at` (timestamps)

### Conversation History Table

- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `session_id` (UUID)
- `role` (enum: user, assistant)
- `message` (text)
- `intent`, `entities` (string, JSON)
- `created_at` (timestamp)

### Task Audit Log Table

- `id` (UUID, PK)
- `task_id` (UUID, FK)
- `user_id` (UUID, FK)
- `action` (enum: created, updated, completed, deleted)
- `old_values`, `new_values` (JSON)
- `created_at` (timestamp)

### User Sessions Table

- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `session_token` (string, unique)
- `expires_at`, `created_at` (timestamps)

## Authentication Flow

1. **Register**: Create new user account
2. **Login**: Get access token (15 min) and refresh token (7 days)
3. **Access API**: Include access token in Authorization header
4. **Refresh**: Use refresh token to get new access token when expired
5. **Logout**: Invalidate refresh token

## Configuration

Edit `.env` to configure:

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./task_assistant.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Claude API
ANTHROPIC_API_KEY=your-api-key-here

# Application
APP_NAME=Task Assistant
DEBUG=false
ALLOWED_ORIGINS=http://localhost:3000

# WebSocket
WS_HEARTBEAT_INTERVAL=30
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_agents/test_task_agent.py

# Async tests
pytest -v tests/test_agents/
```

### Test Coverage

```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Performance Considerations

- **Database Indexes**: Optimized for common queries (user_id, status, due_date, priority)
- **Async Operations**: All I/O is async for concurrency
- **Connection Pooling**: SQLAlchemy handles automatic pooling
- **Soft Deletes**: Preserves data integrity
- **Pagination**: Implement for large result sets
- **Query Optimization**: Avoid N+1 queries

## Security Best Practices

✅ **Implemented**:

- JWT token-based auth with refresh rotation
- Bcrypt password hashing (12 rounds)
- User data isolation at all levels
- SQL injection protection (SQLAlchemy)
- CORS configuration
- Input validation with Pydantic
- Row-level security checks

✅ **Recommendations**:

- Use HTTPS in production
- Set strong SECRET_KEY
- Rotate API keys regularly
- Monitor for suspicious activity
- Implement rate limiting
- Add logging and auditing

## Deployment

### Docker

```dockerfile
# Dockerfile (example)
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_ORIGINS` properly
- [ ] Set up HTTPS/SSL
- [ ] Use PostgreSQL for production
- [ ] Enable query logging
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Set up CI/CD pipeline

## Future Enhancements

🚀 **Planned Features**:

- Notification system (email, SMS, push)
- Task collaboration and sharing
- Task templates and recurring tasks
- AI-powered task prioritization
- Integration with calendar services
- Mobile app support
- Advanced analytics and dashboards
- Team management and permissions
- Custom AI models training
- Task automation workflows

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:

- Open an issue on GitHub
- Check documentation at `/docs`
- Review API errors for guidance

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- AI powered by [Anthropic Claude](https://claude.ai/)
- Database with [SQLAlchemy](https://www.sqlalchemy.org/)

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✓
