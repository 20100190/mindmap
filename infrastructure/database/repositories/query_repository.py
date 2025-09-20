import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..models import QueryLog

logger = logging.getLogger(__name__)


class QueryRepository:
    """Repository for query log database operations."""

    async def create_query_log(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        query_text: str,
        used_functions: str,
        response_length: int,
        mindmap_depth: int,
        error_flag: bool = False
    ) -> QueryLog:
        """
        Create a new query log entry.
        
        Args:
            db: Database session
            user_id: Optional user identifier
            query_text: The original query text
            used_functions: String representation of functions used
            response_length: Length of the response
            mindmap_depth: Depth of the generated mindmap
            error_flag: Whether an error occurred
            
        Returns:
            Created QueryLog instance
        """
        try:
            log_entry = QueryLog(
                user_id=user_id,
                query_text=query_text,
                used_functions=used_functions,
                response_length=response_length,
                mindmap_depth=mindmap_depth,
                error_flag=error_flag
            )
            
            db.add(log_entry)
            await db.commit()
            await db.refresh(log_entry)
            
            logger.info(f"Query log created with ID: {log_entry.id}")
            return log_entry
            
        except Exception as e:
            logger.error(f"Failed to create query log: {e}")
            await db.rollback()
            raise

    async def get_query_log_by_id(self, db: AsyncSession, log_id: str) -> Optional[QueryLog]:
        """Get a query log by ID."""
        try:
            result = await db.execute(select(QueryLog).where(QueryLog.id == log_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get query log {log_id}: {e}")
            return None

    async def get_query_logs_by_user(
        self, 
        db: AsyncSession, 
        user_id: str, 
        limit: int = 50
    ) -> List[QueryLog]:
        """Get query logs for a specific user."""
        try:
            result = await db.execute(
                select(QueryLog)
                .where(QueryLog.user_id == user_id)
                .order_by(desc(QueryLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get query logs for user {user_id}: {e}")
            return []

    async def get_recent_query_logs(self, db: AsyncSession, limit: int = 100) -> List[QueryLog]:
        """Get recent query logs across all users."""
        try:
            result = await db.execute(
                select(QueryLog)
                .order_by(desc(QueryLog.created_at))
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get recent query logs: {e}")
            return []