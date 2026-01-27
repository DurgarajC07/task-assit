"""Test intent agent."""
import pytest
import json
from app.agents.intent_agent import IntentAgent


@pytest.mark.asyncio
async def test_create_task_intent():
    """Test intent detection for task creation."""
    agent = IntentAgent()

    result = await agent.execute("Add a task to buy milk tomorrow at 2pm")

    assert result["success"]
    assert result["intent"] == "CREATE_TASK"
    assert result["confidence"] > 0.7
    assert "title" in result["entities"] or "entities" in result


@pytest.mark.asyncio
async def test_list_tasks_intent():
    """Test intent detection for task listing."""
    agent = IntentAgent()

    result = await agent.execute("Show me my tasks for today")

    assert result["success"]
    assert result["intent"] in ["LIST_TASKS", "GET_STATISTICS"]


@pytest.mark.asyncio
async def test_unclear_intent():
    """Test unclear intent handling."""
    agent = IntentAgent()

    result = await agent.execute("xyzabc qwerty")

    assert result["success"]
    assert result["intent"] == "UNCLEAR" or result["confidence"] < 0.6
