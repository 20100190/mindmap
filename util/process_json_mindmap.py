# Legacy compatibility module
# This module is deprecated. Please use utils.mindmap_processor instead.

import warnings
from utils.mindmap_processor import MindmapProcessor
from utils.id_generator import IDGenerator

warnings.warn(
    "util.process_json_mindmap is deprecated. Please use utils.mindmap_processor.MindmapProcessor instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create processor instance for legacy functions
_processor = MindmapProcessor()
_id_generator = IDGenerator()

# Legacy function implementations for backward compatibility
def process_mindmap(json_response):
    """Legacy wrapper for mindmap processing."""
    return _processor.process_mindmap(json_response)

def count_depth(node):
    """Legacy wrapper for depth counting."""
    return _processor.count_depth(node)

def traverse_and_update(node, is_root=False):
    """Legacy wrapper for node traversal."""
    return _processor._traverse_and_update(node, is_root)

# Legacy ID generation functions
def generate_uuid():
    """Legacy wrapper for UUID generation."""
    return _id_generator.generate_uuid_based()

def generate_id():
    """Legacy wrapper for ID generation."""
    return _id_generator.generate_random_based()

def generate_id_deduplicated():
    """Legacy wrapper for deduplicated ID generation."""
    return _id_generator.generate_deduplicated()

class IDGenerator:
    """Legacy ID generator class."""
    def __init__(self):
        self.generator = _id_generator
    
    def generate(self):
        return self.generator.generate_timestamp_based()

# Re-export for backward compatibility
__all__ = [
    "process_mindmap", 
    "count_depth", 
    "traverse_and_update",
    "generate_uuid",
    "generate_id", 
    "generate_id_deduplicated",
    "IDGenerator"
]