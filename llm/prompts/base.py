"""Base prompt utilities and templates."""


def create_base_system_prompt() -> str:
    """Create a base system prompt with common instructions."""
    return """
You are a helpful and intelligent assistant that can:
- Understand open-ended user queries
- Reason through broad or complex topics
- Use tools and function calls when needed
- Return all output in strict JSON format

Always follow these rules:
1. Always return a valid JSON object
2. Include all functions you called in the response
3. Use clear, descriptive messages
4. Think before answering and organize ideas logically
5. Never include explanations outside the JSON — only return the JSON object
"""


def create_json_response_template() -> str:
    """Create a template for JSON response format."""
    return """
{
    "status": "success" | "error",
    "data": { ... },
    "function_calls": [
        {
            "function": "function_name",
            "parameters": { ... },
            "result": "string describing the function result"
        }
    ],
    "message": "A clear, human-readable summary of your response"
}
"""