"""
Database Connection Module
Handles MongoDB connections and database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages MongoDB database connections.
    Implements singleton pattern for connection management.
    """
    
    _client: Optional[AsyncIOMotorClient] = None
    _master_db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """
        Establish connection to MongoDB.
        """
        if cls._client is None:
            try:
                cls._client = AsyncIOMotorClient(settings.mongodb_url)
                cls._master_db = cls._client[settings.master_db_name]
                
                # Verify connection
                await cls._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
                
                # Initialize master database collections
                await cls._initialize_master_db()
                
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """
        Close MongoDB connection.
        """
        if cls._client is not None:
            cls._client.close()
            cls._client = None
            cls._master_db = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def _initialize_master_db(cls) -> None:
        """
        Initialize master database with required collections and indexes.
        """
        if cls._master_db is not None:
            # Create indexes for organizations collection
            await cls._master_db.organizations.create_index("name", unique=True)
            await cls._master_db.organizations.create_index("collection_name", unique=True)
            
            # Create indexes for admin_users collection
            await cls._master_db.admin_users.create_index("email", unique=True)
            await cls._master_db.admin_users.create_index("organization_id")
            
            logger.info("Master database initialized with indexes")
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """
        Get the MongoDB client instance.
        
        Returns:
            AsyncIOMotorClient: The MongoDB client
            
        Raises:
            RuntimeError: If not connected to database
        """
        if cls._client is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls._client
    
    @classmethod
    def get_master_db(cls) -> AsyncIOMotorDatabase:
        """
        Get the master database instance.
        
        Returns:
            AsyncIOMotorDatabase: The master database
            
        Raises:
            RuntimeError: If not connected to database
        """
        if cls._master_db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls._master_db
    
    @classmethod
    def get_organization_collection(cls, collection_name: str):
        """
        Get a specific organization's collection.
        
        Args:
            collection_name: The name of the organization's collection
            
        Returns:
            Collection: The organization's collection
        """
        return cls.get_master_db()[collection_name]
    
    @classmethod
    async def create_organization_collection(cls, collection_name: str) -> bool:
        """
        Create a new collection for an organization.
        
        Args:
            collection_name: The name for the new collection
            
        Returns:
            bool: True if successful
        """
        try:
            db = cls.get_master_db()
            
            # Create the collection
            await db.create_collection(collection_name)
            
            # Initialize with a basic schema document (optional)
            collection = db[collection_name]
            await collection.insert_one({
                "_schema_version": "1.0",
                "_created_at": "initialization",
                "_type": "schema_metadata"
            })
            
            # Create basic indexes for the organization collection
            await collection.create_index("_type")
            await collection.create_index("created_at")
            
            logger.info(f"Created organization collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    @classmethod
    async def delete_organization_collection(cls, collection_name: str) -> bool:
        """
        Delete an organization's collection.
        
        Args:
            collection_name: The name of the collection to delete
            
        Returns:
            bool: True if successful
        """
        try:
            db = cls.get_master_db()
            await db.drop_collection(collection_name)
            logger.info(f"Deleted organization collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            raise
    
    @classmethod
    async def rename_collection(cls, old_name: str, new_name: str) -> bool:
        """
        Rename a collection (used for organization updates).
        
        Args:
            old_name: Current collection name
            new_name: New collection name
            
        Returns:
            bool: True if successful
        """
        try:
            db = cls.get_master_db()
            collection = db[old_name]
            await collection.rename(new_name)
            logger.info(f"Renamed collection from {old_name} to {new_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to rename collection: {e}")
            raise


# Dependency for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency for getting database instance.
    """
    return DatabaseManager.get_master_db()
