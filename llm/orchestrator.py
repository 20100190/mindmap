from .llm_client import LLMClient
from jsonschema import validate
from . import schema
from typing import Any, Dict, Optional
import jsonschema
import logging
logger = logging.getLogger(__name__)

expected_schema = schema.expected_schema_mindmap_query

class LLMOrchestrator:
    def __init__(self, 
                 expected_schema: dict = expected_schema, 
                 llm_client:LLMClient = LLMClient()):
        self.llm_client = llm_client
        self.expected_schema = expected_schema
    
    def validate_json_structure(self, response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate JSON response structure"""
        try:
            validate(instance=response, schema=self.expected_schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            error_message = f"JSON validation failed: {e.message}"
            return False, error_message
        except Exception as e:
            error_message = f"Validation error: {str(e)}"
            return False, error_message
    
    async def generate_mindmap(self, user_query: str) -> Dict[str, Any]:
        
        for attempt in range(self.llm_client.llm_config.max_retries):

            logger.info(f"Running loop {attempt} in orch with user query {user_query}")

            if attempt == 0:
                llm_response = await self.llm_client.process_query(
                    user_query = user_query
                )
                logger.info(f"Attempt 0 llm response {llm_response}")
            else:
                llm_response = await self.llm_client.process_query(
                    user_query=user_query, error_feedback=last_error
                )
    
            is_valid, validation_error = self.validate_json_structure(llm_response)

            logger.info(f"attemp valid sign {is_valid} and error {validation_error}")
                
            if is_valid:
                return llm_response
            else:
                last_error = validation_error
                
                if attempt == self.llm_client.llm_config.max_retries - 1:
                    # Last attempt failed, return error
                    return {
                        "status": "error",
                        "data": {"error": "Failed to generate valid response after retries"},
                        "function_calls": [],
                        "message": f"Validation failed: {validation_error}"
                    }