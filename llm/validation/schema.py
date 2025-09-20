"""JSON schemas for validating LLM responses."""

# Schema for mindmap query responses
MINDMAP_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["success", "error"]
        },
        "data": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "children": {
                    "type": "array",
                    "items": {
                        "$ref": "#/$defs/mindmap_node"
                    }
                }
            },
            "required": ["topic"]
        },
        "function_calls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "function": {"type": "string"},
                    "parameters": {"type": "object"},
                    "result": {"type": "string"}
                },
                "required": ["function", "parameters", "result"]
            }
        },
        "message": {"type": "string"}
    },
    "required": ["status", "data", "message"],
    "$defs": {
        "mindmap_node": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/mindmap_node"}
                }
            },
            "required": ["topic"]
        }
    }
}

# For backward compatibility
expected_schema_mindmap_query = MINDMAP_SCHEMA