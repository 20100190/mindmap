import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from llm.orchestrator import LLMOrchestrator
from util import process_json_mindmap
from db.models import QueryLog
from util.gcs_util import upload_result_to_gcs
from logs_management.log_manager import log_error, log_performance, get_correlation_id

logger = logging.getLogger(__name__)

class QueryServiceConfig:
    """Configuration for query service."""
    MAX_RETRIES = int(os.getenv("QUERY_MAX_RETRIES", "3"))
    MIN_DEPTH_THRESHOLD = int(os.getenv("MIN_DEPTH_THRESHOLD", "1"))
    SAVE_TO_GCS = os.getenv("SAVE_TO_GCS", "true").lower() == "true"
    LOG_TO_DB = os.getenv("LOG_TO_DB", "true").lower() == "true"

config = QueryServiceConfig()

async def handle_query(user_query: str, db: AsyncSession) -> Dict[str, Any]:
    """
    Handle mindmap generation query with proper error handling and logging.
    
    Args:
        user_query: User's query text
        db: Database session
        
    Returns:
        Dict containing the processed mindmap result
        
    Raises:
        ValueError: If query is invalid
        RuntimeError: If processing fails after retries
    """
    start_time = time.time()
    correlation_id = get_correlation_id()
    
    # Validate input
    if not user_query or not user_query.strip():
        raise ValueError("Query cannot be empty")
    
    if len(user_query.strip()) > 2000:
        raise ValueError("Query too long (max 2000 characters)")
    
    user_query = user_query.strip()
    
    logger.info(
        f"Starting query processing",
        extra={'extra_data': {
            'query_length': len(user_query),
            'max_retries': config.MAX_RETRIES,
            'correlation_id': correlation_id
        }}
    )
    
    try:
        orchestrator = LLMOrchestrator()
        message = ""
        result = None
        last_error = None

        for try_count in range(config.MAX_RETRIES):
            logger.info(
                f"Query attempt {try_count + 1}/{config.MAX_RETRIES}",
                extra={'extra_data': {
                    'attempt': try_count + 1,
                    'retry_message': message.strip() if message else None,
                    'correlation_id': correlation_id
                }}
            )
            
            try:
                query = user_query + message
                result = await orchestrator.generate_mindmap(query)
                
                if not result:
                    raise RuntimeError("No result returned from orchestrator")
                
                # Check if result has error status
                if result.get("status") == "error":
                    logger.warning(f"Orchestrator returned error: {result.get('message', 'Unknown error')}")
                    last_error = result.get('message', 'Unknown error from orchestrator')
                    continue
                
                depth = process_json_mindmap.count_depth(result.get("data", {}))
                
                logger.info(
                    f"Mindmap generated with depth {depth}",
                    extra={'extra_data': {
                        'depth': depth,
                        'min_threshold': config.MIN_DEPTH_THRESHOLD,
                        'attempt': try_count + 1,
                        'correlation_id': correlation_id
                    }}
                )

                if depth > config.MIN_DEPTH_THRESHOLD:
                    # Process the successful result
                    processed = await _process_successful_result(
                        result, user_query, depth, db
                    )
                    
                    end_time = time.time()
                    log_performance(
                        logger,
                        "query_handling",
                        start_time,
                        end_time,
                        attempts=try_count + 1,
                        depth=depth,
                        success=True,
                        correlation_id=correlation_id
                    )
                    
                    return processed

                # Depth too shallow, try again
                message = " Please provide a more detailed and structured mindmap with deeper hierarchy and more comprehensive coverage."
                
            except Exception as e:
                logger.warning(
                    f"Attempt {try_count + 1} failed: {str(e)}",
                    extra={'extra_data': {
                        'attempt': try_count + 1,
                        'error_type': type(e).__name__,
                        'correlation_id': correlation_id
                    }}
                )
                last_error = str(e)
                
                # If this is the last attempt, don't continue
                if try_count == config.MAX_RETRIES - 1:
                    break
                
                # Add error feedback for retry
                message = f" The previous attempt failed with error: {str(e)}. Please provide a more detailed response."

        # All retries exhausted, handle fallback
        logger.warning(
            f"All {config.MAX_RETRIES} attempts exhausted",
            extra={'extra_data': {
                'last_error': last_error,
                'correlation_id': correlation_id
            }}
        )
        
        # Try to process whatever we have as fallback
        if result:
            try:
                fallback_processed = process_json_mindmap.process_mindmap(result)
                
                # Log the fallback usage
                await _log_query_result(
                    user_query, result, db, 
                    error_flag=True, 
                    error_message=f"Used fallback after {config.MAX_RETRIES} attempts: {last_error}"
                )
                
                logger.warning("Returned fallback result after exhausting retries")
                return fallback_processed
                
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {str(fallback_error)}")
                
        # Complete failure
        end_time = time.time()
        log_performance(
            logger,
            "query_handling",
            start_time,
            end_time,
            attempts=config.MAX_RETRIES,
            success=False,
            correlation_id=correlation_id
        )
        
        raise RuntimeError(f"Failed to generate mindmap after {config.MAX_RETRIES} attempts. Last error: {last_error}")
        
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        end_time = time.time()
        log_error(logger, e, {
            'operation': 'query_handling',
            'query_length': len(user_query),
            'processing_time': end_time - start_time,
            'correlation_id': correlation_id
        })
        raise RuntimeError(f"Query processing failed: {str(e)}") from e

async def _process_successful_result(
    result: Dict[str, Any], 
    user_query: str, 
    depth: int, 
    db: AsyncSession
) -> Dict[str, Any]:
    """Process a successful mindmap result."""
    correlation_id = get_correlation_id()
    
    try:
        processed = process_json_mindmap.process_mindmap(result)
        
        # Save to GCS if enabled
        if config.SAVE_TO_GCS:
            await _save_to_gcs(processed, correlation_id)
        
        # Log to database if enabled
        if config.LOG_TO_DB:
            await _log_query_result(user_query, result, db, depth=depth)
        
        return processed
        
    except Exception as e:
        logger.error(f"Error processing successful result: {str(e)}")
        # Still return the processed result even if logging fails
        try:
            return process_json_mindmap.process_mindmap(result)
        except Exception as process_error:
            log_error(logger, process_error, {
                'operation': 'result_processing',
                'correlation_id': correlation_id
            })
            raise

async def _save_to_gcs(processed_result: Dict[str, Any], correlation_id: str) -> None:
    """Save result to GCS with error handling."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f"query_result_{timestamp}_{correlation_id[:8]}.json"
        
        upload_result_to_gcs(processed_result, json_filename)
        
        logger.info(
            f"Result saved to GCS: {json_filename}",
            extra={'extra_data': {
                'filename': json_filename,
                'correlation_id': correlation_id
            }}
        )
    except Exception as e:
        # Log but don't fail the request for GCS errors
        logger.error(f"Failed to save to GCS: {str(e)}")

async def _log_query_result(
    user_query: str, 
    result: Dict[str, Any], 
    db: AsyncSession,
    depth: int = 0,
    error_flag: bool = False,
    error_message: str = None
) -> None:
    """Log query result to database with error handling."""
    try:
        log_entry = QueryLog(
            user_id=None,  # Could be extracted from authentication context
            query_text=user_query,
            used_functions=str(result.get('function_calls', [])),
            response_length=len(str(result)),
            mindmap_depth=depth,
            error_flag=error_flag,
        )
        
        db.add(log_entry)
        await db.commit()
        
        logger.info(
            f"Query result logged to database",
            extra={'extra_data': {
                'log_id': str(log_entry.id),
                'error_flag': error_flag,
                'depth': depth
            }}
        )
        
    except SQLAlchemyError as e:
        logger.error(f"Database logging failed: {str(e)}")
        # Try to rollback
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Rollback also failed: {str(rollback_error)}")
    except Exception as e:
        logger.error(f"Unexpected error during database logging: {str(e)}")