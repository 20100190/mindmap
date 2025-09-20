from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from ..domain.mindmap import Mindmap, MindmapMeta, MindmapNode


class QueryRequest(BaseModel):
    """Request model for mindmap queries."""
    
    query: str = Field(..., description="The user's query for mindmap generation")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Learn Python programming"
            }
        }


class QueryResponse(BaseModel):
    """Response model for mindmap queries."""
    
    meta: Dict[str, Any] = Field(..., description="Mindmap metadata")
    format: str = Field(..., description="Format of the mindmap data")
    data: Dict[str, Any] = Field(..., description="Mindmap data structure")
    
    @classmethod
    def from_mindmap(cls, mindmap: Mindmap) -> 'QueryResponse':
        """Create response from domain mindmap object."""
        return cls(
            meta=mindmap.meta.dict(),
            format=mindmap.format,
            data=mindmap.data.dict()
        )
    
    class Config:
        schema_extra = {
            "example": {
                "meta": {
                    "name": "Python Programming",
                    "author": "System",
                    "version": "1.0"
                },
                "format": "node_tree",
                "data": {
                    "id": "root",
                    "topic": "Python Programming",
                    "children": [],
                    "expanded": True
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mindmap-api"
            }
        }