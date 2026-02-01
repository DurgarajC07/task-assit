"""Provider and Model models for AI provider management."""
from sqlalchemy import Column, String, Text, JSON, Index, Boolean, ForeignKey, Integer, LargeBinary, Enum as SQLEnum, Numeric, DateTime
from sqlalchemy.orm import relationship
import enum
from app.models.base import TenantModel, BaseModel, GUID


class ProviderType(str, enum.Enum):
    """Provider type enum."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    OLLAMA = "ollama"


class Provider(TenantModel):
    """AI Provider configuration model.
    
    Stores provider configurations per tenant with encrypted credentials.
    """
    
    __tablename__ = "providers"
    
    name = Column(String(100), nullable=False)  # Internal identifier
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Provider type
    type = Column(SQLEnum(ProviderType), nullable=False, index=True)
    
    # Configuration (provider-specific settings)
    config = Column(JSON, default=dict, nullable=False)
    # Example config: {
    #   "base_url": "https://api.openai.com/v1",
    #   "organization_id": "org-xxx",
    #   "timeout": 30
    # }
    
    # Encrypted credentials (API keys, secrets)
    credentials_encrypted = Column(LargeBinary, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False, index=True)
    
    # Priority for fallback (lower = higher priority)
    priority = Column(Integer, default=0, nullable=False)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)
    rate_limit_per_day = Column(Integer, nullable=True)
    
    # Health check
    last_health_check_at = Column(DateTime, nullable=True)
    last_health_status = Column(String(50), nullable=True)  # healthy, unhealthy
    
    # Relationships
    # models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_providers_tenant_name", "tenant_id", "name", unique=True),
        Index("idx_providers_type", "type"),
        Index("idx_providers_active", "is_active"),
        Index("idx_providers_default", "tenant_id", "is_default"),
    )
    
    def __repr__(self) -> str:
        return f"<Provider(id={self.id}, name={self.name}, type={self.type})>"


class Model(BaseModel):
    """AI Model registry.
    
    Stores available models for each provider with pricing and capabilities.
    """
    
    __tablename__ = "models"
    
    provider_id = Column(GUID, ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Capabilities
    context_window = Column(Integer, nullable=False)  # Max tokens
    max_tokens = Column(Integer, nullable=False)  # Max output tokens
    supports_streaming = Column(Boolean, default=True, nullable=False)
    supports_functions = Column(Boolean, default=False, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    
    # Pricing (per 1K tokens)
    cost_per_1k_input = Column(Numeric(10, 6), default=0, nullable=False)
    cost_per_1k_output = Column(Numeric(10, 6), default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Additional info
    model_metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    # provider = relationship("Provider", back_populates="models")
    
    __table_args__ = (
        Index("idx_models_provider_name", "provider_id", "name", unique=True),
        Index("idx_models_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name}, provider_id={self.provider_id})>"
