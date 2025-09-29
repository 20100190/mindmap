expected_schema_mindmap_query = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "mindmap" : {"type":"string", "enum": ["true", "false"]},
        "mindmap-data": {
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
                                "items": {"$ref": "#/properties/mindmap-data/properties/children/items"}
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False
                    }
                }
            },
            "required" : ["topic"],
        },
        "message": {"type": "string"}
    },
    "required": ["status", "mindmap", "message"]
}