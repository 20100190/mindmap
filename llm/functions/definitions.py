from typing import List, Dict, Any


def get_function_definitions() -> List[Dict[str, Any]]:
    """Get all available function definitions for the LLM."""
    return [
        {
            "name": "google_search",
            "description": "Search Google for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "calculate_sum",
            "description": "Execute a custom sum function",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number to add"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number to add"
                    }
                },
                "required": ["a", "b"]
            }
        }
    ]