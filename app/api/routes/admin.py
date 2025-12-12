"""
Admin/Authentication Routes Module
Defines API endpoints for admin authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas import (
    AdminLogin,
    Token,
    SuccessResponse,
    ErrorResponse,
    TokenData,
)
from app.services.auth_service import auth_service
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def admin_login(data: AdminLogin):
    """
    Authenticate an admin user and receive a JWT token.
    
    **Request Body:**
    - `email`: Admin email address
    - `password`: Admin password
    
    **Returns:**
    - `access_token`: JWT token for authentication
    - `token_type`: Token type (always "bearer")
    
    **Token Payload Contains:**
    - Admin identification (admin_id)
    - Organization identifier (organization_id)
    - Organization name
    - Admin role
    
    **Usage:**
    Include the token in subsequent requests using the Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    token = await auth_service.login(data)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


@router.get(
    "/me",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Current admin info"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_admin_info(current_admin: TokenData = Depends(get_current_admin)):
    """
    Get the current authenticated admin's information.
    
    **Requires Authentication:** Yes (JWT Bearer token)
    
    **Returns:**
    - Admin ID
    - Email
    - Organization ID
    - Organization name
    """
    return SuccessResponse(
        success=True,
        message="Admin information retrieved successfully",
        data={
            "admin": {
                "id": current_admin.admin_id,
                "email": current_admin.email,
                "organization_id": current_admin.organization_id,
                "organization_name": current_admin.organization_name,
            }
        }
    )


@router.post(
    "/verify-token",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Token is valid"},
        401: {"model": ErrorResponse, "description": "Invalid token"},
    },
)
async def verify_token(current_admin: TokenData = Depends(get_current_admin)):
    """
    Verify if the current JWT token is valid.
    
    **Requires Authentication:** Yes (JWT Bearer token)
    
    **Returns:**
    - Confirmation that the token is valid
    - Admin and organization information
    """
    return SuccessResponse(
        success=True,
        message="Token is valid",
        data={
            "valid": True,
            "admin_id": current_admin.admin_id,
            "organization_id": current_admin.organization_id,
        }
    )
