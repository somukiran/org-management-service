"""
Organization Routes Module
Defines API endpoints for organization management.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional

from app.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    SuccessResponse,
    ErrorResponse,
    TokenData,
)
from app.services.organization_service import organization_service
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/org", tags=["Organizations"])


@router.post(
    "/create",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Organization created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Organization already exists"},
    },
)
async def create_organization(data: OrganizationCreate):
    """
    Create a new organization with an admin user.
    
    This endpoint:
    - Validates that the organization name doesn't already exist
    - Creates a new MongoDB collection for the organization
    - Creates an admin user associated with the organization
    - Stores metadata in the Master Database
    
    **Request Body:**
    - `organization_name`: Unique name for the organization (3-50 chars, alphanumeric + underscore)
    - `email`: Admin email address
    - `password`: Admin password (min 8 chars, must contain uppercase, lowercase, and digit)
    """
    try:
        result = await organization_service.create_organization(data)
        
        return SuccessResponse(
            success=True,
            message=f"Organization '{data.organization_name}' created successfully",
            data={
                "organization": {
                    "id": result["id"],
                    "name": result["name"],
                    "collection_name": result["collection_name"],
                    "admin_email": result["admin_email"],
                    "created_at": result["created_at"].isoformat(),
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )


@router.get(
    "/get",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Organization found"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
async def get_organization(
    organization_name: str = Query(..., min_length=3, max_length=50, description="Organization name")
):
    """
    Get organization details by name.
    
    **Query Parameters:**
    - `organization_name`: The name of the organization to retrieve
    
    **Returns:**
    - Organization metadata from the Master Database
    """
    try:
        organization = await organization_service.get_organization_by_name(organization_name)
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{organization_name}' not found"
            )
        
        return SuccessResponse(
            success=True,
            message="Organization retrieved successfully",
            data={
                "organization": {
                    "id": str(organization["_id"]),
                    "name": organization["name"],
                    "collection_name": organization["collection_name"],
                    "admin_email": organization.get("admin_email"),
                    "created_at": organization["created_at"].isoformat(),
                    "updated_at": organization["updated_at"].isoformat() if organization.get("updated_at") else None,
                    "is_active": organization.get("is_active", True),
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organization: {str(e)}"
        )


@router.put(
    "/update",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Organization updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
        409: {"model": ErrorResponse, "description": "New organization name already exists"},
    },
)
async def update_organization(
    data: OrganizationUpdate,
    current_org_name: str = Query(..., min_length=3, max_length=50, description="Current organization name"),
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Update an organization's details.
    
    **Requires Authentication:** Yes (JWT Bearer token)
    
    This endpoint:
    - Validates that the new organization name doesn't already exist
    - Renames the MongoDB collection if the name changes
    - Syncs existing data to the new collection
    - Updates admin credentials if provided
    
    **Query Parameters:**
    - `current_org_name`: The current name of the organization
    
    **Request Body:**
    - `organization_name`: New name for the organization
    - `email`: New admin email (optional)
    - `password`: New admin password (optional)
    """
    try:
        result = await organization_service.update_organization(
            current_org_name=current_org_name,
            data=data,
            admin_id=current_admin.admin_id
        )
        
        return SuccessResponse(
            success=True,
            message=f"Organization updated successfully",
            data={
                "organization": {
                    "id": result["id"],
                    "name": result["name"],
                    "collection_name": result["collection_name"],
                    "admin_email": result["admin_email"],
                    "created_at": result["created_at"].isoformat(),
                    "updated_at": result["updated_at"].isoformat() if result.get("updated_at") else None,
                }
            }
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )


@router.delete(
    "/delete",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Organization deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Organization not found"},
    },
)
async def delete_organization(
    organization_name: str = Query(..., min_length=3, max_length=50, description="Organization name to delete"),
    current_admin: TokenData = Depends(get_current_admin),
):
    """
    Delete an organization and all associated data.
    
    **Requires Authentication:** Yes (JWT Bearer token)
    
    This endpoint:
    - Validates that the authenticated admin belongs to the organization
    - Deletes the organization's MongoDB collection
    - Removes all admin users associated with the organization
    - Removes the organization from the Master Database
    
    **Query Parameters:**
    - `organization_name`: The name of the organization to delete
    
    **Warning:** This action is irreversible!
    """
    try:
        await organization_service.delete_organization(
            org_name=organization_name,
            admin_id=current_admin.admin_id
        )
        
        return SuccessResponse(
            success=True,
            message=f"Organization '{organization_name}' deleted successfully",
            data=None
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )
