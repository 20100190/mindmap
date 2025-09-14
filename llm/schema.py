expected_schema_mindmap_query = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "children": {"type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "children": {
                                "type": "array",
                                "items": {"$ref": "#/properties/data/properties/children/items"}
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False
                    }
                }
            }
        },
        "message": {"type": "string"}
    },
    "required": ["status", "data", "message"]
}