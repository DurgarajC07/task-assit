# Multi-LLM Provider Guide

Welcome! Your Task Assistant now supports **4 different LLM providers**. Choose which AI to use based on your needs.

## 🎯 Start Here

### 1️⃣ Choose Your Provider

| Option | Best For | Cost | Setup |
|--------|----------|------|-------|
| **Gemini** (FREE) ⭐ | Testing, personal use | $0 | 2 min |
| **Claude** | Best accuracy | ~$5/mo | 5 min |
| **OpenAI** | Flexibility | ~$1-20/mo | 5 min |
| **Grok** | Latest AI | Paid | 5 min |

### 2️⃣ Quick Setup (Pick one)

**EASIEST - Using Gemini (FREE):**
```bash
./setup_llm.sh
# Choose: 3 (Gemini)
# Visit: https://makersuite.google.com/app/apikey
# Paste key when prompted
```

**MANUAL - Edit .env:**
```bash
nano .env
# Add:
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy_your_key_here
```

### 3️⃣ Start Application
```bash
./start.sh --seed
# Visit: http://localhost:8000/docs
```

## 📚 Documentation

- **[LLM_GETTING_STARTED.md](LLM_GETTING_STARTED.md)** ← Start here (10 min read)
- **[LLM_QUICK_START.md](LLM_QUICK_START.md)** - Setup examples
- **[LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md)** - Detailed guide
- **[LLM_IMPLEMENTATION_SUMMARY.md](LLM_IMPLEMENTATION_SUMMARY.md)** - Technical details
- **[LLM_CHANGES.txt](LLM_CHANGES.txt)** - What changed

## ⚡ Switch Providers Anytime

No code changes needed!

```bash
# 1. Stop app (Ctrl+C)
# 2. Edit .env - change provider and API key
nano .env
# 3. Restart
./start.sh --seed
# Done!
```

## ❓ Quick Help

**No API key?** → Use Gemini free tier!

**Slow?** → Gemini free tier has rate limits, use paid option

**Can't import?** → Run: `pip install -r requirements.txt`

## 🏃 TL;DR - 3 Steps

1. **Choose:** Gemini (free), Claude, OpenAI, or Grok
2. **Get Key:** Visit provider's console (2-5 min)
3. **Setup:** Edit `.env` or run `./setup_llm.sh`
4. **Go:** `./start.sh --seed`

That's it! 🚀
