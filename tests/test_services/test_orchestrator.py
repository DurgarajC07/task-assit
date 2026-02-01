"""Tests for orchestrator services."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.orchestrator.agent_manager import AgentManager
from app.services.orchestrator.tool_registry import ToolRegistry
from app.services.orchestrator.usage_tracker import UsageTracker
from app.services.orchestrator.conversation_manager import ConversationManager
from app.models import Agent, Tenant, User, Conversation


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_register_tool(self):
        """Test tool registration."""
        registry = ToolRegistry()
        
        def test_function(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y
        
        registry.register_tool(
            name="add",
            func=test_function,
            description="Add two numbers"
        )
        
        assert "add" in registry.tools
        assert registry.tools["add"].name == "add"
        assert registry.tools["add"].description == "Add two numbers"
    
    def test_execute_tool_sync(self):
        """Test executing synchronous tool."""
        registry = ToolRegistry()
        
        def multiply(x: int, y: int) -> int:
            return x * y
        
        registry.register_tool("multiply", multiply, "Multiply two numbers")
        result = registry.execute_tool("multiply", {"x": 5, "y": 3})
        
        assert result.success
        assert result.result == 15
    
    @pytest.mark.asyncio
    async def test_execute_tool_async(self):
        """Test executing asynchronous tool."""
        registry = ToolRegistry()
        
        async def async_add(x: int, y: int) -> int:
            return x + y
        
        registry.register_tool("async_add", async_add, "Async add")
        result = await registry.execute_tool("async_add", {"x": 10, "y": 5})
        
        assert result.success
        assert result.result == 15
    
    def test_execute_tool_error(self):
        """Test tool execution error handling."""
        registry = ToolRegistry()
        
        def error_func():
            raise ValueError("Test error")
        
        registry.register_tool("error_func", error_func, "Error function")
        result = registry.execute_tool("error_func", {})
        
        assert not result.success
        assert "Test error" in result.error
    
    def test_list_tools(self):
        """Test listing available tools."""
        registry = ToolRegistry()
        
        # Built-in tools should be registered
        tools = registry.list_tools()
        
        assert len(tools) >= 3  # calculator, search, time
        assert any(t["name"] == "calculator" for t in tools)
        assert any(t["name"] == "search" for t in tools)
        assert any(t["name"] == "time" for t in tools)


class TestUsageTracker:
    """Tests for UsageTracker."""
    
    @pytest.mark.asyncio
    async def test_track_completion(self, test_db: AsyncSession, test_tenant: Tenant):
        """Test tracking completion usage."""
        tracker = UsageTracker(test_db)
        
        usage_id = await tracker.track_completion(
            tenant_id=test_tenant.id,
            user_id=None,
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            metadata={"test": True}
        )
        
        assert usage_id is not None
    
    @pytest.mark.asyncio
    async def test_calculate_cost(self):
        """Test cost calculation."""
        tracker = UsageTracker(None)
        
        # OpenAI GPT-4 pricing
        cost = tracker._calculate_cost(
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        # $0.03 per 1K prompt tokens + $0.06 per 1K completion tokens
        expected_cost = (1000 * 0.03 / 1000) + (500 * 0.06 / 1000)
        assert abs(cost - expected_cost) < 0.0001
    
    @pytest.mark.asyncio
    async def test_get_usage_summary(self, test_db: AsyncSession, test_tenant: Tenant):
        """Test getting usage summary."""
        tracker = UsageTracker(test_db)
        
        # Track some usage
        await tracker.track_completion(
            tenant_id=test_tenant.id,
            user_id=None,
            provider="openai",
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        summary = await tracker.get_usage_summary(tenant_id=test_tenant.id)
        
        assert summary["total_tokens"] == 1500
        assert summary["total_cost"] > 0
        assert "openai" in summary["by_provider"]


class TestAgentManager:
    """Tests for AgentManager."""
    
    @pytest.mark.asyncio
    async def test_execute_agent_mock(
        self,
        test_db: AsyncSession,
        test_agent: Agent,
        test_user: User,
        test_tenant: Tenant
    ):
        """Test agent execution with mocked provider."""
        manager = AgentManager(test_db)
        
        with patch("app.llm.factory.LLMFactory.create_provider") as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.complete.return_value = "Test response from AI"
            mock_factory.return_value = mock_provider
            
            result = await manager.execute_agent(
                agent_id=test_agent.id,
                tenant_id=test_tenant.id,
                user_id=test_user.id,
                input_text="Test input"
            )
            
            assert result["status"] == "completed"
            assert result["output"] == "Test response from AI"
            assert "run_id" in result
            assert result["tokens_used"] > 0
    
    @pytest.mark.asyncio
    async def test_get_agent_runs(
        self,
        test_db: AsyncSession,
        test_agent: Agent,
        test_tenant: Tenant
    ):
        """Test retrieving agent runs."""
        manager = AgentManager(test_db)
        
        runs = await manager.get_agent_runs(
            tenant_id=test_tenant.id,
            agent_id=test_agent.id
        )
        
        assert isinstance(runs, list)
    
    @pytest.mark.asyncio
    async def test_get_run_stats(
        self,
        test_db: AsyncSession,
        test_agent: Agent,
        test_tenant: Tenant
    ):
        """Test getting run statistics."""
        manager = AgentManager(test_db)
        
        stats = await manager.get_run_stats(
            tenant_id=test_tenant.id,
            agent_id=test_agent.id
        )
        
        assert "total_runs" in stats
        assert "successful_runs" in stats
        assert "failed_runs" in stats
        assert "average_execution_time" in stats


class TestConversationManager:
    """Tests for ConversationManager."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_tenant: Tenant
    ):
        """Test creating a conversation."""
        manager = ConversationManager(test_db)
        
        conversation = await manager.create_conversation(
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            title="Test Chat",
            provider="openai",
            model="gpt-3.5-turbo",
            system_prompt="You are a helpful assistant."
        )
        
        assert conversation.id is not None
        assert conversation.title == "Test Chat"
        assert conversation.provider == "openai"
    
    @pytest.mark.asyncio
    async def test_add_message(
        self,
        test_db: AsyncSession,
        test_conversation: Conversation
    ):
        """Test adding a message to conversation."""
        manager = ConversationManager(test_db)
        
        message = await manager.add_message(
            conversation_id=test_conversation.id,
            role="user",
            content="Hello, how are you?"
        )
        
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
    
    @pytest.mark.asyncio
    async def test_get_messages(
        self,
        test_db: AsyncSession,
        test_conversation: Conversation
    ):
        """Test retrieving conversation messages."""
        manager = ConversationManager(test_db)
        
        # Add some messages
        await manager.add_message(test_conversation.id, "user", "Hello")
        await manager.add_message(test_conversation.id, "assistant", "Hi there!")
        
        messages = await manager.get_messages(
            conversation_id=test_conversation.id,
            limit=10
        )
        
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
    
    @pytest.mark.asyncio
    async def test_send_message_mock(
        self,
        test_db: AsyncSession,
        test_conversation: Conversation
    ):
        """Test sending a message and getting AI response."""
        manager = ConversationManager(test_db)
        
        with patch("app.llm.factory.LLMFactory.create_provider") as mock_factory:
            mock_provider = AsyncMock()
            mock_provider.complete.return_value = "This is a test response."
            mock_factory.return_value = mock_provider
            
            response = await manager.send_message(
                conversation_id=test_conversation.id,
                message="What is 2+2?"
            )
            
            assert response.role == "assistant"
            assert response.content == "This is a test response."
    
    @pytest.mark.asyncio
    async def test_conversation_context_window(
        self,
        test_db: AsyncSession,
        test_conversation: Conversation
    ):
        """Test conversation context window limiting."""
        manager = ConversationManager(test_db)
        
        # Add many messages (more than context window of 20)
        for i in range(25):
            await manager.add_message(
                test_conversation.id,
                "user" if i % 2 == 0 else "assistant",
                f"Message {i}"
            )
        
        messages = await manager.get_messages(test_conversation.id, limit=100)
        
        # Should only return last 20 messages
        assert len(messages) <= 20
