import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .mindmap_service import MindmapService

logger = logging.getLogger(__name__)


class QueryService:
    """Service for handling different types of queries."""

    def __init__(self):
        self.mindmap_service = MindmapService()

    async def process_query(self, query: str, query_type: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Process different types of queries.
        
        Args:
            query: The user query
            query_type: Type of query (e.g., 'mindmap', 'search', etc.)
            db: Database session
            
        Returns:
            Processed query result
        """
        if query_type == "mindmap":
            return await self.mindmap_service.generate_mindmap(query, db)
        else:
            raise ValueError(f"Unsupported query type: {query_type}")

    async def handle_mindmap_query(self, query: str, db: AsyncSession) -> Dict[str, Any]:
        """Handle mindmap-specific queries."""
        return await self.mindmap_service.generate_mindmap(query, db)