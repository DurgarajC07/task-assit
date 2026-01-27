"""Task service."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.task_agent import TaskManagementAgent


class TaskService:
    """Task service."""

    def __init__(self, db: AsyncSession):
        """Initialize task service.

        Args:
            db: Database session.
        """
        self.db = db
        self.agent = TaskManagementAgent(db)

    async def create_task(self, user_id, task_data):
        """Create task."""
        return await self.agent.execute(
            action="create",
            user_id=user_id,
            task_data=task_data,
        )

    async def get_tasks(self, user_id, filters=None):
        """Get tasks."""
        return await self.agent.execute(
            action="list",
            user_id=user_id,
            filters=filters or {},
        )

    async def get_task(self, user_id, task_id):
        """Get single task."""
        return await self.agent.execute(
            action="get",
            user_id=user_id,
            task_id=task_id,
        )

    async def update_task(self, user_id, task_id, updates):
        """Update task."""
        return await self.agent.execute(
            action="update",
            user_id=user_id,
            task_id=task_id,
            updates=updates,
        )

    async def delete_task(self, user_id, task_id):
        """Delete task."""
        return await self.agent.execute(
            action="delete",
            user_id=user_id,
            task_id=task_id,
        )

    async def get_statistics(self, user_id):
        """Get task statistics."""
        return await self.agent.execute(
            action="statistics",
            user_id=user_id,
        )
