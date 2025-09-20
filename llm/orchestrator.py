import logging
from typing import Any, Dict

from .client import LLMClient
from .validation.validator import ResponseValidator
from core.config import config

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Orchestrates LLM interactions with validation and retry logic.
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.validator = ResponseValidator()
        self.max_retries = config.llm.max_retries

    async def generate_mindmap(self, user_query: str) -> Dict[str, Any]:
        """
        Generate a mindmap with validation and retry logic.
        
        Args:
            user_query: The user's query
            
        Returns:
            Validated LLM response
        """
        last_error = None

        for attempt in range(self.max_retries):
            logger.info(f"Mindmap generation attempt {attempt + 1} for query: {user_query[:50]}...")

            try:
                if attempt == 0:
                    llm_response = await self.llm_client.process_query(user_query)
                else:
                    llm_response = await self.llm_client.process_query(
                        user_query=user_query, 
                        error_feedback=last_error
                    )

                logger.debug(f"LLM response received: {llm_response}")

                # Validate the response
                is_valid, validation_error = self.validator.validate_mindmap_response(llm_response)

                logger.info(f"Validation result - Valid: {is_valid}, Error: {validation_error}")

                if is_valid:
                    return llm_response
                else:
                    last_error = validation_error

            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {e}")
                last_error = f"Processing error: {str(e)}"

            if attempt == self.max_retries - 1:
                # Last attempt failed, return error response
                logger.error(f"All attempts failed. Last error: {last_error}")
                return self._create_error_response(last_error)

        # This shouldn't be reached, but just in case
        return self._create_error_response("Unknown error occurred")

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "status": "error",
            "data": {"error": "Failed to generate valid response after retries"},
            "function_calls": [],
            "message": f"Validation failed: {error_message}"
        }