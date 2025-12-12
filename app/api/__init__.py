"""
API module initialization.
"""

from app.api.routes import organization_router, admin_router
from app.api.dependencies import get_current_admin, get_optional_admin

__all__ = [
    "organization_router",
    "admin_router",
    "get_current_admin",
    "get_optional_admin",
]
