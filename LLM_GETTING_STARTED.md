# Multi-LLM Configuration - Getting Started

## 🚀 Quick Start (Choose ONE)

### ⭐ FREE Option (Recommended for testing)

```bash
# 1. Get free Gemini API key (2 minutes)
# Visit: https://makersuite.google.com/app/apikey
# Click "Create API Key" → "Create API key in new project"
# Copy the key

# 2. Update .env
nano .env
# Change to:
#   LLM_PROVIDER=gemini
#   GEMINI_API_KEY=AIzaSy_paste_your_key_here

# 3. Start!
./start.sh --seed
```

**Why Gemini?** Free tier, good accuracy, perfect for personal use!

---

### 💎 Best Quality (Claude)

```bash
# 1. Get Claude API key from: https://console.anthropic.com
# 2. Update .env:
#   LLM_PROVIDER=claude
#   ANTHROPIC_API_KEY=sk-ant-your_key_here
# 3. Start: ./start.sh --seed
```

**Cost:** ~$3-15/month | **Quality:** Best in class

---

### 🤖 OpenAI Option

```bash
# 1. Get key from: https://platform.openai.com
# 2. Update .env:
#   LLM_PROVIDER=openai
#   OPENAI_API_KEY=sk-your_key_here
# 3. Start: ./start.sh --seed

# Tip: Edit app/llm/openai_provider.py line 16 to use cheaper model:
#   self.model = "gpt-3.5-turbo"
```

**Cost:** ~$1-20/month | **Quality:** Very good

---

### ⚡ New: Grok Option

```bash
# 1. Get key from: https://console.x.ai
# 2. Update .env:
#   LLM_PROVIDER=grok
#   GROK_API_KEY=your_key_here
# 3. Start: ./start.sh --seed
```

**Cost:** Paid | **Quality:** Latest AI model

---

## 📖 Detailed Guides

- **[LLM_QUICK_START.md](LLM_QUICK_START.md)** - Setup examples for each provider
- **[LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md)** - Complete detailed setup guide
- **[LLM_IMPLEMENTATION_SUMMARY.md](LLM_IMPLEMENTATION_SUMMARY.md)** - Technical overview

---

## 🔧 Automated Setup

```bash
./setup_llm.sh
```

This interactive script will:
1. Show you all provider options
2. Ask which one you want
3. Guide you through getting an API key
4. Configure `.env` automatically

---

## 🔄 Switching Providers

Want to try a different provider?

```bash
# 1. Edit .env
nano .env

# 2. Change provider and API key
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_new_key

# 3. Restart app (Ctrl+C, then:)
./start.sh --seed

# Done! No code changes needed ✓
```

---

## 📊 Quick Comparison

| | Claude | OpenAI | Gemini | Grok |
|---|--------|--------|--------|------|
| **Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Speed** | Fast | Medium | Fast | Fast |
| **Cost** | Paid | Paid | **FREE** ✓ | Paid |
| **Setup** | Easy | Easy | **EASIEST** | Easy |
| **Best For** | Production | Flexibility | Personal use | Latest tech |

---

## ✅ Verification

After setup, verify it's working:

```bash
# 1. Open browser
# http://localhost:8000/docs

# 2. Register and login

# 3. Test POST /api/chat:
{
  "message": "Create a task to organize my desk"
}

# You should see the AI respond! ✓
```

---

## ❓ Help

### "API key not set" error

Add the key to `.env`:
```bash
nano .env
# Make sure you have:
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=AIzaSy_your_actual_key
```

### Slow responses?

- If Gemini: Wait a minute (free tier rate limit)
- Otherwise: Upgrade to paid provider or use GPT-3.5-turbo

### Can't import module?

```bash
pip install -r requirements.txt
```

---

## 🎯 Recommended Setup by Use Case

**Just Testing?**
```
→ Use Gemini (FREE)
```

**Production Application?**
```
→ Use Claude (most reliable)
```

**Budget-Conscious?**
```
→ Use Gemini free tier
→ Switch to OpenAI GPT-3.5 if needed
```

**Want Latest Features?**
```
→ Use Grok
```

---

## 📝 .env Reference

Your `.env` file should look like:

```bash
# Pick ONE provider
LLM_PROVIDER=claude    # or: openai, gemini, grok

# Add ONLY the API key for your chosen provider
ANTHROPIC_API_KEY=sk-ant-...          # For Claude
OPENAI_API_KEY=sk-...                 # For OpenAI
GEMINI_API_KEY=AIzaSy-...            # For Gemini
GROK_API_KEY=...                     # For Grok

# Other settings (already configured)
DATABASE_URL=sqlite+aiosqlite:///./task_assistant.db
SECRET_KEY=your-secret-key-here
DEBUG=true
```

---

## 🎉 You're Ready!

Pick your LLM provider and get started:

1. Choose from: Gemini (free), Claude, OpenAI, or Grok
2. Get API key for your choice
3. Update `.env`
4. Run `./start.sh --seed`
5. Visit http://localhost:8000/docs
6. Start creating tasks with AI! 🚀

**Questions?** Check the [LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md) for detailed information.
