"""Test task agent."""
import pytest
import uuid
from datetime import datetime, timedelta
from app.agents.task_agent import TaskManagementAgent
from app.models import TaskStatus, TaskPriority


@pytest.mark.asyncio
async def test_create_task(test_db, test_user):
    """Test task creation."""
    agent = TaskManagementAgent(test_db)

    result = await agent.create_task(
        user_id=test_user.id,
        task_data={
            "title": "New Task",
            "description": "Task description",
            "priority": "high",
            "tags": ["urgent"],
        },
    )

    assert result["success"]
    assert result["data"]["title"] == "New Task"
    assert result["data"]["priority"] == "high"


@pytest.mark.asyncio
async def test_get_tasks(test_db, test_user, test_task):
    """Test retrieving tasks."""
    agent = TaskManagementAgent(test_db)

    result = await agent.get_tasks(user_id=test_user.id)

    assert result["success"]
    assert len(result["data"]["tasks"]) >= 1
    assert any(t["id"] == str(test_task.id) for t in result["data"]["tasks"])


@pytest.mark.asyncio
async def test_update_task(test_db, test_user, test_task):
    """Test task update."""
    agent = TaskManagementAgent(test_db)

    result = await agent.update_task(
        user_id=test_user.id,
        task_id=test_task.id,
        updates={
            "title": "Updated Task",
            "priority": "low",
        },
    )

    assert result["success"]
    assert result["data"]["title"] == "Updated Task"
    assert result["data"]["priority"] == "low"


@pytest.mark.asyncio
async def test_complete_task(test_db, test_user, test_task):
    """Test marking task as complete."""
    agent = TaskManagementAgent(test_db)

    result = await agent.complete_task(
        user_id=test_user.id,
        task_id=test_task.id,
    )

    assert result["success"]
    assert result["data"]["status"] == "completed"
    assert result["data"]["completed_at"] is not None


@pytest.mark.asyncio
async def test_delete_task(test_db, test_user, test_task):
    """Test task deletion (soft delete)."""
    agent = TaskManagementAgent(test_db)

    result = await agent.delete_task(
        user_id=test_user.id,
        task_id=test_task.id,
    )

    assert result["success"]

    # Verify task is soft deleted
    get_result = await agent.get_task(
        user_id=test_user.id,
        task_id=test_task.id,
    )
    assert not get_result["success"]


@pytest.mark.asyncio
async def test_search_tasks(test_db, test_user, test_task):
    """Test task search."""
    agent = TaskManagementAgent(test_db)

    result = await agent.search_tasks(
        user_id=test_user.id,
        query="test",
    )

    assert result["success"]
    assert len(result["data"]["tasks"]) >= 1


@pytest.mark.asyncio
async def test_get_statistics(test_db, test_user, test_task):
    """Test task statistics."""
    agent = TaskManagementAgent(test_db)

    result = await agent.get_statistics(user_id=test_user.id)

    assert result["success"]
    assert "total_tasks" in result["data"]
    assert "pending_tasks" in result["data"]
    assert "completed_tasks" in result["data"]
    assert result["data"]["total_tasks"] >= 1
