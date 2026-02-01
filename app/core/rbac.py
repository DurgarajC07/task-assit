"""Role-Based Access Control (RBAC) utilities and dependencies.

Provides FastAPI dependencies for permission checking and role verification.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.tenant_context import get_tenant_context
import logging

logger = logging.getLogger(__name__)


class PermissionChecker:
    """Dependency class for checking user permissions.
    
    Usage:
        @router.post("/tasks")
        async def create_task(
            task: TaskCreate,
            _: None = Depends(PermissionChecker(["tasks:create"]))
        ):
            # User has tasks:create permission
            ...
    """
    
    def __init__(self, required_permissions: List[str]):
        """Initialize permission checker.
        
        Args:
            required_permissions: List of required permissions
        """
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> None:
        """Check if user has required permissions.
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Raises:
            HTTPException: If user lacks required permissions
        """
        tenant_id = get_tenant_context()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context not set"
            )
        
        auth_service = AuthService(db)
        
        # Check each required permission
        for permission in self.required_permissions:
            has_permission = await auth_service.check_permission(
                user_id=current_user.id,
                tenant_id=tenant_id,
                permission=permission
            )
            
            if not has_permission:
                logger.warning(
                    f"User {current_user.id} lacks permission: {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission}"
                )
        
        logger.debug(f"User {current_user.id} has permissions: {self.required_permissions}")


class RoleChecker:
    """Dependency class for checking user roles.
    
    Usage:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            _: None = Depends(RoleChecker(["admin", "user_manager"]))
        ):
            # User has admin or user_manager role
            ...
    """
    
    def __init__(self, required_roles: List[str]):
        """Initialize role checker.
        
        Args:
            required_roles: List of required role names (any match)
        """
        self.required_roles = required_roles
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> None:
        """Check if user has any of the required roles.
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Raises:
            HTTPException: If user lacks required roles
        """
        tenant_id = get_tenant_context()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context not set"
            )
        
        auth_service = AuthService(db)
        user_roles = await auth_service.get_user_roles(
            user_id=current_user.id,
            tenant_id=tenant_id
        )
        
        # Check if user has any of the required roles
        user_role_names = {role.name for role in user_roles}
        has_required_role = any(
            role_name in user_role_names
            for role_name in self.required_roles
        )
        
        if not has_required_role:
            logger.warning(
                f"User {current_user.id} lacks roles: {self.required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role (need one of: {', '.join(self.required_roles)})"
            )
        
        logger.debug(f"User {current_user.id} has required role")


async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[str]:
    """Get all permissions for current user.
    
    Usage:
        async def my_endpoint(
            permissions: List[str] = Depends(get_user_permissions)
        ):
            if "tasks:delete" in permissions:
                # User can delete tasks
                ...
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of permission strings
    """
    tenant_id = get_tenant_context()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not set"
        )
    
    auth_service = AuthService(db)
    permissions = await auth_service.get_user_permissions(
        user_id=current_user.id,
        tenant_id=tenant_id
    )
    
    return list(permissions)


# Common permission patterns
PERMISSIONS = {
    # Task permissions
    "tasks:create": "Create tasks",
    "tasks:read": "Read tasks",
    "tasks:update": "Update tasks",
    "tasks:delete": "Delete tasks",
    "tasks:*": "All task permissions",
    
    # Agent permissions
    "agents:create": "Create agents",
    "agents:read": "Read agents",
    "agents:update": "Update agents",
    "agents:delete": "Delete agents",
    "agents:execute": "Execute agents",
    "agents:*": "All agent permissions",
    
    # User permissions
    "users:create": "Create users",
    "users:read": "Read users",
    "users:update": "Update users",
    "users:delete": "Delete users",
    "users:*": "All user permissions",
    
    # Provider permissions
    "providers:create": "Create providers",
    "providers:read": "Read providers",
    "providers:update": "Update providers",
    "providers:delete": "Delete providers",
    "providers:*": "All provider permissions",
    
    # Billing permissions
    "billing:read": "Read billing info",
    "billing:update": "Update billing info",
    "billing:*": "All billing permissions",
    
    # Admin permissions
    "admin:*": "All admin permissions",
    "*:*": "All permissions (super admin)",
}


# Common role definitions
DEFAULT_ROLES = {
    "owner": {
        "description": "Tenant owner with full access",
        "permissions": ["*:*"],
        "is_system": True,
    },
    "admin": {
        "description": "Administrator with most permissions",
        "permissions": [
            "tasks:*", "agents:*", "users:*", "providers:*", "billing:read"
        ],
        "is_system": True,
    },
    "developer": {
        "description": "Developer with agent and task access",
        "permissions": [
            "tasks:*", "agents:*", "providers:read"
        ],
        "is_system": True,
    },
    "user": {
        "description": "Regular user with basic access",
        "permissions": [
            "tasks:create", "tasks:read", "tasks:update", "agents:read", "agents:execute"
        ],
        "is_system": True,
    },
    "viewer": {
        "description": "Read-only access",
        "permissions": [
            "tasks:read", "agents:read"
        ],
        "is_system": True,
    },
}
