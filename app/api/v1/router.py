"""
API v1 Router.

Main router that includes all sub-routers.
"""
from fastapi import APIRouter
from app.api.v1 import contractors, auth, onboarding

# Create main v1 router
router = APIRouter()

# Include all sub-routers
router.include_router(auth.router)
router.include_router(contractors.router)
router.include_router(onboarding.router)

# Health check endpoint
@router.get("/health", tags=["Health"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
    }
