"""Agent models for dynamic agent system."""
from sqlalchemy import Column, String, Text, JSON, Index, Boolean, ForeignKey, Integer, Enum as SQLEnum, Numeric, DateTime
from sqlalchemy.orm import relationship
import enum
from app.models.base import TenantModel, BaseModel, GUID


class MemoryStrategy(str, enum.Enum):
    """Agent memory strategy enum."""
    NONE = "none"  # No memory
    CONVERSATION_BUFFER = "conversation_buffer"  # Simple conversation buffer
    CONVERSATION_SUMMARY = "conversation_summary"  # Summarize old messages
    VECTOR = "vector"  # Vector store for semantic retrieval


class Agent(TenantModel):
    """Dynamic agent configuration model.
    
    Agents can be created and configured at runtime without code changes.
    """
    
    __tablename__ = "agents"
    
    name = Column(String(255), nullable=False)  # Internal identifier
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # LLM Configuration
    model_id = Column(GUID, ForeignKey("models.id", ondelete="RESTRICT"), nullable=False, index=True)
    system_prompt = Column(Text, nullable=False)
    
    # Model parameters
    temperature = Column(Numeric(3, 2), default=0.7, nullable=False)
    max_tokens = Column(Integer, default=1000, nullable=False)
    top_p = Column(Numeric(3, 2), default=1.0, nullable=False)
    frequency_penalty = Column(Numeric(3, 2), default=0.0, nullable=False)
    presence_penalty = Column(Numeric(3, 2), default=0.0, nullable=False)
    
    # Tools (function calling)
    tools = Column(JSON, default=list, nullable=False)
    # Example: ["task_create", "task_update", "search_tasks"]
    
    # Memory configuration
    memory_strategy = Column(SQLEnum(MemoryStrategy), default=MemoryStrategy.CONVERSATION_BUFFER, nullable=False)
    memory_config = Column(JSON, default=dict, nullable=False)
    # Example: {"max_messages": 20, "summary_interval": 10}
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System agents can't be deleted
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    
    # Audit
    created_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    # model = relationship("Model")
    # runs = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_agents_tenant_name", "tenant_id", "name", unique=True),
        Index("idx_agents_model", "model_id"),
        Index("idx_agents_active", "is_active"),
        Index("idx_agents_system", "is_system"),
    )
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, model_id={self.model_id})>"


class AgentTool(TenantModel):
    """Tool registry for agent function calling."""
    
    __tablename__ = "agent_tools"
    
    name = Column(String(255), nullable=False)  # e.g., "task_create"
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Function mapping
    function_name = Column(String(255), nullable=False)  # Python function to call
    module_path = Column(String(500), nullable=False)  # Full module path
    
    # Parameters schema (OpenAI function calling format)
    parameters_schema = Column(JSON, nullable=False)
    # Example: {
    #   "type": "object",
    #   "properties": {
    #     "title": {"type": "string"},
    #     "priority": {"type": "string", "enum": ["low", "medium", "high"]}
    #   },
    #   "required": ["title"]
    # }
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    # (Many-to-many relationship with agents through the tools JSON field)
    
    __table_args__ = (
        Index("idx_agent_tools_tenant_name", "tenant_id", "name", unique=True),
        Index("idx_agent_tools_active", "is_active"),
        Index("idx_agent_tools_function", "function_name"),
    )
    
    def __repr__(self) -> str:
        return f"<AgentTool(id={self.id}, name={self.name})>"


class AgentRunStatus(str, enum.Enum):
    """Agent run status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRun(TenantModel):
    """Agent execution history and metrics."""
    
    __tablename__ = "agent_runs"
    
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(GUID, nullable=False, index=True)  # Groups related runs
    
    # Input/Output
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(AgentRunStatus), default=AgentRunStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Metrics
    tokens_input = Column(Integer, default=0, nullable=False)
    tokens_output = Column(Integer, default=0, nullable=False)
    tokens_total = Column(Integer, default=0, nullable=False)
    cost = Column(Numeric(10, 6), default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)  # Total execution time
    
    # Additional info
    run_metadata = Column(JSON, default=dict, nullable=False)
    # Can store: model_used, temperature, tools_called, etc.
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    # agent = relationship("Agent", back_populates="runs")
    # user = relationship("User")
    
    __table_args__ = (
        Index("idx_agent_runs_agent", "agent_id"),
        Index("idx_agent_runs_user", "user_id"),
        Index("idx_agent_runs_session", "session_id"),
        Index("idx_agent_runs_status", "status"),
        Index("idx_agent_runs_created", "created_at"),
        Index("idx_agent_runs_tenant_user_created", "tenant_id", "user_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent_id={self.agent_id}, status={self.status})>"
