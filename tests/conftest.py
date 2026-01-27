"""Test configuration and fixtures."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import User, Task, TaskStatus, TaskPriority
from app.core.security import hash_password
import uuid
from datetime import datetime


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession):
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("test_password_123"),
        preferences={},
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_task(test_db: AsyncSession, test_user: User):
    """Create test task."""
    task = Task(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Test Task",
        description="This is a test task",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        due_date=datetime.utcnow(),
        tags=["test"],
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    return task
