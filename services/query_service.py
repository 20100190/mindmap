import os
from datetime import datetime
from typing import Dict, Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from llm.orchestrator import LLMOrchestrator
from util import process_json_mindmap

import logging
logger = logging.getLogger(__name__)

class QueryServiceConfig:
    """Configuration for query service."""
    MAX_RETRIES = int(os.getenv("QUERY_MAX_RETRIES", "3"))
    MIN_DEPTH_THRESHOLD = int(os.getenv("MIN_DEPTH_THRESHOLD", "1"))

config = QueryServiceConfig()

async def handle_query(user_request, correlation_id) -> Dict[str, Any]:
    """
    Handle mindmap generation query with proper error handling and logging.
    
    Args:
        request: User's request
        
    Returns:
        Dict containing the processed mindmap result
        
    Raises:
        ValueError: If query is invalid
        RuntimeError: If processing fails after retries
    """
    user_query = user_request.user_query
    if not user_query or not user_query.strip():
        logger.error("Got emmpty query.")
        raise ValueError("Query can not be empty.")

    orchestrator = LLMOrchestrator()
    message = ""
    last_error = None

    for try_count in range(config.MAX_RETRIES):
        logger.info( f"Query attempt for generate_mindmap: {try_count + 1}/{config.MAX_RETRIES}")
        try:
            user_request.user_query = user_query + message
            result = await orchestrator.generate_mindmap(user_request)
            #result = result.dict()

            if not result:
                raise RuntimeError("No Result from LLM Orchastrator")
            
            if result.main_response.get("status") == "error":
                logger.warning(f"Orchestrator returned error:")
                message = result.main_response.get("message", "Got error in last response. Please try again.")
                continue

            if result.main_response.get("mindmap") == "false":
                return  {
                        "message": result.main_response.get("message"),
                        "full_response": result.full_response,
                        "function_calls": result.function_calls,
                        "chat_log": result.chat_log
                }
                
            # check mind map depth
            depth = process_json_mindmap.count_depth(result.main_response.get("mindmap-data", {}))
            logger.info(f"Mindmap generated with depth {depth} for try={try_count+1}")
    
            if depth > config.MIN_DEPTH_THRESHOLD or try_count==config.MAX_RETRIES-1:
                processed = process_json_mindmap.process_mindmap(result.main_response)
                return {
                    "mindmap": processed,
                    "message": result.main_response.get("message"),
                    "full_response": result.full_response,
                    "function_calls": result.function_calls,
                    "chat_log": result.chat_log
                }
            message = " Please provide a more detailed and structured mindmap with deeper hierarchy."
        except Exception as e:
            logger.error(f"Exception: {e}")
    raise RuntimeError(f"Failed to generate mindmap after {config.MAX_RETRIES} attempts. Last error: {last_error}")
