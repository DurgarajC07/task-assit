"""Role and permission models for RBAC."""
from sqlalchemy import Column, String, Text, JSON, Index, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import TenantModel, BaseModel, GUID


class Role(TenantModel):
    """Role model for RBAC."""
    
    __tablename__ = "roles"
    
    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions as JSON array of permission strings
    # Example: ["tasks:create", "tasks:update", "agents:execute"]
    permissions = Column(JSON, default=list, nullable=False)
    
    # System roles cannot be modified or deleted
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    # user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_roles_tenant_name", "tenant_id", "name", unique=True),
        Index("idx_roles_system", "is_system"),
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"


class UserRole(BaseModel):
    """User-Role mapping table."""
    
    __tablename__ = "user_roles"
    
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(GUID, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Audit fields
    assigned_by = Column(GUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    # user = relationship("User", foreign_keys=[user_id], back_populates="roles")
    # role = relationship("Role", back_populates="user_roles")
    # assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    __table_args__ = (
        Index("idx_user_roles_user_role", "user_id", "role_id", unique=True),
        Index("idx_user_roles_role", "role_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
