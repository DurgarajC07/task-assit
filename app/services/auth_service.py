"""Enhanced authentication service with RBAC support.

Handles user authentication, authorization, API keys, and permission checking.
"""
from typing import Optional, List, Set
from uuid import UUID
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import secrets
import hashlib

from app.models.user import User
from app.models.session import UserSession
from app.models.role import Role, UserRole
from app.models.api_key import APIKey
from app.core.security import (
    hash_password,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import (
    UserNotFoundException,
    DuplicateResourceException,
    UnauthorizedAccessException,
)
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication and authorization."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service.

        Args:
            db: Database session.
        """
        self.db = db

    async def register(
        self,
        username: str,
        email: str,
        password: str,
    ) -> User:
        """Register a new user.

        Args:
            username: Username.
            email: Email address.
            password: Password.

        Returns:
            Created user.

        Raises:
            DuplicateResourceException: If user already exists.
        """
        # Check if user exists
        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise DuplicateResourceException(
                "User",
                username or email,
            )

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            preferences={
                "default_priority": "medium",
                "date_format": "ISO",
                "timezone": "UTC",
            },
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def login(
        self,
        username: str,
        password: str,
    ) -> tuple[User, str, str]:
        """Login user.

        Args:
            username: Username.
            password: Password.

        Returns:
            Tuple of (user, access_token, refresh_token).

        Raises:
            UserNotFoundException: If user not found.
            UnauthorizedAccessException: If password is incorrect.
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotFoundException(username)

        if not verify_password(password, user.password_hash):
            raise UnauthorizedAccessException(
                "Invalid password"
            )

        # Create tokens
        access_token = create_access_token(user.id, user.username)
        refresh_token = create_refresh_token(user.id, user.username)

        # Store session
        session = UserSession(
            user_id=user.id,
            session_token=refresh_token,
            expires_at=UserSession.create_expiry(),
        )
        self.db.add(session)
        await self.db.commit()

        return user, access_token, refresh_token

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> Optional[str]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token.

        Returns:
            New access token or None if invalid.
        """
        token_data = decode_token(refresh_token)

        if not token_data or token_data.get("token_type") != "refresh":
            return None

        user_id = token_data.get("user_id")

        # Verify session exists and is valid
        result = await self.db.execute(
            select(UserSession).where(
                (UserSession.user_id == user_id)
                & (UserSession.session_token == refresh_token)
                & (UserSession.expires_at > datetime.utcnow())
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Create new access token
        username = token_data.get("username")
        return create_access_token(user_id, username)

    async def logout(
        self,
        user_id: uuid.UUID,
        refresh_token: str,
    ) -> bool:
        """Logout user by invalidating refresh token.

        Args:
            user_id: User ID.
            refresh_token: Refresh token.

        Returns:
            Success status.
        """
        result = await self.db.execute(
            select(UserSession).where(
                (UserSession.user_id == user_id)
                & (UserSession.session_token == refresh_token)
            )
        )
        session = result.scalar_one_or_none()

        if session:
            await self.db.delete(session)
            await self.db.commit()
            return True

        return False

    async def get_user(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID.

        Returns:
            User or None.
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(
        self,
        username: str,
        password: str,
        tenant_id: UUID
    ) -> Optional[User]:
        """Authenticate user with username/password for specific tenant.
        
        Args:
            username: Username or email
            password: Plain text password
            tenant_id: Tenant UUID
            
        Returns:
            User if authenticated, None otherwise
        """
        # Try username first
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.tenant_id == tenant_id,
                    User.username == username,
                    User.deleted_at.is_(None)
                )
            )
        )
        user = result.scalar_one_or_none()
        
        # Try email if username not found
        if not user:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.tenant_id == tenant_id,
                        User.email == username,
                        User.deleted_at.is_(None)
                    )
                )
            )
            user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"User not found: {username}")
            return None
        
        # Check password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password for user: {username}")
            return None
        
        # Check if user is active
        if user.status != "active":
            logger.warning(f"User not active: {username} (status: {user.status})")
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        
        logger.info(f"User authenticated: {username}")
        return user
    
    async def create_api_key(
        self,
        user_id: UUID,
        tenant_id: UUID,
        name: str,
        expires_at: Optional[datetime] = None,
        scopes: Optional[List[str]] = None
    ) -> tuple[APIKey, str]:
        """Create API key for user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            name: Key name/description
            expires_at: Optional expiration
            scopes: Optional permission scopes
            
        Returns:
            Tuple of (APIKey, raw_key)
        """
        # Generate secure random key
        raw_key = f"{settings.api_key_prefix}{secrets.token_urlsafe(settings.api_key_length)}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Create API key
        api_key = APIKey(
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            key_hash=key_hash,
            expires_at=expires_at,
            scopes=scopes or [],
            status="active"
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        logger.info(f"Created API key '{name}' for user {user_id}")
        return api_key, raw_key
    
    async def validate_api_key(
        self,
        raw_key: str
    ) -> Optional[tuple[APIKey, User]]:
        """Validate API key and return associated user.
        
        Args:
            raw_key: Raw API key from request
            
        Returns:
            Tuple of (APIKey, User) if valid, None otherwise
        """
        # Hash the key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Find key
        result = await self.db.execute(
            select(APIKey).where(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.status == "active",
                    APIKey.deleted_at.is_(None)
                )
            )
        )
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            logger.warning("Invalid API key")
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key: {api_key.name}")
            return None
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == api_key.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.status != "active":
            logger.warning(f"API key user not active: {api_key.user_id}")
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        await self.db.commit()
        
        return api_key, user
    
    async def get_user_roles(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> List[Role]:
        """Get all roles for user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            
        Returns:
            List of roles
        """
        result = await self.db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                and_(
                    UserRole.user_id == user_id,
                    Role.tenant_id == tenant_id,
                    Role.deleted_at.is_(None)
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_user_permissions(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> Set[str]:
        """Get all permissions for user.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            
        Returns:
            Set of permission strings
        """
        roles = await self.get_user_roles(user_id, tenant_id)
        
        permissions = set()
        for role in roles:
            permissions.update(role.permissions)
        
        return permissions
    
    async def check_permission(
        self,
        user_id: UUID,
        tenant_id: UUID,
        permission: str
    ) -> bool:
        """Check if user has specific permission.
        
        Args:
            user_id: User UUID
            tenant_id: Tenant UUID
            permission: Permission string (e.g., "tasks:create")
            
        Returns:
            True if user has permission
        """
        permissions = await self.get_user_permissions(user_id, tenant_id)
        
        # Check exact match
        if permission in permissions:
            return True
        
        # Check wildcard permissions (e.g., "tasks:*" matches "tasks:create")
        if ":" in permission:
            resource, action = permission.split(":", 1)
            wildcard = f"{resource}:*"
            if wildcard in permissions:
                return True
        
        # Check admin permission
        if "*:*" in permissions:
            return True
        
        return False
    
    async def assign_role(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: UUID
    ) -> UserRole:
        """Assign role to user.
        
        Args:
            user_id: User UUID
            role_id: Role UUID
            assigned_by: User who assigned the role
            
        Returns:
            UserRole assignment
        """
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow()
        )
        
        self.db.add(user_role)
        await self.db.commit()
        await self.db.refresh(user_role)
        
        logger.info(f"Assigned role {role_id} to user {user_id}")
        return user_role
    
    async def revoke_role(
        self,
        user_id: UUID,
        role_id: UUID
    ) -> bool:
        """Revoke role from user.
        
        Args:
            user_id: User UUID
            role_id: Role UUID
            
        Returns:
            True if revoked, False if not found
        """
        result = await self.db.execute(
            select(UserRole).where(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role_id
                )
            )
        )
        user_role = result.scalar_one_or_none()
        
        if not user_role:
            return False
        
        await self.db.delete(user_role)
        await self.db.commit()
        
        logger.info(f"Revoked role {role_id} from user {user_id}")
        return True
    
    async def create_role(
        self,
        tenant_id: UUID,
        name: str,
        description: Optional[str],
        permissions: List[str],
        is_system: bool = False
    ) -> Role:
        """Create new role.
        
        Args:
            tenant_id: Tenant UUID
            name: Role name
            description: Role description
            permissions: List of permissions
            is_system: System role (cannot be modified)
            
        Returns:
            Created role
        """
        role = Role(
            tenant_id=tenant_id,
            name=name,
            description=description,
            permissions=permissions,
            is_system=is_system
        )
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        
        logger.info(f"Created role '{name}' for tenant {tenant_id}")
        return role
