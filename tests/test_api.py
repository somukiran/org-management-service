"""
API Integration Tests
Tests for organization and admin API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from bson import ObjectId
from unittest.mock import AsyncMock


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns success."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Organization Management Service" in data["message"]
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestOrganizationEndpoints:
    """Tests for organization API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_organization_success(self, client: AsyncClient, mock_db):
        """Test successful organization creation."""
        # Setup mocks
        mock_db.organizations.find_one = AsyncMock(return_value=None)
        mock_db.admin_users.find_one = AsyncMock(return_value=None)
        mock_db.organizations.insert_one = AsyncMock(
            return_value=AsyncMock(inserted_id=ObjectId())
        )
        mock_db.admin_users.insert_one = AsyncMock(
            return_value=AsyncMock(inserted_id=ObjectId())
        )
        mock_db.organizations.update_one = AsyncMock()
        
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "testorg",
                "email": "admin@test.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "testorg" in data["message"]
    
    @pytest.mark.asyncio
    async def test_create_organization_duplicate(self, client: AsyncClient, mock_db):
        """Test organization creation with duplicate name."""
        # Setup mock to return existing organization
        mock_db.organizations.find_one = AsyncMock(
            return_value={"name": "testorg", "_id": ObjectId()}
        )
        
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "testorg",
                "email": "admin@test.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_create_organization_invalid_name(self, client: AsyncClient):
        """Test organization creation with invalid name."""
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "123invalid",  # Starts with number
                "email": "admin@test.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_organization_weak_password(self, client: AsyncClient):
        """Test organization creation with weak password."""
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "testorg",
                "email": "admin@test.com",
                "password": "weak"  # Too short, no uppercase/digit
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_get_organization_success(self, client: AsyncClient, mock_db):
        """Test successful organization retrieval."""
        mock_org = {
            "_id": ObjectId(),
            "name": "testorg",
            "collection_name": "org_testorg",
            "admin_email": "admin@test.com",
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "is_active": True
        }
        mock_db.organizations.find_one = AsyncMock(return_value=mock_org)
        
        response = await client.get("/org/get?organization_name=testorg")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["organization"]["name"] == "testorg"
    
    @pytest.mark.asyncio
    async def test_get_organization_not_found(self, client: AsyncClient, mock_db):
        """Test organization retrieval when not found."""
        mock_db.organizations.find_one = AsyncMock(return_value=None)
        
        response = await client.get("/org/get?organization_name=nonexistent")
        
        assert response.status_code == 404


class TestAdminEndpoints:
    """Tests for admin authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, mock_db):
        """Test successful admin login."""
        from app.core.security import security_service
        
        password_hash = security_service.get_password_hash("TestPass123")
        org_id = ObjectId()
        
        mock_admin = {
            "_id": ObjectId(),
            "email": "admin@test.com",
            "password_hash": password_hash,
            "organization_id": org_id,
            "is_active": True
        }
        mock_org = {
            "_id": org_id,
            "name": "testorg"
        }
        
        mock_db.admin_users.find_one = AsyncMock(return_value=mock_admin)
        mock_db.organizations.find_one = AsyncMock(return_value=mock_org)
        
        response = await client.post(
            "/admin/login",
            json={
                "email": "admin@test.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, mock_db):
        """Test login with invalid credentials."""
        mock_db.admin_users.find_one = AsyncMock(return_value=None)
        
        response = await client.post(
            "/admin/login",
            json={
                "email": "wrong@test.com",
                "password": "WrongPass123"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_admin_info_unauthorized(self, client: AsyncClient):
        """Test getting admin info without authentication."""
        response = await client.get("/admin/me")
        
        assert response.status_code == 403  # No auth header


class TestValidation:
    """Tests for request validation."""
    
    @pytest.mark.asyncio
    async def test_invalid_email_format(self, client: AsyncClient):
        """Test validation of invalid email format."""
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "testorg",
                "email": "not-an-email",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_organization_name_too_short(self, client: AsyncClient):
        """Test validation of short organization name."""
        response = await client.post(
            "/org/create",
            json={
                "organization_name": "ab",  # Less than 3 chars
                "email": "admin@test.com",
                "password": "TestPass123"
            }
        )
        
        assert response.status_code == 422
