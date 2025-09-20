import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from infrastructure.database.repositories.query_repository import QueryRepository

logger = logging.getLogger(__name__)


class LoggingService:
    """Service for handling query logging."""

    def __init__(self):
        self.query_repo = QueryRepository()

    async def log_query(
        self,
        db: AsyncSession,
        user_query: str,
        result: dict,
        depth: int,
        success: bool,
        user_id: Optional[str] = None
    ) -> None:
        """
        Log query execution details to the database.
        
        Args:
            db: Database session
            user_query: Original user query
            result: LLM response
            depth: Mindmap depth achieved
            success: Whether the query was successful
            user_id: Optional user identifier
        """
        try:
            await self.query_repo.create_query_log(
                db=db,
                user_id=user_id,
                query_text=user_query,
                used_functions=str(result.get('function_calls', [])),
                response_length=len(str(result)),
                mindmap_depth=depth,
                error_flag=not success
            )
            logger.info(f"Query logged successfully for query: {user_query[:50]}...")
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            # Don't fail the main operation for logging issues