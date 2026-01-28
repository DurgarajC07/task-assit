# LLM Provider Configuration Guide

This guide explains how to configure and use different LLM providers with the Task Assistant.

## Supported Providers

The system supports 4 LLM providers:
- **Claude** (Anthropic) - Most accurate, requires paid API
- **OpenAI** - GPT-4/GPT-3.5, requires paid API
- **Gemini** (Google) - Free tier available
- **Grok** (xAI) - New option, requires API key

## Quick Start

### 1. Choose Your Provider

Set `LLM_PROVIDER` in `.env`:

```bash
# Use Claude (default)
LLM_PROVIDER=claude

# Or use OpenAI
LLM_PROVIDER=openai

# Or use Gemini (free)
LLM_PROVIDER=gemini

# Or use Grok
LLM_PROVIDER=grok
```

### 2. Add API Key

Add the corresponding API key to `.env`:

```bash
# For Claude
ANTHROPIC_API_KEY=sk-ant-...

# For OpenAI
OPENAI_API_KEY=sk-...

# For Gemini
GEMINI_API_KEY=AIzaSy...

# For Grok
GROK_API_KEY=...
```

### 3. Start the Application

```bash
./start.sh --seed
```

The application will automatically use your selected provider.

---

## Provider Details & Setup

### Claude (Anthropic)

**Best for:** Highest accuracy and reliability

**Pricing:** Paid API (about $3-15/month for most users)

**Model:** Claude 3.5 Sonnet (latest)

**Setup Steps:**

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Sign up and create an API key
3. Add to `.env`:
   ```
   LLM_PROVIDER=claude
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

**Pros:**
- Most accurate for intent classification
- Best conversation quality
- Reliable JSON parsing

**Cons:**
- Paid API only

---

### OpenAI

**Best for:** Flexibility and large feature set

**Pricing:** Paid API (GPT-4 is more expensive, GPT-3.5 is cheaper)

**Model:** GPT-4 Turbo (configurable to GPT-3.5-turbo for cost savings)

**Setup Steps:**

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Create account and add payment method
3. Generate API key
4. Add to `.env`:
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   ```

**Pros:**
- Widely used and reliable
- Good accuracy
- Can use cheaper GPT-3.5-turbo

**Cons:**
- Paid only
- GPT-4 can be expensive

**Cost Optimization:**
- Edit [openai_provider.py](../app/llm/openai_provider.py) line 17:
  ```python
  self.model = "gpt-3.5-turbo"  # Instead of gpt-4-turbo
  ```

---

### Gemini (Google)

**Best for:** Free option with good performance

**Pricing:** Free tier available! (limited requests, but enough for personal use)

**Model:** Gemini Pro (free) or Gemini Pro Vision

**Setup Steps:**

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Choose "Create API key in new project"
4. Copy the key
5. Add to `.env`:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSy_your_key_here
   ```

**Pros:**
- **FREE tier available** ✓
- Good accuracy
- Easy setup
- Perfect for personal use

**Cons:**
- Rate limited on free tier
- Less mature than Claude/OpenAI
- Response quality slightly lower

**Free Tier Limits:**
- 60 requests per minute
- 1000 requests per day
- Sufficient for personal task management

**Install Dependencies:**
```bash
pip install google-generativeai
```

---

### Grok (xAI)

**Best for:** Cutting-edge AI with real-time information

**Pricing:** Paid API

**Model:** Grok 2 Latest

**Setup Steps:**

1. Go to [X AI Platform](https://console.x.ai)
2. Create account and API key
3. Add to `.env`:
   ```
   LLM_PROVIDER=grok
   GROK_API_KEY=your-key-here
   ```

**Pros:**
- Real-time information access
- Latest AI model
- Good reasoning

**Cons:**
- Paid only
- Newer service, less tested

**Install Dependencies:**
```bash
pip install openai  # Grok uses OpenAI-compatible API
```

---

## Switching Providers

To switch LLM providers:

1. **Update `.env`:**
   ```bash
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-key
   ```

2. **Restart application:**
   ```bash
   # Stop current server (Ctrl+C)
   ./start.sh --seed
   ```

**No code changes needed!** The system automatically loads the new provider.

---

## Environment Variables Reference

```bash
# Active provider (required)
LLM_PROVIDER=claude|openai|gemini|grok

# API Keys (only set the key for your chosen provider)
ANTHROPIC_API_KEY=sk-ant-...      # For Claude
OPENAI_API_KEY=sk-...              # For OpenAI
GEMINI_API_KEY=AIzaSy-...         # For Gemini
GROK_API_KEY=...                  # For Grok
```

---

## Troubleshooting

### "API key not set" Error

**Cause:** You selected a provider but didn't add the API key

**Solution:** Add the correct API key for your provider to `.env`

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_actual_key_here  # ← Don't forget this!
```

### Provider not found Error

**Cause:** Typo in `LLM_PROVIDER` value

**Solution:** Check spelling (must be exactly: `claude`, `openai`, `gemini`, or `grok`)

### ImportError for provider package

**Cause:** Package not installed

**Solution:** Install required packages:
```bash
pip install -r requirements.txt
```

Or install specific package:
```bash
pip install google-generativeai  # For Gemini
pip install openai               # For OpenAI/Grok
pip install anthropic            # For Claude
```

### Slow responses

**Cause:** Rate limiting or free tier limits

**Solution:**
- If using Gemini free tier: wait a minute, then retry
- Switch to a paid provider for unlimited speed
- If using OpenAI: switch to GPT-3.5-turbo to reduce latency

---

## Provider Comparison

| Feature | Claude | OpenAI | Gemini | Grok |
|---------|--------|--------|--------|------|
| Free Tier | ❌ No | ❌ No | ✅ Yes | ❌ No |
| Intent Classification | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Conversation Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| JSON Parsing | ✅ Excellent | ✅ Good | ⚠️ Fair | ✅ Good |
| Startup Cost | $0 | $5 trial | $0 | $0 |
| **Recommendation** | Best | Flexible | **Best Free** | Newest |

---

## Using with Docker

When using Docker, pass LLM configuration via environment:

**Option 1: Update .env before building**
```bash
nano .env
# Update LLM_PROVIDER and API keys
docker-compose up
```

**Option 2: Pass via docker-compose.yml**
```yaml
services:
  api:
    environment:
      - LLM_PROVIDER=gemini
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

**Option 3: Pass via command line**
```bash
LLM_PROVIDER=gemini GEMINI_API_KEY=your_key docker-compose up
```

---

## Advanced: Custom Provider

To add a custom LLM provider:

1. Create `app/llm/custom_provider.py`:
   ```python
   from .base import BaseLLMProvider
   
   class CustomProvider(BaseLLMProvider):
       async def classify_intent(self, user_message: str, system_prompt: str) -> dict:
           # Your implementation
           pass
       
       async def generate_response(self, user_message: str, system_prompt: str, context=None) -> str:
           # Your implementation
           pass
       
       async def refine_intent(self, user_message: str, system_prompt: str) -> dict:
           # Your implementation
           pass
   ```

2. Update `app/llm/factory.py` to include your provider

3. Use `LLM_PROVIDER=custom` in `.env`

---

## Support

- **Claude Issues:** [Anthropic Docs](https://docs.anthropic.com)
- **OpenAI Issues:** [OpenAI Docs](https://platform.openai.com/docs)
- **Gemini Issues:** [Google AI Docs](https://ai.google.dev)
- **Grok Issues:** [X AI Docs](https://console.x.ai/docs)

