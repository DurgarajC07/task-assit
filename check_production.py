#!/usr/bin/env python3
"""
Production Environment Checker
Verifies all production requirements before deployment
"""
import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("Checking .env file...")
    env_path = Path(".env")
    
    if not env_path.exists():
        print("  ❌ .env file not found!")
        print("  ℹ️  Copy .env.example to .env and fill in your values")
        return False
    
    required_vars = [
        "SECRET_KEY",
        "LLM_PROVIDER",
        "GROK_API_KEY",
    ]
    
    with open(env_path) as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if f"{var}=" not in content:
            missing.append(var)
    
    if missing:
        print(f"  ❌ Missing required variables: {', '.join(missing)}")
        return False
    
    # Check for default insecure values
    if "CHANGE-THIS" in content or "your-secret-key" in content:
        print("  ⚠️  Warning: SECRET_KEY still has default value!")
        print("  ℹ️  Generate a secure key: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        return False
    
    print("  ✅ .env file looks good!")
    return True

def check_gitignore():
    """Check if sensitive files are in .gitignore"""
    print("\nChecking .gitignore...")
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        print("  ❌ .gitignore not found!")
        return False
    
    with open(gitignore_path) as f:
        content = f.read()
    
    required_entries = [".env", "*.db", "__pycache__"]
    missing = [entry for entry in required_entries if entry not in content]
    
    if missing:
        print(f"  ❌ Missing entries: {', '.join(missing)}")
        return False
    
    print("  ✅ .gitignore configured correctly!")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\nChecking dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        print("  ✅ Core dependencies installed!")
        return True
    except ImportError as e:
        print(f"  ❌ Missing dependency: {e.name}")
        print("  ℹ️  Run: pip install -r requirements.txt")
        return False

def check_database():
    """Check if database can be initialized"""
    print("\nChecking database...")
    try:
        from app.database import init_db, close_db
        import asyncio
        
        async def test_db():
            await init_db()
            await close_db()
        
        asyncio.run(test_db())
        print("  ✅ Database initialization works!")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def check_deployment_files():
    """Check if deployment files exist"""
    print("\nChecking deployment files...")
    files = {
        "render.yaml": "Render configuration",
        "Procfile": "Process file",
        "Dockerfile": "Docker configuration",
        "requirements.txt": "Python dependencies"
    }
    
    all_good = True
    for file, desc in files.items():
        if Path(file).exists():
            print(f"  ✅ {file} - {desc}")
        else:
            print(f"  ❌ {file} missing - {desc}")
            all_good = False
    
    return all_good

def check_api_keys():
    """Check if API keys are configured"""
    print("\nChecking API keys...")
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_provider = os.getenv("LLM_PROVIDER", "")
    
    if llm_provider == "grok":
        key = os.getenv("GROK_API_KEY", "")
        if key and key != "test-key":
            print(f"  ✅ Groq API key configured")
            return True
        else:
            print(f"  ❌ Groq API key not configured")
            return False
    elif llm_provider == "claude":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if key and key != "test-key":
            print(f"  ✅ Anthropic API key configured")
            return True
        else:
            print(f"  ❌ Anthropic API key not configured")
            return False
    elif llm_provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "")
        if key and key != "test-key":
            print(f"  ✅ OpenAI API key configured")
            return True
        else:
            print(f"  ❌ OpenAI API key not configured")
            return False
    else:
        print(f"  ⚠️  Unknown LLM provider: {llm_provider}")
        return False

def main():
    """Run all checks"""
    print("=" * 50)
    print("Production Readiness Checker")
    print("=" * 50)
    
    checks = [
        check_env_file(),
        check_gitignore(),
        check_dependencies(),
        check_deployment_files(),
        check_api_keys(),
        check_database(),
    ]
    
    print("\n" + "=" * 50)
    if all(checks):
        print("✅ All checks passed! Ready for deployment!")
        print("\nNext steps:")
        print("1. Push code to GitHub: git push origin main")
        print("2. Follow RENDER_DEPLOYMENT.md guide")
        print("3. Deploy on Render.com")
        return 0
    else:
        print("❌ Some checks failed. Fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
