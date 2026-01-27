"""Authentication service."""
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, UserSession
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import (
    UserNotFoundException,
    DuplicateResourceException,
    UnauthorizedAccessException,
)


class AuthService:
    """Authentication service."""

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
