from .llm_client import LLMClient
from . import schema
from typing import Any, Dict, Optional
import logging
from util.process_json_mindmap import validate_json_structure
logger = logging.getLogger(__name__)

expected_schema = schema.expected_schema_mindmap_query

class LLMOrchestrator:
    def __init__(self, llm_client:LLMClient = LLMClient()):
        self.llm_client = llm_client
    
    async def generate_mindmap(self, user_request) -> Dict[str, Any]:
        """
        Call LLM check response if invalid retry upto n times.
        user_query: User Question from API
        return: LLM response
        """
        user_query = user_request.user_query
        if not user_query or not user_query.strip():
            raise ValueError("User query cannot be empty")
        validation_error = None
        max_retries = self.llm_client.llm_config.max_retries
        try:
            for iter_count in range(max_retries):
                logger.info(f"Running loop process_query: {iter_count}/{max_retries} with query={user_query}, feedback={validation_error}")
                if iter_count==0:
                    llm_response = await self.llm_client.process_query(user_request)
                else:
                    llm_response = await self.llm_client.process_query(user_request, error_feedback=validation_error)
                logger.info(f"Got response from process_query iteration: {iter_count}: llm response: {llm_response}")
                
                if llm_response.main_response.get("status")=="error":
                    validation_error = "Can you please try again?"
                    continue

                if llm_response.main_response.get("mindmap")=="false":
                    return llm_response

                is_valid, validation_error = validate_json_structure(llm_response.main_response, expected_schema)
                logger.info(f"process_query Attempt={iter_count}: Respone valid check: {is_valid} Error: {validation_error}")
                if is_valid:
                    return llm_response 
            else:
                raise RuntimeError(f"Failed to generate valid mindmap after {max_retries} attempts. Last error: {validation_error}")
        except Exception as e:
            logger.exception(f"Uncaught exception from process_query. Error: {e}")
            raise