from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from api.dependencies import get_db
from models.api.query import QueryRequest, QueryResponse
from core.services.mindmap_service import MindmapService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest, 
    db: AsyncSession = Depends(get_db)
) -> QueryResponse:
    """Generate a mindmap based on user query."""
    mindmap_service = MindmapService()
    result = await mindmap_service.generate_mindmap(request.query, db)
    return QueryResponse(**result)