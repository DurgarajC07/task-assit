"""Tenant context management for multi-tenant operations.

Provides thread-safe tenant context storage and access throughout
the request lifecycle.
"""
from contextvars import ContextVar
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# Context variable for current tenant
_tenant_context: ContextVar[Optional[UUID]] = ContextVar('tenant_context', default=None)

# Context variable for current user
_user_context: ContextVar[Optional[UUID]] = ContextVar('user_context', default=None)


def set_tenant_context(tenant_id: UUID) -> None:
    """Set current tenant context.
    
    Args:
        tenant_id: Tenant UUID
    """
    _tenant_context.set(tenant_id)
    logger.debug(f"Tenant context set to: {tenant_id}")


def get_tenant_context() -> Optional[UUID]:
    """Get current tenant context.
    
    Returns:
        Current tenant UUID or None
    """
    return _tenant_context.get()


def clear_tenant_context() -> None:
    """Clear tenant context."""
    _tenant_context.set(None)
    logger.debug("Tenant context cleared")


def set_user_context(user_id: UUID) -> None:
    """Set current user context.
    
    Args:
        user_id: User UUID
    """
    _user_context.set(user_id)
    logger.debug(f"User context set to: {user_id}")


def get_user_context() -> Optional[UUID]:
    """Get current user context.
    
    Returns:
        Current user UUID or None
    """
    return _user_context.get()


def clear_user_context() -> None:
    """Clear user context."""
    _user_context.set(None)
    logger.debug("User context cleared")


def clear_all_context() -> None:
    """Clear all context variables."""
    clear_tenant_context()
    clear_user_context()
    logger.debug("All context cleared")


class TenantContext:
    """Context manager for tenant operations.
    
    Example:
        with TenantContext(tenant_id):
            # All operations within this block are scoped to tenant_id
            result = await service.get_data()
    """
    
    def __init__(self, tenant_id: UUID):
        """Initialize tenant context.
        
        Args:
            tenant_id: Tenant UUID
        """
        self.tenant_id = tenant_id
        self.previous_tenant = None
    
    def __enter__(self):
        """Enter context and set tenant."""
        self.previous_tenant = get_tenant_context()
        set_tenant_context(self.tenant_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous tenant."""
        if self.previous_tenant:
            set_tenant_context(self.previous_tenant)
        else:
            clear_tenant_context()


class UserContext:
    """Context manager for user operations.
    
    Example:
        with UserContext(user_id):
            # All operations within this block have user context
            result = await service.create_item()
    """
    
    def __init__(self, user_id: UUID):
        """Initialize user context.
        
        Args:
            user_id: User UUID
        """
        self.user_id = user_id
        self.previous_user = None
    
    def __enter__(self):
        """Enter context and set user."""
        self.previous_user = get_user_context()
        set_user_context(self.user_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore previous user."""
        if self.previous_user:
            set_user_context(self.previous_user)
        else:
            clear_user_context()
