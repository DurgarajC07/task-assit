"""Tests for task API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task, User, Tenant


class TestTaskEndpoints:
    """Tests for task endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        authenticated_client: AsyncClient,
        test_task: Task
    ):
        """Test listing tasks."""
        response = await authenticated_client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == test_task.title
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(
        self,
        authenticated_client: AsyncClient,
        test_task: Task
    ):
        """Test listing tasks with filters."""
        response = await authenticated_client.get(
            "/api/v1/tasks",
            params={"status": "pending", "priority": "medium"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    @pytest.mark.asyncio
    async def test_create_task(
        self,
        authenticated_client: AsyncClient
    ):
        """Test creating a new task."""
        response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "title": "New Task",
                "description": "Task description",
                "priority": "high",
                "due_date": "2026-03-01T00:00:00Z"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_task(
        self,
        authenticated_client: AsyncClient,
        test_task: Task
    ):
        """Test getting a specific task."""
        response = await authenticated_client.get(f"/api/v1/tasks/{test_task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_task.id)
        assert data["title"] == test_task.title
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting non-existent task."""
        import uuid
        fake_id = uuid.uuid4()
        response = await authenticated_client.get(f"/api/v1/tasks/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_task(
        self,
        authenticated_client: AsyncClient,
        test_task: Task
    ):
        """Test updating a task."""
        response = await authenticated_client.put(
            f"/api/v1/tasks/{test_task.id}",
            json={
                "title": "Updated Task",
                "description": "Updated description",
                "priority": "low"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Task"
        assert data["description"] == "Updated description"
        assert data["priority"] == "low"
    
    @pytest.mark.asyncio
    async def test_delete_task(
        self,
        authenticated_client: AsyncClient,
        test_task: Task
    ):
        """Test deleting a task."""
        response = await authenticated_client.delete(f"/api/v1/tasks/{test_task.id}")
        
        assert response.status_code == 204
        
        # Verify task is deleted
        response = await authenticated_client.get(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_create_task_validation_error(
        self,
        authenticated_client: AsyncClient
    ):
        """Test creating task with validation errors."""
        response = await authenticated_client.post(
            "/api/v1/tasks",
            json={
                "title": "",  # Empty title
                "priority": "invalid"  # Invalid priority
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_tasks_pagination(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        test_user: User,
        test_tenant: Tenant
    ):
        """Test task list pagination."""
        # Create multiple tasks
        from app.models import Task, TaskStatus, TaskPriority
        import uuid
        from app.core.tenant_context import tenant_context
        
        tenant_context.set(test_tenant.id)
        for i in range(15):
            task = Task(
                id=uuid.uuid4(),
                tenant_id=test_tenant.id,
                user_id=test_user.id,
                title=f"Task {i}",
                description="Test",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM
            )
            test_db.add(task)
        await test_db.commit()
        
        # Test pagination
        response = await authenticated_client.get(
            "/api/v1/tasks",
            params={"limit": 10, "offset": 0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] >= 15
    
    @pytest.mark.asyncio
    async def test_tasks_unauthorized(
        self,
        test_client: AsyncClient
    ):
        """Test accessing tasks without authentication."""
        response = await test_client.get("/api/v1/tasks")
        
        assert response.status_code == 401
