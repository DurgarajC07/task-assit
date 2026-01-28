# Grok AI Setup Guide

This guide will help you set up your Task Assistant to use Grok AI (xAI) with the free tier model.

## Why Grok?

- **Free Tier Available**: Use `llama-3.1-8b-instant` model for free
- **Fast Responses**: Optimized for quick inference
- **Good Performance**: Excellent for task management and natural language understanding
- **Easy Setup**: Simple API key configuration

## Step 1: Get Your Grok API Key

1. Visit [x.ai](https://x.ai/) or [console.x.ai](https://console.x.ai/)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy your API key (starts with `xai-...`)

## Step 2: Configure Your Environment

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file:**

   ```bash
   # Open in your favorite editor
   nano .env
   # or
   code .env
   ```

3. **Update the following values:**

   ```env
   # Set Grok as your provider
   LLM_PROVIDER=grok

   # Use the free tier model
   LLM_MODEL=llama-3.1-8b-instant

   # Add your Grok API key
   GROK_API_KEY=xai-your-actual-key-here
   ```

4. **Save the file**

## Step 3: Verify Setup

1. **Check your configuration:**

   ```bash
   python -c "from app.config import settings; print(f'Provider: {settings.llm_provider}, Model: {settings.llm_model}')"
   ```

2. **Start the application:**

   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test with a simple request:**

   ```bash
   # Register a user (if not already)
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

   # Login to get token
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"testpass123"}'

   # Test task creation
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -d '{"message":"create a meeting for tomorrow at 2pm"}'
   ```

## Supported Models

### Free Tier (Recommended)

- **llama-3.1-8b-instant**: Fast, efficient, perfect for task management

### Paid Tier (If you upgrade)

- **grok-2-latest**: Most powerful Grok model
- **grok-vision**: For multimodal tasks

## Features Enabled with Grok

✅ **Natural Language Understanding**

- "create a meeting for tomorrow at 29th jan on 2pm"
- "show me my tasks for today"
- "delete the meeting task"
- "mark the project task as complete"

✅ **Date and Time Parsing**

- Relative dates: "tomorrow", "next week"
- Specific dates: "29th jan", "january 29"
- Time formats: "2pm", "14:00", "at 2:30pm"

✅ **Smart Task Management**

- Priority detection from urgency
- Tag extraction from context
- Task search and filtering
- Statistics and summaries

✅ **Conversation Memory**

- Remembers recent interactions
- Contextual responses
- User preference tracking
- Session management

## Troubleshooting

### Error: "GROK_API_KEY environment variable is not set"

**Solution**: Make sure you've added your API key to the `.env` file and restarted the application.

### Error: "openai package not installed"

**Solution**: Install the required package:

```bash
pip install openai
```

### Error: Rate limit exceeded

**Solution**: Free tier has rate limits. Wait a moment and try again, or upgrade your Grok account.

### Tasks not creating with correct dates

**Solution**: Be specific with dates. Examples:

- ✅ "create meeting for 29th january at 2pm"
- ✅ "add task for tomorrow at 14:00"
- ❌ "create meeting" (no date/time)

## Example Usage

### Creating Tasks

```
User: "create a meeting for tomorrow at 29th jan on 2pm"
AI: "I've created your 'meeting' task scheduled for January 29th at 2:00 PM!"

User: "remind me to buy milk tomorrow"
AI: "Got it! I've added 'buy milk' to your tasks for tomorrow."

User: "add urgent task to finish project proposal by friday 5pm"
AI: "I've created an urgent task 'finish project proposal' due Friday at 5:00 PM."
```

### Viewing Tasks

```
User: "show me my tasks"
AI: "Here are your tasks:
• Meeting - Jan 29 at 2:00 PM (Medium)
• Buy milk - Jan 28 (Medium)
• Finish project proposal - Feb 2 at 5:00 PM (Urgent)"

User: "what do I have today?"
AI: "You have 1 task for today:
• Buy milk (Medium priority)"
```

### Managing Tasks

```
User: "mark the meeting as complete"
AI: "Great job! I've marked 'meeting' as complete ✓"

User: "delete the milk task"
AI: "I've deleted the 'buy milk' task for you."

User: "change the meeting to 3pm"
AI: "I've updated your meeting to 3:00 PM."
```

## Advanced Configuration

### Adjusting Model Parameters

You can customize the model behavior by modifying `app/llm/grok_provider.py`:

```python
# For more creative responses
temperature=0.7  # Default for conversations

# For more consistent classification
temperature=0.3  # Used for intent classification

# For longer responses
max_tokens=2048  # Increase if needed
```

### Switching Models

To use a different Grok model (requires appropriate API access):

```env
# In .env file
LLM_MODEL=grok-2-latest
```

## Performance Tips

1. **Be specific with dates and times** - This helps the AI understand exactly what you want
2. **Use natural language** - The system is designed to understand conversational requests
3. **Reference tasks clearly** - Use distinctive task names when updating/deleting
4. **Check task list regularly** - Use "show my tasks" to see what's scheduled

## Support

If you encounter issues:

1. Check the logs: `tail -f logs/app.log`
2. Verify your API key is valid
3. Ensure you have internet connectivity
4. Check Grok API status: [status.x.ai](https://status.x.ai)

## Next Steps

- Explore the [API Documentation](http://localhost:8000/docs)
- Read the [Architecture Guide](ARCHITECTURE.md)
- Try the [UI Guide](UI_GUIDE.md)
- Set up [Deployment](DEPLOYMENT.md)

---

**Note**: The free tier model `llama-3.1-8b-instant` is perfect for personal task management. If you need more advanced features or higher rate limits, consider upgrading to a paid tier.
