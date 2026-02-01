"""Tests for authentication API endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.core.security import verify_password


class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user(self, test_client: AsyncClient, test_db: AsyncSession):
        """Test user registration."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecureP@ssw0rd123",
                "full_name": "New User",
                "tenant_name": "New Tenant"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "tenant_id" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test registration with duplicate email."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "full_name": "Duplicate User",
                "tenant_name": "Tenant"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "test_password_123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_client: AsyncClient):
        """Test login with invalid credentials."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test login with wrong password."""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user(
        self,
        authenticated_client: AsyncClient,
        test_user: User
    ):
        """Test getting current user information."""
        response = await authenticated_client.get("/api/v1/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, test_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_token(
        self,
        authenticated_client: AsyncClient
    ):
        """Test token refresh."""
        response = await authenticated_client.post("/api/v1/auth/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_register_validation_error(self, test_client: AsyncClient):
        """Test registration with validation errors."""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",  # Invalid email format
                "password": "short",  # Too short
                "full_name": "User",
                "tenant_name": "Tenant"
            }
        )
        
        assert response.status_code == 422
        assert "detail" in response.json()
