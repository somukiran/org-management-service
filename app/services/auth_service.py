"""
Authentication Service Module
Handles admin authentication and token operations.
"""

from datetime import timedelta
from typing import Optional, Dict, Any
from bson import ObjectId
import logging

from app.db.database import DatabaseManager
from app.core.security import security_service
from app.core.config import settings
from app.schemas import AdminLogin, Token, TokenData

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication operations.
    Handles admin login and token management.
    """
    
    @staticmethod
    async def get_admin_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an admin user by email.
        
        Args:
            email: Admin email address
            
        Returns:
            Optional[Dict]: Admin data if found, None otherwise
        """
        db = DatabaseManager.get_master_db()
        admin = await db.admin_users.find_one({"email": email})
        return admin
    
    @staticmethod
    async def get_admin_by_id(admin_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an admin user by ID.
        
        Args:
            admin_id: Admin user ID
            
        Returns:
            Optional[Dict]: Admin data if found, None otherwise
        """
        db = DatabaseManager.get_master_db()
        admin = await db.admin_users.find_one({"_id": ObjectId(admin_id)})
        return admin
    
    @staticmethod
    async def authenticate_admin(email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate an admin user with email and password.
        
        Args:
            email: Admin email
            password: Plain text password
            
        Returns:
            Optional[Dict]: Admin data if authentication successful, None otherwise
        """
        admin = await AuthService.get_admin_by_email(email)
        
        if not admin:
            logger.warning(f"Authentication failed: Admin not found for email {email}")
            return None
        
        if not admin.get("is_active", True):
            logger.warning(f"Authentication failed: Admin account is inactive for email {email}")
            return None
        
        if not security_service.verify_password(password, admin["password_hash"]):
            logger.warning(f"Authentication failed: Invalid password for email {email}")
            return None
        
        logger.info(f"Admin authenticated successfully: {email}")
        return admin
    
    @staticmethod
    async def login(data: AdminLogin) -> Optional[Token]:
        """
        Process admin login and generate JWT token.
        
        Args:
            data: Login credentials
            
        Returns:
            Optional[Token]: JWT token if login successful, None otherwise
        """
        admin = await AuthService.authenticate_admin(data.email, data.password)
        
        if not admin:
            return None
        
        # Get organization details
        db = DatabaseManager.get_master_db()
        organization = await db.organizations.find_one({"_id": admin["organization_id"]})
        
        if not organization:
            logger.error(f"Organization not found for admin {data.email}")
            return None
        
        # Create token payload
        token_data = {
            "sub": str(admin["_id"]),  # Subject (admin ID)
            "email": admin["email"],
            "organization_id": str(admin["organization_id"]),
            "organization_name": organization["name"],
            "role": admin.get("role", "admin"),
        }
        
        # Generate access token
        access_token = security_service.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        logger.info(f"Token generated for admin: {data.email}")
        
        return Token(access_token=access_token, token_type="bearer")
    
    @staticmethod
    async def validate_token(token: str) -> Optional[TokenData]:
        """
        Validate a JWT token and return token data.
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[TokenData]: Decoded token data if valid, None otherwise
        """
        try:
            payload = security_service.decode_token(token)
            
            admin_id = payload.get("sub")
            if not admin_id:
                return None
            
            # Verify admin still exists and is active
            admin = await AuthService.get_admin_by_id(admin_id)
            if not admin or not admin.get("is_active", True):
                return None
            
            return TokenData(
                admin_id=admin_id,
                email=payload.get("email"),
                organization_id=payload.get("organization_id"),
                organization_name=payload.get("organization_name"),
            )
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None


# Create a singleton instance
auth_service = AuthService()
