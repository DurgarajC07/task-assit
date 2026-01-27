"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.services import AuthService
from app.core import get_current_user
from app.models import User
from app.core.exceptions import (
    UserNotFoundException,
    DuplicateResourceException,
    UnauthorizedAccessException,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    request: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    try:
        service = AuthService(db)
        user = await service.register(
            username=request.username,
            email=request.email,
            password=request.password,
        )
        return user
    except DuplicateResourceException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login user."""
    try:
        service = AuthService(db)
        user, access_token, refresh_token = await service.login(
            username=request.username,
            password=request.password,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except UnauthorizedAccessException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    refresh_token_value = request.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    service = AuthService(db)
    new_access_token = await service.refresh_access_token(refresh_token_value)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user."""
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required",
        )

    service = AuthService(db)
    success = await service.logout(current_user.id, refresh_token)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to logout",
        )

    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return current_user
