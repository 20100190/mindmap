import json
from typing import List, Dict, Any
from langchain_google_community import GoogleSearchAPIWrapper

def define_functions() -> List[Dict[str, Any]]:
    """Define available functions for the LLM to call"""
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

def google_search(query: str, num_results: int = 5) -> str:
    """Mock Google search function - replace with actual implementation"""
    # This is a placeholder - you would integrate with Google Search API
    # or use libraries like googlesearch-python
    search_tool = GoogleSearchAPIWrapper()
    search_results = search_tool.run(query)

    return json.dumps({
        "query": query,
        "results": search_results
    })

def calculate_sum(a: float, b: float) -> float:
    """Example custom function to calculate sum"""
    try:
        return json.dumps({  # ✅ Returns JSON string
            "a": a,
            "b": b,
            "sum": a*b
        })
    except Exception as e:
        return f"Calculation error: {str(e)}"


def execute_function_call(function_name: str, parameters: Dict[str, Any]) -> str:
    """Execute function calls based on function name"""
    if function_name == "google_search":
        return google_search(**parameters)
    elif function_name == "calculate_sum":
        return calculate_sum(**parameters)
    else:
        return f"Unknown function: {function_name}"