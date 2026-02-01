"""Middleware for tenant context extraction and injection.

Automatically extracts tenant information from requests and sets
the tenant context for downstream operations.
"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import UUID
import logging

from app.core.tenant_context import set_tenant_context, set_user_context, clear_all_context
from app.core.exceptions import UnauthorizedAccessException

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request and set tenant context.
        
        Extracts tenant information from:
        1. X-Tenant-ID header
        2. JWT token claims
        3. API key metadata
        4. Subdomain (if configured)
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        try:
            tenant_id = None
            user_id = None
            
            # Try to get tenant from header
            tenant_header = request.headers.get("X-Tenant-ID")
            if tenant_header:
                try:
                    tenant_id = UUID(tenant_header)
                    logger.debug(f"Tenant from header: {tenant_id}")
                except ValueError:
                    logger.warning(f"Invalid tenant ID in header: {tenant_header}")
            
            # Try to get from request state (set by auth dependency)
            if hasattr(request.state, "tenant_id"):
                tenant_id = request.state.tenant_id
                logger.debug(f"Tenant from auth: {tenant_id}")
            
            if hasattr(request.state, "user_id"):
                user_id = request.state.user_id
                logger.debug(f"User from auth: {user_id}")
            
            # Set context if available
            if tenant_id:
                set_tenant_context(tenant_id)
            if user_id:
                set_user_context(user_id)
            
            # Process request
            response = await call_next(request)
            
            return response
            
        finally:
            # Always clear context after request
            clear_all_context()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests for tracing."""
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Add correlation ID to request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with correlation ID header
        """
        import uuid
        
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
