"""
Test Configuration Module
Provides test fixtures and configuration for pytest.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.db.database import DatabaseManager


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db():
    """
    Mock database for testing without MongoDB connection.
    """
    # Create mock collections
    mock_organizations = AsyncMock()
    mock_admin_users = AsyncMock()
    
    # Create mock database
    mock_database = MagicMock()
    mock_database.organizations = mock_organizations
    mock_database.admin_users = mock_admin_users
    mock_database.__getitem__ = MagicMock(return_value=AsyncMock())
    mock_database.create_collection = AsyncMock()
    mock_database.drop_collection = AsyncMock()
    
    # Patch DatabaseManager
    original_get_master_db = DatabaseManager.get_master_db
    DatabaseManager.get_master_db = MagicMock(return_value=mock_database)
    DatabaseManager._client = MagicMock()
    DatabaseManager._master_db = mock_database
    
    yield mock_database
    
    # Restore original
    DatabaseManager.get_master_db = original_get_master_db
    DatabaseManager._client = None
    DatabaseManager._master_db = None


@pytest.fixture
async def client(mock_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Sample test data
TEST_ORGANIZATION = {
    "organization_name": "testorg",
    "email": "admin@testorg.com",
    "password": "TestPass123"
}

TEST_ADMIN = {
    "email": "admin@testorg.com",
    "password": "TestPass123"
}
