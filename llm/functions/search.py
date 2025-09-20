import json
import logging
from typing import Optional
from langchain_google_community import GoogleSearchAPIWrapper

logger = logging.getLogger(__name__)


class GoogleSearchFunction:
    """Handles Google search functionality."""

    def __init__(self):
        self.search_tool = None
        self._initialize_search_tool()

    def _initialize_search_tool(self):
        """Initialize the Google search tool."""
        try:
            self.search_tool = GoogleSearchAPIWrapper()
        except Exception as e:
            logger.warning(f"Failed to initialize Google search: {e}")
            self.search_tool = None

    def search(self, query: str, num_results: int = 5) -> str:
        """
        Perform Google search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            JSON string with search results
        """
        if not self.search_tool:
            return json.dumps({
                "error": "Google search not available",
                "query": query,
                "results": "Search functionality is not configured"
            })

        try:
            search_results = self.search_tool.run(query)
            return json.dumps({
                "query": query,
                "results": search_results,
                "num_results_requested": num_results
            })
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "query": query,
                "results": "Search operation failed"
            })