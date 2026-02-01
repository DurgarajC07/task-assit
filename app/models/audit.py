"""Audit log model for compliance and security (refactored)."""
from sqlalchemy import Column, String, Text, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, GUID


class AuditLog(BaseModel):
    """Audit log for compliance and security tracking."""
    
    __tablename__ = "audit_logs"
    
    # Tenant and user
    tenant_id = Column(GUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action details
    action = Column(String(255), nullable=False, index=True)
    # Examples: user.login, user.logout, task.create, task.update, task.delete,
    #           agent.create, agent.update, provider.create, settings.update, etc.
    
    # Resource affected
    resource_type = Column(String(100), nullable=False, index=True)
    # Examples: user, task, agent, provider, tenant, etc.
    
    resource_id = Column(GUID, nullable=True, index=True)
    
    # Changes (before/after values)
    changes = Column(JSON, nullable=True)
    # Example: {
    #   "before": {"status": "pending"},
    #   "after": {"status": "completed"}
    # }
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)  # For correlation
    
    # Additional info
    audit_metadata = Column(JSON, default=dict, nullable=False)
    # Can store: method, path, status_code, error, etc.
    
    # Relationships
    # tenant = relationship("Tenant")
    # user = relationship("User")
    
    __table_args__ = (
        Index("idx_audit_logs_tenant", "tenant_id"),
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index("idx_audit_logs_user_created", "user_id", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type}:{self.resource_id})>"
