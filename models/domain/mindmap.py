from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MindmapNode(BaseModel):
    """Domain model for a mindmap node."""
    
    id: str = Field(..., description="Unique identifier for the node")
    topic: str = Field(..., description="The topic/content of the node")
    children: List['MindmapNode'] = Field(default_factory=list, description="Child nodes")
    expanded: bool = Field(default=True, description="Whether the node is expanded")
    direction: Optional[str] = Field(default=None, description="Direction from parent (left/right)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "node_123",
                "topic": "Python Programming",
                "children": [
                    {
                        "id": "node_124",
                        "topic": "Variables",
                        "children": [],
                        "expanded": True,
                        "direction": "right"
                    }
                ],
                "expanded": True
            }
        }


class MindmapMeta(BaseModel):
    """Metadata for a mindmap."""
    
    name: str = Field(..., description="Name of the mindmap")
    author: str = Field(default="System", description="Author of the mindmap")
    version: str = Field(default="1.0", description="Version of the mindmap")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class Mindmap(BaseModel):
    """Complete mindmap domain model."""
    
    meta: MindmapMeta = Field(..., description="Mindmap metadata")
    format: str = Field(default="node_tree", description="Format of the mindmap data")
    data: MindmapNode = Field(..., description="Root node of the mindmap")
    
    def get_depth(self) -> int:
        """Calculate the depth of the mindmap."""
        return self._calculate_node_depth(self.data)
    
    def _calculate_node_depth(self, node: MindmapNode) -> int:
        """Recursively calculate node depth."""
        if not node.children:
            return 1
        return 1 + max(self._calculate_node_depth(child) for child in node.children)
    
    def get_total_nodes(self) -> int:
        """Count total number of nodes in the mindmap."""
        return self._count_nodes(self.data)
    
    def _count_nodes(self, node: MindmapNode) -> int:
        """Recursively count nodes."""
        count = 1  # Current node
        for child in node.children:
            count += self._count_nodes(child)
        return count
    
    class Config:
        schema_extra = {
            "example": {
                "meta": {
                    "name": "Python Learning Path",
                    "author": "System",
                    "version": "1.0"
                },
                "format": "node_tree",
                "data": {
                    "id": "root",
                    "topic": "Python Programming",
                    "children": [
                        {
                            "id": "node_1",
                            "topic": "Basics",
                            "children": [],
                            "expanded": True,
                            "direction": "right"
                        }
                    ],
                    "expanded": True
                }
            }
        }


class QueryLog(BaseModel):
    """Domain model for query logs."""
    
    id: Optional[str] = Field(default=None, description="Log entry ID")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    query_text: str = Field(..., description="Original query text")
    used_functions: Optional[str] = Field(default=None, description="Functions used in processing")
    response_length: Optional[int] = Field(default=None, description="Length of the response")
    mindmap_depth: Optional[int] = Field(default=None, description="Depth of generated mindmap")
    error_flag: bool = Field(default=False, description="Whether an error occurred")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    
    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class LLMResponse(BaseModel):
    """Domain model for LLM responses."""
    
    status: str = Field(..., description="Response status (success/error)")
    data: Dict[str, Any] = Field(..., description="Response data")
    function_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Function calls made")
    message: str = Field(..., description="Human-readable message")
    
    def is_success(self) -> bool:
        """Check if the response indicates success."""
        return self.status == "success"
    
    def has_function_calls(self) -> bool:
        """Check if the response includes function calls."""
        return len(self.function_calls) > 0


# Update forward references
MindmapNode.model_rebuild()