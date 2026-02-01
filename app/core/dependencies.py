"""FastAPI dependencies for injection with tenant awareness."""
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.core.tenant_context import set_tenant_context, set_user_context, get_tenant_context


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token or API key.
    
    Supports two authentication methods:
    1. Bearer token (JWT) via Authorization header
    2. API key via X-API-Key header
    
    Also extracts and sets tenant context for multi-tenant operations.
    """
    user = None
    tenant_id = None
    
    # Try API key first
    if x_api_key:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        result = await auth_service.validate_api_key(x_api_key)
        
        if result:
            api_key, user = result
            tenant_id = api_key.tenant_id
            request.state.api_key_id = api_key.id
    
    # Try JWT token if no API key
    elif authorization:
        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError()
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
            )
        
        token_data = decode_token(token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_data.get("token_type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cannot use refresh token for this operation",
                headers={"WWW-Authenticate": "Bearer"},
            )

        from sqlalchemy import select

        result = await db.execute(
            select(User).where(User.id == token_data["user_id"])
        )
        user = result.scalar_one_or_none()
        
        if user:
            tenant_id = user.tenant_id
    
    # No authentication provided
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user is active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    # Set context for this request
    if tenant_id:
        set_tenant_context(tenant_id)
        set_user_context(user.id)
        request.state.tenant_id = tenant_id
        request.state.user_id = user.id

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (deprecated, use get_current_user)."""
    return current_user


async def get_tenant_id(
    request: Request,
) -> UUID:
    """Get tenant ID from request context.
    
    Requires authentication middleware to have run first.
    """
    tenant_id = get_tenant_context()
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not available"
        )
    
    return tenant_id
