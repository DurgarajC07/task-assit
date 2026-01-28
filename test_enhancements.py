"""Quick test script to verify the enhanced system works correctly."""
import asyncio
from datetime import datetime
from app.utils.date_parser import parse_natural_date, parse_time_from_string, combine_date_and_time


async def test_date_parsing():
    """Test the enhanced date parsing capabilities."""
    print("=" * 60)
    print("Testing Enhanced Date Parser")
    print("=" * 60)
    
    test_cases = [
        # Format: (input, description)
        ("tomorrow", "Tomorrow"),
        ("29th jan", "29th January (ordinal)"),
        ("january 29", "January 29"),
        ("jan 29th", "Jan 29th"),
        ("next monday", "Next Monday"),
        ("in 3 days", "In 3 days"),
        ("today", "Today"),
    ]
    
    print("\nDate Parsing Tests:")
    print("-" * 60)
    for date_str, description in test_cases:
        result = parse_natural_date(date_str)
        status = "✓" if result else "✗"
        result_str = result.strftime("%Y-%m-%d") if result else "Failed"
        print(f"{status} {description:25} | Input: '{date_str:15}' → {result_str}")
    
    print("\n" + "=" * 60)
    print("Testing Time Parser")
    print("=" * 60)
    
    time_test_cases = [
        "2pm",
        "14:00",
        "2:30pm",
        "at 2pm",
        "2 pm",
        "3:30 PM",
    ]
    
    print("\nTime Parsing Tests:")
    print("-" * 60)
    for time_str in time_test_cases:
        result = parse_time_from_string(time_str)
        status = "✓" if result else "✗"
        result_str = f"{result[0]:02d}:{result[1]:02d}" if result else "Failed"
        print(f"{status} Input: '{time_str:15}' → {result_str}")
    
    print("\n" + "=" * 60)
    print("Testing Combined Date+Time")
    print("=" * 60)
    
    combined_tests = [
        ("29th jan", "2pm"),
        ("tomorrow", "14:00"),
        ("next monday", "3:30pm"),
    ]
    
    print("\nCombined Date+Time Tests:")
    print("-" * 60)
    for date_str, time_str in combined_tests:
        date_obj = parse_natural_date(date_str)
        result = combine_date_and_time(date_obj, time_str)
        status = "✓" if result else "✗"
        result_str = result.strftime("%Y-%m-%d %H:%M") if result else "Failed"
        print(f"{status} '{date_str}' at '{time_str}' → {result_str}")
    
    print("\n" + "=" * 60)
    print("All Tests Completed!")
    print("=" * 60)


async def test_grok_provider():
    """Test Grok provider initialization."""
    print("\n" + "=" * 60)
    print("Testing Grok Provider")
    print("=" * 60)
    
    try:
        from app.llm.factory import get_provider
        from app.config import settings
        
        print(f"\nConfiguration:")
        print(f"  Provider: {settings.llm_provider}")
        print(f"  Model: {settings.llm_model}")
        print(f"  API Key Set: {'Yes' if settings.grok_api_key else 'No'}")
        
        if settings.grok_api_key:
            provider = get_provider()
            print(f"\n✓ Provider initialized successfully!")
            print(f"  Type: {type(provider).__name__}")
            print(f"  Model: {provider.model}")
        else:
            print("\n⚠ Warning: GROK_API_KEY not set in environment")
            print("  Set it in .env file to test API calls")
        
    except Exception as e:
        print(f"\n✗ Error initializing provider: {e}")
        print(f"  Make sure all dependencies are installed")
    
    print("\n" + "=" * 60)


async def test_intent_prompt():
    """Display the enhanced intent prompt."""
    print("\n" + "=" * 60)
    print("Enhanced Intent Agent System Prompt")
    print("=" * 60)
    
    from app.agents.intent_agent import IntentAgent
    
    agent = IntentAgent()
    prompt_lines = agent.INTENT_SYSTEM_PROMPT.split('\n')
    
    print("\nKey Features:")
    print("-" * 60)
    for line in prompt_lines[:20]:  # First 20 lines
        if line.strip():
            print(f"  {line.strip()}")
    
    print("\n... (prompt continues with examples and detailed instructions)")
    print("=" * 60)


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Task Assistant - Enhanced System Test" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    
    await test_date_parsing()
    await test_grok_provider()
    await test_intent_prompt()
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("  1. Set your GROK_API_KEY in .env file")
    print("  2. Run: uvicorn app.main:app --reload")
    print("  3. Visit: http://localhost:8000/docs")
    print("  4. Try: 'create a meeting for tomorrow at 29th jan on 2pm'")
    print("=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
