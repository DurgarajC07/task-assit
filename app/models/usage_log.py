"""Usage tracking model for billing and analytics."""
from sqlalchemy import Column, String, JSON, Index, ForeignKey, Integer, Numeric, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, GUID


class UsageLog(BaseModel):
    """Usage log for metering and billing."""
    
    __tablename__ = "usage_logs"
    
    # Tenant and user
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Resources used
    agent_id = Column(GUID, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id = Column(GUID, ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True)
    model_id = Column(GUID, ForeignKey("models.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Operation type
    operation_type = Column(String(100), nullable=False, index=True)
    # Examples: agent_run, embedding, completion, etc.
    
    # Token usage
    tokens_input = Column(Integer, default=0, nullable=False)
    tokens_output = Column(Integer, default=0, nullable=False)
    tokens_total = Column(Integer, default=0, nullable=False)
    
    # Cost calculation
    cost = Column(Numeric(10, 6), default=0, nullable=False)
    
    # Additional info
    usage_metadata = Column(JSON, default=dict, nullable=False)
    # Can store: model, temperature, status, latency, etc.
    
    # Relationships
    # tenant = relationship("Tenant")
    # user = relationship("User")
    # agent = relationship("Agent")
    # provider = relationship("Provider")
    # model = relationship("Model")
    
    __table_args__ = (
        Index("idx_usage_logs_tenant", "tenant_id"),
        Index("idx_usage_logs_user", "user_id"),
        Index("idx_usage_logs_agent", "agent_id"),
        Index("idx_usage_logs_operation", "operation_type"),
        Index("idx_usage_logs_created", "created_at"),
        Index("idx_usage_logs_billing", "tenant_id", "created_at"),  # For billing queries
        Index("idx_usage_logs_analytics", "tenant_id", "user_id", "operation_type", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<UsageLog(id={self.id}, operation={self.operation_type}, tokens={self.tokens_total}, cost=${self.cost})>"
