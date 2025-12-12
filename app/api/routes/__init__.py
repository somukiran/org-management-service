"""
Routes module initialization.
"""

from app.api.routes.organization import router as organization_router
from app.api.routes.admin import router as admin_router

__all__ = ["organization_router", "admin_router"]
