from fastapi import APIRouter
from .query import router as query_router
from .health import router as health_router
from .chat import router as home_page_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(query_router, tags=["query"])
v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(home_page_router)

__all__ = ["v1_router"]