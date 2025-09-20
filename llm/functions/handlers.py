import json
import logging
from typing import Dict, Any, List

from .definitions import get_function_definitions
from .search import GoogleSearchFunction

logger = logging.getLogger(__name__)


class FunctionHandler:
    """Handles function call execution for the LLM."""

    def __init__(self):
        self.search_function = GoogleSearchFunction()

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Get function definitions for the LLM."""
        return get_function_definitions()

    def execute_function(self, function_name: str, parameters: Dict[str, Any]) -> str:
        """
        Execute a function call based on function name.
        
        Args:
            function_name: Name of the function to execute
            parameters: Function parameters
            
        Returns:
            JSON string result of function execution
        """
        try:
            if function_name == "google_search":
                return self._execute_google_search(**parameters)
            elif function_name == "calculate_sum":
                return self._execute_calculate_sum(**parameters)
            else:
                return json.dumps({"error": f"Unknown function: {function_name}"})
        except Exception as e:
            logger.error(f"Function execution failed for {function_name}: {e}")
            return json.dumps({"error": f"Function execution failed: {str(e)}"})

    def _execute_google_search(self, query: str, num_results: int = 5) -> str:
        """Execute Google search function."""
        return self.search_function.search(query, num_results)

    def _execute_calculate_sum(self, a: float, b: float) -> str:
        """Execute sum calculation function."""
        try:
            return json.dumps({
                "a": a,
                "b": b,
                "sum": a + b  # Fixed the multiplication bug from original
            })
        except Exception as e:
            return json.dumps({"error": f"Calculation error: {str(e)}"})