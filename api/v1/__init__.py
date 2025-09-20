from fastapi import APIRouter
from .query import router as query_router
from .health import router as health_router

# Create main v1 router
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(query_router, tags=["queries"])
v1_router.include_router(health_router, tags=["health"])