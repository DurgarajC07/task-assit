# 🚀 Quick Start Guide - Your Smart Personal Task Assistant

## What You Have Now

A fully functional, intelligent personal task assistant that:

- ✅ Understands natural language: "create a meeting for tomorrow at 29th jan on 2pm"
- ✅ Remembers conversations and context
- ✅ Manages tasks smartly (create, update, delete, complete)
- ✅ Uses FREE Grok AI (llama-3.1-8b-instant)
- ✅ Handles complex date/time formats
- ✅ Maintains conversation history
- ✅ Works with per-user data isolation

## Setup in 3 Steps

### Step 1: Get Your FREE Grok API Key (2 minutes)

1. Visit: https://console.x.ai
2. Sign up (free account)
3. Create API Key
4. Copy key (starts with `xai-`)

### Step 2: Configure (1 minute)

Edit your `.env` file:

```env
LLM_PROVIDER=grok
LLM_MODEL=llama-3.1-8b-instant
GROK_API_KEY=xai-your-key-here

# Database
DATABASE_URL=sqlite+aiosqlite:///./task_assistant.db

# Security (change in production)
SECRET_KEY=your-secret-key-change-this-in-production
```

### Step 3: Start (30 seconds)

```bash
# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Start the server
uvicorn app.main:app --reload
```

**That's it!** 🎉 Your AI assistant is running at http://localhost:8000

## First Use - Try These Examples

### 1. Open API Documentation

Visit: http://localhost:8000/docs

### 2. Register Your Account

**POST** `/api/auth/register`

```json
{
  "username": "myusername",
  "email": "my@email.com",
  "password": "mysecurepass123"
}
```

### 3. Login

**POST** `/api/auth/login`

```json
{
  "username": "myusername",
  "password": "mysecurepass123"
}
```

Copy the `access_token` from response!

### 4. Chat with Your AI Assistant

**POST** `/api/chat`
Headers: `Authorization: Bearer YOUR_TOKEN`

```json
{
  "message": "create a meeting for tomorrow at 29th jan on 2pm"
}
```

**Response:**

```json
{
  "success": true,
  "message": "I've created your 'meeting' task for January 29th at 2:00 PM!",
  "data": {
    "id": "...",
    "title": "meeting",
    "due_date": "2026-01-29T14:00:00",
    "priority": "medium",
    "status": "pending"
  }
}
```

## Real-World Usage Examples

### Creating Tasks

```
✅ "create a meeting for tomorrow at 29th jan on 2pm"
   → Creates task: "meeting" due Jan 29, 2026 at 14:00

✅ "remind me to buy milk tomorrow"
   → Creates task: "buy milk" due tomorrow

✅ "add urgent task to finish project by friday 5pm"
   → Creates: "finish project" (urgent) due Friday at 17:00

✅ "add task call mom next monday at 3:30pm"
   → Creates: "call mom" due next Monday at 15:30
```

### Viewing Tasks

```
✅ "show my tasks"
   → Lists all your active tasks

✅ "what do I have today?"
   → Shows tasks due today

✅ "show high priority tasks"
   → Filters by priority

✅ "what's due this week?"
   → Shows weekly tasks
```

### Managing Tasks

```
✅ "mark the meeting as complete"
   → Marks meeting task as done

✅ "delete the milk task"
   → Removes the task

✅ "change meeting to 3pm"
   → Updates meeting time to 15:00

✅ "make project task urgent"
   → Updates priority to urgent
```

### Getting Insights

```
✅ "how many tasks do I have?"
   → Shows task count and stats

✅ "show my completed tasks"
   → Lists finished tasks

✅ "what's my productivity?"
   → Shows completion rates
```

## Supported Date/Time Formats

### Dates

- **Relative**: tomorrow, today, yesterday, next week, in 3 days
- **Days**: monday, tuesday, friday, next monday
- **Specific**: 29th jan, january 29, jan 29th, 29th january
- **Full dates**: 29/01/2026, 2026-01-29

### Times

- **12-hour**: 2pm, 2:30pm, 2 pm, at 2pm
- **24-hour**: 14:00, 14:30, 15:45

### Combined

- "tomorrow at 2pm"
- "29th jan at 14:00"
- "next monday at 3:30pm"
- "january 29 at 2 pm"

## Your AI Assistant Features

### 🧠 Smart Understanding

- Extracts task title automatically
- Infers priority from urgency words ("urgent" → high priority)
- Generates tags from context ("client meeting" → tags: client, meeting)
- Understands references ("it", "that", "the meeting")

### 💬 Conversational Memory

- Remembers recent conversations
- Knows your recent tasks
- Context-aware responses
- Natural follow-up questions

### 🎯 Intelligent Actions

- Creates tasks with all details
- Updates specific fields
- Smart search and filtering
- Task statistics

### 🔒 Secure & Private

- Per-user data isolation
- JWT authentication
- Encrypted passwords
- Complete audit trail

## Troubleshooting

### "GROK_API_KEY not set"

**Solution**: Add your Grok API key to `.env` file and restart server

### Date not parsing correctly

**Be specific**:

- ✅ "tomorrow at 2pm"
- ✅ "29th jan at 14:00"
- ❌ "sometime tomorrow"

### Task not found

**Use clear names**:

- ✅ "delete the meeting task"
- ✅ "mark meeting as complete"
- ❌ "delete it" (without context)

## Advanced Usage

### Using the Web UI (if available)

Open `app/static/index.html` in browser after starting server:

```
http://localhost:8000/static/index.html
```

### WebSocket for Real-Time Updates

Connect to: `ws://localhost:8000/api/ws`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## File Structure

```
task-assit/
├── app/
│   ├── agents/          ← Multi-agent AI system
│   ├── api/             ← REST API endpoints
│   ├── llm/             ← Grok AI provider
│   ├── models/          ← Database models
│   ├── services/        ← Business logic
│   └── utils/           ← Date parser, validators
│
├── .env                 ← Your configuration
├── requirements.txt     ← Dependencies
└── README.md           ← Full documentation
```

## Production Deployment

When ready for production:

1. **Update `.env`**:

   ```env
   DEBUG=false
   SECRET_KEY=generate-strong-random-key
   DATABASE_URL=postgresql://user:pass@host/db
   ```

2. **Use PostgreSQL** instead of SQLite

3. **Set up HTTPS** with nginx/Apache

4. **Configure rate limiting**

5. **Set up monitoring** and logging

See `DEPLOYMENT.md` for detailed guide.

## Next Steps

1. ✅ **Test the system** with various commands
2. ✅ **Explore the API** at http://localhost:8000/docs
3. ✅ **Read documentation**: `ARCHITECTURE.md`, `GROK_SETUP.md`
4. ✅ **Customize** for your needs
5. ✅ **Scale** as needed

## Support & Documentation

- **Full Documentation**: See `README.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Grok Setup**: See `GROK_SETUP.md`
- **API Guide**: http://localhost:8000/docs
- **Enhancement Details**: See `SYSTEM_ENHANCEMENT.md`

## Your System is Ready! 🎉

Start using your smart personal AI assistant today. It will:

- Remember your tasks and conversations
- Understand natural language
- Help you stay organized
- Learn from your usage patterns
- Keep your data secure and private

**Happy Task Managing!** 🚀

---

Need help? Check the documentation files or visit http://localhost:8000/docs for API reference.
