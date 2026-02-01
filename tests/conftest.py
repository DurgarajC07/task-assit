"""Test configuration and fixtures."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient
from typing import AsyncGenerator
import uuid
from datetime import datetime, timedelta

from app.database import Base
from app.models import (
    User, Task, TaskStatus, TaskPriority, Tenant,
    Agent, Conversation, Session
)
from app.core.security import hash_password, create_access_token
from app.core.tenant_context import tenant_context
from app.main import app


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
async def test_tenant(test_db: AsyncSession):
    """Create test tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        slug="test-tenant",
        subscription_plan="pro",
        is_active=True,
        settings={"features": ["all"]},
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession, test_tenant: Tenant):
    """Create test user."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="test@example.com",
        full_name="Test User",
        password_hash=hash_password("test_password_123"),
        role="admin",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_token(test_user: User, test_tenant: Tenant):
    """Create test access token."""
    token_data = {
        "sub": str(test_user.id),
        "tenant_id": str(test_tenant.id),
        "role": test_user.role,
    }
    return create_access_token(token_data)


@pytest_asyncio.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(
    test_client: AsyncClient, test_token: str
) -> AsyncClient:
    """Create authenticated test HTTP client."""
    test_client.headers.update({"Authorization": f"Bearer {test_token}"})
    return test_client


@pytest_asyncio.fixture
async def test_task(test_db: AsyncSession, test_user: User, test_tenant: Tenant):
    """Create test task."""
    tenant_context.set(test_tenant.id)
    task = Task(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
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


@pytest_asyncio.fixture
async def test_agent(test_db: AsyncSession, test_tenant: Tenant):
    """Create test agent."""
    tenant_context.set(test_tenant.id)
    agent = Agent(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Agent",
        description="Test agent for unit tests",
        instructions="You are a helpful test assistant.",
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.7,
        is_active=True,
    )
    test_db.add(agent)
    await test_db.commit()
    await test_db.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def test_conversation(test_db: AsyncSession, test_user: User, test_tenant: Tenant):
    """Create test conversation."""
    tenant_context.set(test_tenant.id)
    conversation = Conversation(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        title="Test Conversation",
        provider="openai",
        model="gpt-3.5-turbo",
    )
    test_db.add(conversation)
    await test_db.commit()
    await test_db.refresh(conversation)
    return conversation
