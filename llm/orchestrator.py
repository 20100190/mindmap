import time
import logging
from typing import Any, Dict, Optional

import jsonschema
from jsonschema import validate

from .llm_client import LLMClient
from . import schema
from logs_management.log_manager import log_error, log_performance, get_correlation_id

logger = logging.getLogger(__name__)

class LLMOrchestrator:
    """Orchestrator for LLM-based mindmap generation with validation."""
    
    def __init__(self, 
                 expected_schema: dict = None, 
                 llm_client: LLMClient = None):
        """
        Initialize the orchestrator.
        
        Args:
            expected_schema: JSON schema for response validation
            llm_client: LLM client instance
        """
        self.llm_client = llm_client or LLMClient()
        self.expected_schema = expected_schema or schema.expected_schema_mindmap_query
        
        logger.info("LLM Orchestrator initialized")
    
    def validate_json_structure(self, response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate JSON response structure against expected schema.
        
        Args:
            response: Response to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not response:
            return False, "Response is empty or None"
            
        try:
            validate(instance=response, schema=self.expected_schema)
            logger.debug("JSON validation successful")
            return True, None
            
        except jsonschema.exceptions.ValidationError as e:
            error_message = f"JSON schema validation failed: {e.message} at path: {'.'.join(str(p) for p in e.absolute_path)}"
            logger.warning(f"Validation error: {error_message}")
            return False, error_message
            
        except jsonschema.exceptions.SchemaError as e:
            error_message = f"Schema definition error: {str(e)}"
            logger.error(f"Schema error: {error_message}")
            return False, error_message
            
        except Exception as e:
            error_message = f"Unexpected validation error: {str(e)}"
            logger.error(f"Validation error: {error_message}")
            return False, error_message
    
    async def generate_mindmap(self, user_query: str) -> Dict[str, Any]:
        """
        Generate mindmap with retry logic and validation.
        
        Args:
            user_query: User's query for mindmap generation
            
        Returns:
            Dict containing the generated mindmap or error information
        """
        if not user_query or not user_query.strip():
            return {
                "status": "error",
                "data": {"error": "Empty query provided"},
                "function_calls": [],
                "message": "Query cannot be empty"
            }
        
        start_time = time.time()
        correlation_id = get_correlation_id()
        max_retries = self.llm_client.llm_config.max_retries
        last_error = None
        
        logger.info(
            f"Starting mindmap generation",
            extra={'extra_data': {
                'query_length': len(user_query),
                'max_retries': max_retries,
                'correlation_id': correlation_id
            }}
        )
        
        try:
            for attempt in range(max_retries):
                logger.info(
                    f"Orchestrator attempt {attempt + 1}/{max_retries}",
                    extra={'extra_data': {
                        'attempt': attempt + 1,
                        'has_previous_error': bool(last_error),
                        'correlation_id': correlation_id
                    }}
                )

                try:
                    # Process query with LLM
                    if attempt == 0:
                        llm_response = await self.llm_client.process_query(user_query=user_query)
                    else:
                        llm_response = await self.llm_client.process_query(
                            user_query=user_query, 
                            error_feedback=last_error
                        )
                    
                    if not llm_response:
                        raise ValueError("LLM client returned empty response")
                    
                    logger.debug(
                        f"LLM response received",
                        extra={'extra_data': {
                            'attempt': attempt + 1,
                            'response_status': llm_response.get('status', 'unknown'),
                            'correlation_id': correlation_id
                        }}
                    )
                    
                    # Validate response structure
                    is_valid, validation_error = self.validate_json_structure(llm_response)

                    logger.info(
                        f"Attempt {attempt + 1} validation result: {is_valid}",
                        extra={'extra_data': {
                            'attempt': attempt + 1,
                            'is_valid': is_valid,
                            'validation_error': validation_error,
                            'correlation_id': correlation_id
                        }}
                    )
                        
                    if is_valid:
                        end_time = time.time()
                        log_performance(
                            logger,
                            "mindmap_generation",
                            start_time,
                            end_time,
                            attempts=attempt + 1,
                            success=True,
                            correlation_id=correlation_id
                        )
                        
                        logger.info(f"Mindmap generation successful after {attempt + 1} attempts")
                        return llm_response
                        
                    else:
                        last_error = validation_error
                        
                        if attempt == max_retries - 1:
                            # Last attempt failed, return error
                            logger.error(
                                f"All attempts exhausted, final validation error: {validation_error}"
                            )
                            break
                        
                        logger.warning(f"Attempt {attempt + 1} failed validation, retrying...")
                        
                except Exception as e:
                    error_msg = f"Attempt {attempt + 1} failed with exception: {str(e)}"
                    logger.warning(error_msg)
                    last_error = str(e)
                    
                    if attempt == max_retries - 1:
                        # Last attempt, log the error
                        log_error(logger, e, {
                            'operation': 'mindmap_generation_attempt',
                            'attempt': attempt + 1,
                            'correlation_id': correlation_id
                        })
                        break
            
            # All attempts failed
            end_time = time.time()
            log_performance(
                logger,
                "mindmap_generation",
                start_time,
                end_time,
                attempts=max_retries,
                success=False,
                correlation_id=correlation_id
            )
            
            error_response = {
                "status": "error",
                "data": {"error": "Failed to generate valid response after retries"},
                "function_calls": [],
                "message": f"Validation failed after {max_retries} attempts. Last error: {last_error}"
            }
            
            logger.error(
                f"Mindmap generation failed after {max_retries} attempts",
                extra={'extra_data': {
                    'last_error': last_error,
                    'correlation_id': correlation_id
                }}
            )
            
            return error_response
            
        except Exception as e:
            # Unexpected error during generation
            end_time = time.time()
            log_error(logger, e, {
                'operation': 'mindmap_generation',
                'query_length': len(user_query),
                'processing_time': end_time - start_time,
                'correlation_id': correlation_id
            })
            
            return {
                "status": "error",
                "data": {"error": "Unexpected error during mindmap generation"},
                "function_calls": [],
                "message": f"Unexpected error: {str(e)}"
            }