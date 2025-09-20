import logging
from typing import Dict, Any, List
from .id_generator import IDGenerator

logger = logging.getLogger(__name__)


class MindmapProcessor:
    """Processes mindmap data for frontend consumption."""

    def __init__(self):
        self.id_generator = IDGenerator()

    def process_mindmap(self, json_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process LLM response into frontend-compatible mindmap format.
        
        Args:
            json_response: Raw LLM response
            
        Returns:
            Processed mindmap data
        """
        try:
            # Clear any previous IDs
            self.id_generator.clear_used_ids()
            
            # Process the data section
            processed_data = self._traverse_and_update(json_response['data'], is_root=True)
            
            # Create the final structure
            return {
                "meta": {
                    "name": processed_data['topic'],
                    "author": "System",
                    "version": "1.0"
                },
                "format": "node_tree",
                "data": processed_data
            }
        except Exception as e:
            logger.error(f"Error processing mindmap: {e}")
            # Return a fallback structure
            return {
                "meta": {
                    "name": "Error Processing Mindmap",
                    "author": "System",
                    "version": "1.0"
                },
                "format": "node_tree",
                "data": {
                    "id": "root",
                    "topic": "Processing Error",
                    "expanded": True,
                    "children": []
                }
            }

    def count_depth(self, node: Dict[str, Any]) -> int:
        """
        Count the depth of a mindmap tree.
        
        Args:
            node: Root node of the mindmap
            
        Returns:
            Maximum depth of the tree
        """
        if not isinstance(node, dict):
            return 0
            
        if 'children' not in node or not node['children']:
            return 1
        
        try:
            return 1 + max(self.count_depth(child) for child in node['children'])
        except Exception as e:
            logger.error(f"Error counting depth: {e}")
            return 1

    def _traverse_and_update(self, node: Dict[str, Any], is_root: bool = False) -> Dict[str, Any]:
        """
        Traverse and update a mindmap node with required frontend properties.
        
        Args:
            node: Node to process
            is_root: Whether this is the root node
            
        Returns:
            Updated node
        """
        # Create a copy to avoid modifying the original
        updated_node = node.copy()
        
        # Set required properties
        if is_root:
            updated_node["id"] = self.id_generator.generate_root_id()
        else:
            updated_node.setdefault("id", self.id_generator.generate_uuid_based())
            updated_node.setdefault("direction", "right")
        
        updated_node.setdefault("expanded", True)

        # Process children if any
        if "children" in updated_node and updated_node["children"]:
            updated_children = []
            for child in updated_node["children"]:
                if isinstance(child, dict):
                    updated_children.append(self._traverse_and_update(child, is_root=False))
                else:
                    logger.warning(f"Invalid child node: {child}")
            updated_node["children"] = updated_children

        return updated_node

    def validate_mindmap_structure(self, mindmap_data: Dict[str, Any]) -> bool:
        """
        Validate that a mindmap has the expected structure.
        
        Args:
            mindmap_data: Mindmap data to validate
            
        Returns:
            True if structure is valid
        """
        try:
            # Check top-level structure
            required_keys = ["meta", "format", "data"]
            if not all(key in mindmap_data for key in required_keys):
                return False
            
            # Check data structure
            data = mindmap_data["data"]
            if not isinstance(data, dict) or "topic" not in data:
                return False
            
            # Recursively check node structure
            return self._validate_node(data)
            
        except Exception as e:
            logger.error(f"Error validating mindmap structure: {e}")
            return False

    def _validate_node(self, node: Dict[str, Any]) -> bool:
        """Validate a single node structure."""
        if not isinstance(node, dict):
            return False
        
        # Must have topic
        if "topic" not in node:
            return False
        
        # If has children, validate them
        if "children" in node:
            if not isinstance(node["children"], list):
                return False
            
            for child in node["children"]:
                if not self._validate_node(child):
                    return False
        
        return True