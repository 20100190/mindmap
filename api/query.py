import time
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from services import query_service
from logs_management.log_manager import log_error, log_performance, get_correlation_id

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Query text for mindmap generation")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()

class QueryResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    correlation_id: str
    processing_time: float

router = APIRouter(tags=["Query"])

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest, 
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a mindmap based on the provided query.
    
    Args:
        request: Query request containing the query text
        http_request: HTTP request object for correlation ID
        db: Database session
    
    Returns:
        QueryResponse: Generated mindmap data with metadata
    """
    start_time = time.time()
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    logger.info(
        f"Query request received",
        extra={'extra_data': {
            'query_length': len(request.query),
            'correlation_id': correlation_id
        }}
    )
    
    try:
        # Validate database connection
        if db is None:
            raise HTTPException(
                status_code=500,
                detail="Database connection unavailable"
            )
        
        # Process query
        result = await query_service.handle_query(request.query, db)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Log performance
        log_performance(
            logger,
            "query_processing",
            start_time,
            end_time,
            query_length=len(request.query),
            correlation_id=correlation_id
        )
        
        logger.info(
            f"Query processed successfully",
            extra={'extra_data': {
                'processing_time': processing_time,
                'correlation_id': correlation_id,
                'result_status': result.get('status', 'unknown')
            }}
        )
        
        return QueryResponse(
            status="success",
            data=result,
            correlation_id=correlation_id,
            processing_time=processing_time
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        logger.warning(f"Invalid query request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid query: {str(e)}"
        )
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        
        log_error(logger, e, {
            'operation': 'query_processing',
            'query_length': len(request.query),
            'processing_time': processing_time,
            'correlation_id': correlation_id
        })
        
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while processing query"
        )