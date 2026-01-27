"""Database seeding script for sample data."""
import asyncio
import uuid
import os
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings
from app.database import Base
from app.models import (
    User,
    Task,
    TaskStatus,
    TaskPriority,
    ConversationHistory,
    MessageRole,
)
from app.core.security import hash_password


async def seed_database():
    """Seed database with sample data."""
    # Create engine and tables
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        # Check if demo user already exists
        from sqlalchemy import select
        existing_user = await session.execute(
            select(User).where(User.username == "demo_user")
        )
        if existing_user.scalar():
            print("✓ Demo user already exists, skipping seed")
            return

        # Create sample user
        user = User(
            id=uuid.uuid4(),
            username="demo_user",
            email="demo@example.com",
            password_hash=hash_password("demo_password_123"),
            preferences={
                "default_priority": "medium",
                "date_format": "ISO",
                "timezone": "UTC",
            },
        )
        session.add(user)
        await session.flush()

        # Create sample tasks
        now = datetime.utcnow()
        tasks_data = [
            {
                "title": "Buy groceries",
                "description": "Milk, eggs, bread, and vegetables",
                "priority": TaskPriority.HIGH,
                "due_date": now + timedelta(days=1),
                "tags": ["shopping", "personal"],
                "status": TaskStatus.PENDING,
            },
            {
                "title": "Complete project report",
                "description": "Finish Q1 report and submit to manager",
                "priority": TaskPriority.URGENT,
                "due_date": now + timedelta(days=2),
                "tags": ["work", "important"],
                "status": TaskStatus.IN_PROGRESS,
            },
            {
                "title": "Schedule dentist appointment",
                "description": "Call dentist to book cleaning",
                "priority": TaskPriority.MEDIUM,
                "due_date": now + timedelta(days=7),
                "tags": ["health", "personal"],
                "status": TaskStatus.PENDING,
            },
            {
                "title": "Exercise for 30 minutes",
                "description": "Morning run or gym session",
                "priority": TaskPriority.MEDIUM,
                "due_date": now + timedelta(hours=6),
                "tags": ["health", "fitness"],
                "status": TaskStatus.PENDING,
            },
            {
                "title": "Review team presentations",
                "description": "Review presentations for Thursday meeting",
                "priority": TaskPriority.HIGH,
                "due_date": now + timedelta(days=3),
                "tags": ["work", "meetings"],
                "status": TaskStatus.PENDING,
            },
            {
                "title": "Read project documentation",
                "description": "Read and understand new API documentation",
                "priority": TaskPriority.LOW,
                "due_date": now + timedelta(days=5),
                "tags": ["work", "learning"],
                "status": TaskStatus.PENDING,
            },
            {
                "title": "Completed: Weekly standup",
                "description": "Attended and participated in team standup",
                "priority": TaskPriority.MEDIUM,
                "due_date": now - timedelta(days=1),
                "tags": ["work", "meetings"],
                "status": TaskStatus.COMPLETED,
                "completed_at": now - timedelta(hours=2),
            },
        ]

        for task_data in tasks_data:
            completed_at = task_data.pop("completed_at", None)
            task = Task(
                id=uuid.uuid4(),
                user_id=user.id,
                **task_data,
            )
            if completed_at:
                task.completed_at = completed_at
            session.add(task)

        # Create sample conversation history
        session_id = uuid.uuid4()
        conversations = [
            ConversationHistory(
                id=uuid.uuid4(),
                user_id=user.id,
                session_id=session_id,
                role=MessageRole.USER,
                message="Add a task to buy groceries tomorrow at 5pm",
                intent="CREATE_TASK",
                entities={
                    "title": "buy groceries",
                    "due_date": "tomorrow",
                    "due_time": "5pm",
                },
            ),
            ConversationHistory(
                id=uuid.uuid4(),
                user_id=user.id,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                message="✓ Task 'buy groceries' created successfully!",
                intent="CREATE_TASK",
            ),
            ConversationHistory(
                id=uuid.uuid4(),
                user_id=user.id,
                session_id=session_id,
                role=MessageRole.USER,
                message="Show me my tasks for today",
                intent="LIST_TASKS",
                entities={"filters": ["today"]},
            ),
            ConversationHistory(
                id=uuid.uuid4(),
                user_id=user.id,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                message="You have 2 tasks due today.",
                intent="LIST_TASKS",
            ),
        ]

        for conv in conversations:
            session.add(conv)

        await session.commit()
        print("✓ Database seeded successfully!")
        print(f"  - User: demo_user (password: demo_password_123)")
        print(f"  - Tasks: {len(tasks_data)}")
        print(f"  - Conversation history: {len(conversations)} messages")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
