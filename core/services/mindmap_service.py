import logging
from sqlalchemy.ext.asyncio import AsyncSession

from llm.orchestrator import LLMOrchestrator
from utils.mindmap_processor import MindmapProcessor
from .logging_service import LoggingService
from infrastructure.storage.gcs_client import GCSClient

logger = logging.getLogger(__name__)


class MindmapService:
    """Core service for mindmap generation."""

    def __init__(self):
        self.orchestrator = LLMOrchestrator()
        self.processor = MindmapProcessor()
        self.logging_service = LoggingService()
        self.gcs_client = GCSClient()

    async def generate_mindmap(self, user_query: str, db: AsyncSession) -> dict:
        """
        Generate a mindmap based on user query with retry logic for depth.
        
        Args:
            user_query: The user's input query
            db: Database session for logging
            
        Returns:
            Processed mindmap data
        """
        message = ""
        result = None
        max_attempts = 3

        for attempt in range(max_attempts):
            query = user_query + message
            result = await self.orchestrator.generate_mindmap(query)
            depth = self.processor.count_depth(result.get("data", {}))

            if depth > 1:
                # Process the mindmap
                processed = self.processor.process_mindmap(result)

                # Save to GCS (async)
                await self._save_result_to_gcs(processed)

                # Log to database
                await self.logging_service.log_query(
                    db=db,
                    user_query=user_query,
                    result=result,
                    depth=depth,
                    success=True
                )

                return processed

            message = " Please provide a more detailed and structured mindmap with deeper hierarchy."

        # Fallback - process whatever we got
        processed = self.processor.process_mindmap(result)
        
        # Log the fallback result
        await self.logging_service.log_query(
            db=db,
            user_query=user_query,
            result=result,
            depth=self.processor.count_depth(result.get("data", {})),
            success=False
        )

        return processed

    async def _save_result_to_gcs(self, processed_result: dict) -> None:
        """Save the result to GCS asynchronously."""
        try:
            from datetime import datetime
            filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await self.gcs_client.upload_json(processed_result, filename)
        except Exception as e:
            logger.error(f"Failed to save result to GCS: {e}")
            # Don't fail the main operation for storage issues