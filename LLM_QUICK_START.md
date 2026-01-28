# Quick LLM Setup Examples

## Using Claude (Default)

```bash
# Update .env
nano .env

# Add:
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

Then start:
```bash
./start.sh --seed
```

---

## Using Gemini (FREE) ⭐

**This is the recommended free option!**

### Get Free API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click **"Create API Key"**
3. Select **"Create API key in new project"**
4. Copy the key

### Configure

```bash
# Update .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_key_here

# Or use the setup script
./setup_llm.sh
```

### Start

```bash
./start.sh --seed
```

---

## Using OpenAI

```bash
# Update .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here

# Or use the setup script
./setup_llm.sh
```

Tip: Change the model to GPT-3.5 for lower costs:
- Edit `app/llm/openai_provider.py`
- Line 16: `self.model = "gpt-3.5-turbo"`

---

## Using Grok

```bash
# Update .env
LLM_PROVIDER=grok
GROK_API_KEY=your_key_here

# Or use the setup script
./setup_llm.sh
```

---

## Switching Providers

To switch between providers after setup:

```bash
# Edit .env
nano .env

# Change LLM_PROVIDER and the corresponding API key

# Restart the app
# Press Ctrl+C to stop current instance
./start.sh --seed
```

**No code changes needed!** The system auto-loads the new provider.

---

## Testing Your LLM

Once running, test via API docs:

1. Visit: http://localhost:8000/docs
2. Go to **POST /api/chat**
3. Click **"Try it out"**
4. Send a message:
   ```json
   {
     "message": "Create a task to learn Python"
   }
   ```
5. See the LLM response!

---

## Troubleshooting

### "API key not set"

Make sure you:
1. Added the API key to `.env`
2. Set the correct `LLM_PROVIDER`
3. Restarted the app

### "ImportError: cannot import name..."

Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Slow responses

- If using Gemini free tier: Wait a minute (rate limited)
- Switch to paid provider for unlimited speed
- Or use GPT-3.5-turbo if using OpenAI

---

## Recommended Setups

### Budget-Conscious 💰
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_free_key
```
- Free tier
- Good accuracy
- Rate limited (OK for personal use)

### Professional Quality 🎯
```bash
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your_key
```
- Most accurate
- Reliable JSON parsing
- ~$3-15/month

### Cost-Effective OpenAI 💵
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key
# Use GPT-3.5-turbo (cheaper than GPT-4)
```
- Good balance of cost and quality
- ~$1-5/month

---

## Detailed Guide

See [LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md) for:
- Complete setup instructions for each provider
- Provider comparison
- Docker configuration
- Custom provider setup
- Troubleshooting guide
