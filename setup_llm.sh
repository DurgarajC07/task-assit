#!/bin/bash
# Multi-LLM Configuration Helper Script
# This script helps you set up and switch between different LLM providers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Task Assistant - LLM Provider Configuration          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo -e "${YELLOW}\nAvailable LLM Providers:${NC}"
echo "1. Claude (Anthropic) - Most accurate, paid API"
echo "2. OpenAI - GPT-4/GPT-3.5, paid API"
echo "3. Gemini (Google) - FREE tier available ⭐"
echo "4. Grok (xAI) - Latest model, paid API"
echo ""

read -p "Choose provider (1-4): " choice

case $choice in
    1)
        provider="claude"
        echo -e "${YELLOW}\n📝 Claude Setup:${NC}"
        echo "1. Visit: https://console.anthropic.com"
        echo "2. Create an API key"
        read -p "Paste your ANTHROPIC_API_KEY: " api_key
        sed -i "s/^LLM_PROVIDER=.*/LLM_PROVIDER=claude/" .env
        sed -i "s/^ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" .env
        ;;
    2)
        provider="openai"
        echo -e "${YELLOW}\n📝 OpenAI Setup:${NC}"
        echo "1. Visit: https://platform.openai.com"
        echo "2. Create an API key"
        read -p "Paste your OPENAI_API_KEY: " api_key
        sed -i "s/^LLM_PROVIDER=.*/LLM_PROVIDER=openai/" .env
        sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
        ;;
    3)
        provider="gemini"
        echo -e "${YELLOW}\n📝 Gemini Setup (FREE):${NC}"
        echo "1. Visit: https://makersuite.google.com/app/apikey"
        echo "2. Click 'Create API Key'"
        echo "3. Choose 'Create API key in new project'"
        read -p "Paste your GEMINI_API_KEY: " api_key
        sed -i "s/^LLM_PROVIDER=.*/LLM_PROVIDER=gemini/" .env
        sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$api_key/" .env
        ;;
    4)
        provider="grok"
        echo -e "${YELLOW}\n📝 Grok Setup:${NC}"
        echo "1. Visit: https://console.x.ai"
        echo "2. Create an API key"
        read -p "Paste your GROK_API_KEY: " api_key
        sed -i "s/^LLM_PROVIDER=.*/LLM_PROVIDER=grok/" .env
        sed -i "s/^GROK_API_KEY=.*/GROK_API_KEY=$api_key/" .env
        ;;
    *)
        echo -e "${RED}Invalid choice!${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}\n✅ Configuration saved!${NC}"
echo -e "${BLUE}Current Settings:${NC}"
grep "^LLM_PROVIDER=" .env
grep "^.*_API_KEY=" .env | grep -v "your-api-key"

echo -e "${YELLOW}\nNext steps:${NC}"
echo "1. Run: ./start.sh --seed"
echo "2. Visit: http://localhost:8000/docs"
echo "3. Test the API with your new LLM provider"

echo -e "${BLUE}\nFor more information, see: LLM_SETUP_GUIDE.md${NC}"
