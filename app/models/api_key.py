"""API Key model for programmatic access."""
from sqlalchemy import Column, String, JSON, Index, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.models.base import TenantModel, GUID


class APIKey(TenantModel):
    """API Key model for programmatic access to the platform."""
    
    __tablename__ = "api_keys"
    
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Key storage (hashed)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # e.g., "ta_abc123" for identification
    
    # Permissions and scopes
    scopes = Column(JSON, default=list, nullable=False)  # List of allowed permissions
    
    # Status
    status = Column(String(50), default="active", nullable=False, index=True)  # active, revoked
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    last_used_ip = Column(String(45), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    # tenant = relationship("Tenant")
    # user = relationship("User")
    
    __table_args__ = (
        Index("idx_api_keys_tenant", "tenant_id"),
        Index("idx_api_keys_user", "user_id"),
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_status", "status"),
        Index("idx_api_keys_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"
