"""
Pydantic Schemas Module
Defines request and response models for API validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ==================== Organization Schemas ====================

class OrganizationCreate(BaseModel):
    """
    Schema for creating a new organization.
    """
    organization_name: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Unique name for the organization"
    )
    email: EmailStr = Field(
        ..., 
        description="Admin email address"
    )
    password: str = Field(
        ..., 
        min_length=8,
        description="Admin password (minimum 8 characters)"
    )
    
    @field_validator('organization_name')
    @classmethod
    def validate_organization_name(cls, v: str) -> str:
        """
        Validate organization name format.
        Only alphanumeric characters and underscores allowed.
        """
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError(
                'Organization name must start with a letter and contain only '
                'alphanumeric characters and underscores'
            )
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.
        """
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class OrganizationUpdate(BaseModel):
    """
    Schema for updating an organization.
    """
    organization_name: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="New name for the organization"
    )
    email: Optional[EmailStr] = Field(
        None, 
        description="New admin email address (optional)"
    )
    password: Optional[str] = Field(
        None, 
        min_length=8,
        description="New admin password (optional)"
    )
    
    @field_validator('organization_name')
    @classmethod
    def validate_organization_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError(
                'Organization name must start with a letter and contain only '
                'alphanumeric characters and underscores'
            )
        return v.lower()


class OrganizationResponse(BaseModel):
    """
    Schema for organization response.
    """
    id: str = Field(..., description="Organization ID")
    name: str = Field(..., description="Organization name")
    collection_name: str = Field(..., description="MongoDB collection name")
    admin_email: str = Field(..., description="Admin email address")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class OrganizationGetRequest(BaseModel):
    """
    Schema for getting organization by name.
    """
    organization_name: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Name of the organization to retrieve"
    )


class OrganizationDeleteRequest(BaseModel):
    """
    Schema for deleting an organization.
    """
    organization_name: str = Field(
        ..., 
        min_length=3, 
        max_length=50,
        description="Name of the organization to delete"
    )


# ==================== Admin/Auth Schemas ====================

class AdminLogin(BaseModel):
    """
    Schema for admin login request.
    """
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., description="Admin password")


class Token(BaseModel):
    """
    Schema for JWT token response.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """
    Schema for decoded token data.
    """
    admin_id: str = Field(..., description="Admin user ID")
    email: str = Field(..., description="Admin email")
    organization_id: str = Field(..., description="Organization ID")
    organization_name: str = Field(..., description="Organization name")


# ==================== Generic Response Schemas ====================

class SuccessResponse(BaseModel):
    """
    Generic success response schema.
    """
    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Additional data")


class ErrorResponse(BaseModel):
    """
    Generic error response schema.
    """
    success: bool = Field(default=False)
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
