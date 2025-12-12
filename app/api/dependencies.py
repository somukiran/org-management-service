"""
API Dependencies Module
Provides FastAPI dependencies for authentication and authorization.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.services.auth_service import auth_service
from app.schemas import TokenData

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency to get the current authenticated admin.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        TokenData: The authenticated admin's token data
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = await auth_service.validate_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_optional_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[TokenData]:
    """
    FastAPI dependency to optionally get the current authenticated admin.
    Returns None if not authenticated (doesn't raise an exception).
    
    Args:
        credentials: Optional HTTP Bearer credentials
        
    Returns:
        Optional[TokenData]: The authenticated admin's token data or None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return await auth_service.validate_token(token)
