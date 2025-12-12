"""
Organization Service Module
Handles all organization-related business logic.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
import logging

from app.db.database import DatabaseManager
from app.core.security import security_service
from app.schemas import OrganizationCreate, OrganizationUpdate, OrganizationResponse

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Service class for organization management operations.
    Implements business logic for CRUD operations on organizations.
    """
    
    @staticmethod
    def _generate_collection_name(org_name: str) -> str:
        """
        Generate a collection name for an organization.
        
        Args:
            org_name: The organization name
            
        Returns:
            str: The collection name (e.g., 'org_mycompany')
        """
        return f"org_{org_name.lower().replace(' ', '_')}"
    
    @staticmethod
    async def get_organization_by_name(org_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an organization by its name.
        
        Args:
            org_name: The organization name
            
        Returns:
            Optional[Dict]: Organization data if found, None otherwise
        """
        db = DatabaseManager.get_master_db()
        organization = await db.organizations.find_one({"name": org_name.lower()})
        return organization
    
    @staticmethod
    async def get_organization_by_id(org_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an organization by its ID.
        
        Args:
            org_id: The organization ID
            
        Returns:
            Optional[Dict]: Organization data if found, None otherwise
        """
        db = DatabaseManager.get_master_db()
        organization = await db.organizations.find_one({"_id": ObjectId(org_id)})
        return organization
    
    @staticmethod
    async def create_organization(data: OrganizationCreate) -> Dict[str, Any]:
        """
        Create a new organization with admin user.
        
        Args:
            data: Organization creation data
            
        Returns:
            Dict: Created organization data
            
        Raises:
            ValueError: If organization already exists
        """
        db = DatabaseManager.get_master_db()
        
        # Check if organization already exists
        existing_org = await db.organizations.find_one({"name": data.organization_name})
        if existing_org:
            raise ValueError(f"Organization '{data.organization_name}' already exists")
        
        # Check if admin email already exists
        existing_admin = await db.admin_users.find_one({"email": data.email})
        if existing_admin:
            raise ValueError(f"Admin with email '{data.email}' already exists")
        
        # Generate collection name
        collection_name = OrganizationService._generate_collection_name(data.organization_name)
        
        # Create organization document
        organization_doc = {
            "name": data.organization_name,
            "collection_name": collection_name,
            "created_at": datetime.utcnow(),
            "updated_at": None,
            "is_active": True,
        }
        
        # Insert organization
        org_result = await db.organizations.insert_one(organization_doc)
        org_id = org_result.inserted_id
        
        # Create admin user document
        admin_doc = {
            "email": data.email,
            "password_hash": security_service.get_password_hash(data.password),
            "organization_id": org_id,
            "organization_name": data.organization_name,
            "role": "admin",
            "created_at": datetime.utcnow(),
            "is_active": True,
        }
        
        # Insert admin user
        admin_result = await db.admin_users.insert_one(admin_doc)
        
        # Update organization with admin reference
        await db.organizations.update_one(
            {"_id": org_id},
            {"$set": {"admin_id": admin_result.inserted_id, "admin_email": data.email}}
        )
        
        # Create dynamic collection for the organization
        await DatabaseManager.create_organization_collection(collection_name)
        
        logger.info(f"Created organization: {data.organization_name}")
        
        # Return organization data
        return {
            "id": str(org_id),
            "name": data.organization_name,
            "collection_name": collection_name,
            "admin_email": data.email,
            "created_at": organization_doc["created_at"],
            "updated_at": None,
        }
    
    @staticmethod
    async def update_organization(
        current_org_name: str, 
        data: OrganizationUpdate,
        admin_id: str
    ) -> Dict[str, Any]:
        """
        Update an organization.
        
        Args:
            current_org_name: Current organization name
            data: Update data
            admin_id: ID of the admin making the update
            
        Returns:
            Dict: Updated organization data
            
        Raises:
            ValueError: If organization not found or new name already exists
        """
        db = DatabaseManager.get_master_db()
        
        # Get current organization
        current_org = await db.organizations.find_one({"name": current_org_name.lower()})
        if not current_org:
            raise ValueError(f"Organization '{current_org_name}' not found")
        
        # Verify admin belongs to this organization
        admin = await db.admin_users.find_one({"_id": ObjectId(admin_id)})
        if not admin or str(admin.get("organization_id")) != str(current_org["_id"]):
            raise ValueError("Unauthorized: Admin does not belong to this organization")
        
        # Check if new name already exists (if name is being changed)
        if data.organization_name.lower() != current_org_name.lower():
            existing = await db.organizations.find_one({"name": data.organization_name.lower()})
            if existing:
                raise ValueError(f"Organization '{data.organization_name}' already exists")
        
        # Prepare update data
        update_data = {
            "name": data.organization_name,
            "updated_at": datetime.utcnow(),
        }
        
        # Generate new collection name if name changed
        old_collection_name = current_org["collection_name"]
        new_collection_name = OrganizationService._generate_collection_name(data.organization_name)
        
        if old_collection_name != new_collection_name:
            # Rename the collection
            await DatabaseManager.rename_collection(old_collection_name, new_collection_name)
            update_data["collection_name"] = new_collection_name
        
        # Update organization
        await db.organizations.update_one(
            {"_id": current_org["_id"]},
            {"$set": update_data}
        )
        
        # Update admin user if email/password provided
        admin_update = {"organization_name": data.organization_name}
        if data.email:
            # Check if new email already exists
            existing_email = await db.admin_users.find_one({
                "email": data.email,
                "_id": {"$ne": ObjectId(admin_id)}
            })
            if existing_email:
                raise ValueError(f"Email '{data.email}' is already in use")
            admin_update["email"] = data.email
            update_data["admin_email"] = data.email
            
        if data.password:
            admin_update["password_hash"] = security_service.get_password_hash(data.password)
        
        await db.admin_users.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": admin_update}
        )
        
        # If email was updated, also update it in organization
        if data.email:
            await db.organizations.update_one(
                {"_id": current_org["_id"]},
                {"$set": {"admin_email": data.email}}
            )
        
        logger.info(f"Updated organization: {current_org_name} -> {data.organization_name}")
        
        # Get updated organization
        updated_org = await db.organizations.find_one({"_id": current_org["_id"]})
        
        return {
            "id": str(updated_org["_id"]),
            "name": updated_org["name"],
            "collection_name": updated_org["collection_name"],
            "admin_email": updated_org.get("admin_email", data.email or admin["email"]),
            "created_at": updated_org["created_at"],
            "updated_at": updated_org["updated_at"],
        }
    
    @staticmethod
    async def delete_organization(org_name: str, admin_id: str) -> bool:
        """
        Delete an organization and its associated data.
        
        Args:
            org_name: Organization name to delete
            admin_id: ID of the admin making the request
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If organization not found or unauthorized
        """
        db = DatabaseManager.get_master_db()
        
        # Get organization
        organization = await db.organizations.find_one({"name": org_name.lower()})
        if not organization:
            raise ValueError(f"Organization '{org_name}' not found")
        
        # Verify admin belongs to this organization
        admin = await db.admin_users.find_one({"_id": ObjectId(admin_id)})
        if not admin or str(admin.get("organization_id")) != str(organization["_id"]):
            raise ValueError("Unauthorized: Admin does not belong to this organization")
        
        # Delete the organization's collection
        await DatabaseManager.delete_organization_collection(organization["collection_name"])
        
        # Delete admin users associated with the organization
        await db.admin_users.delete_many({"organization_id": organization["_id"]})
        
        # Delete the organization
        await db.organizations.delete_one({"_id": organization["_id"]})
        
        logger.info(f"Deleted organization: {org_name}")
        
        return True


# Create a singleton instance
organization_service = OrganizationService()
