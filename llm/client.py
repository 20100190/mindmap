import json
import logging
from typing import Optional, Dict, Any, List
import openai

from core.config import config
from .functions.handlers import FunctionHandler
from .prompts.mindmap import create_mindmap_system_prompt

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with the LLM API."""

    def __init__(self):
        self.config = config.llm
        self.client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
        self.function_handler = FunctionHandler()

    async def process_query(
        self, 
        user_query: str, 
        error_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a query with function calling support.
        
        Args:
            user_query: The user's query
            error_feedback: Optional feedback from previous errors
            
        Returns:
            LLM response with function calls if any
        """
        system_prompt = create_mindmap_system_prompt()

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if error_feedback:
            messages.append({
                'role': 'user',
                "content": f"Previous response had errors: {error_feedback}. Please fix and provide a corrected response for: {user_query}"
            })
        else:
            messages.append({'role': 'user', 'content': user_query})

        function_calls_made = []
        max_function_calls = self.config.max_function_calls

        for call_iteration in range(max_function_calls):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    temperature=self.config.temperature,
                    messages=messages,
                    functions=self.function_handler.get_function_definitions(),
                    function_call="auto"
                )
            except Exception as e:
                logger.error(f"LLM API call failed: {e}")
                return self._create_error_response(str(e))

            message = response.choices[0].message

            # Check if LLM wants to call a function
            if hasattr(message, 'function_call') and message.function_call:
                function_call_result = await self._handle_function_call(
                    message, messages, function_calls_made
                )
                if function_call_result is None:
                    continue  # Function call handled, continue loop
                else:
                    return function_call_result  # Error occurred
            else:
                # No function call, we have the final content
                final_content = message.content
                break
        else:
            # Hit max_function_calls, get final response
            final_content = await self._get_final_response(messages)

        return self._parse_final_response(final_content, function_calls_made)

    async def _handle_function_call(
        self, 
        message, 
        messages: List[Dict], 
        function_calls_made: List[Dict]
    ) -> Optional[Dict]:
        """Handle function call execution."""
        try:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            # Execute the function
            function_result = self.function_handler.execute_function(
                function_name, function_args
            )

            # Store the function call
            function_calls_made.append({
                "function": function_name,
                "parameters": function_args,
                "result": function_result
            })

            # Add assistant's function call to conversation
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": message.function_call
            })

            # Add function result to conversation
            messages.append({
                "role": "function",
                "name": function_name,
                "content": function_result
            })

            return None  # Continue processing

        except Exception as e:
            logger.error(f"Function call failed: {e}")
            return self._create_error_response(f"Function call failed: {e}")

    async def _get_final_response(self, messages: List[Dict]) -> str:
        """Get final response when max function calls reached."""
        try:
            final_response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages + [
                    {"role": "user", "content": "Please provide your final response based on the function calls you've made."}
                ]
            )
            return final_response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to get final response: {e}")
            return f"Error getting final response: {e}"

    def _parse_final_response(self, final_content: str, function_calls_made: List[Dict]) -> Dict[str, Any]:
        """Parse the final response content."""
        try:
            response_json = json.loads(final_content)
            if function_calls_made:
                response_json["function_calls"] = function_calls_made
            return response_json
        except json.JSONDecodeError:
            # If not JSON, wrap in expected format
            return {
                "status": "success",
                "data": {"response": final_content},
                "function_calls": function_calls_made,
                "message": "Response generated successfully"
            }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "status": "error",
            "data": {"error": error_message},
            "function_calls": [],
            "message": f"Error: {error_message}"
        }