import logging
from typing import Dict, Any, Tuple, Optional
import jsonschema
from jsonschema import validate

from .schema import MINDMAP_SCHEMA

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates LLM responses against expected schemas."""

    def __init__(self):
        self.mindmap_schema = MINDMAP_SCHEMA

    def validate_mindmap_response(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a mindmap response against the expected schema.
        
        Args:
            response: The response to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self._validate_against_schema(response, self.mindmap_schema)

    def validate_json_structure(self, response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Legacy method for backward compatibility.
        Validates JSON response structure using mindmap schema.
        """
        return self.validate_mindmap_response(response)

    def _validate_against_schema(
        self, 
        response: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate response against a given schema.
        
        Args:
            response: Response to validate
            schema: JSON schema to validate against
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=response, schema=schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            error_message = f"JSON validation failed: {e.message}"
            logger.warning(f"Validation error: {error_message}")
            return False, error_message
        except Exception as e:
            error_message = f"Validation error: {str(e)}"
            logger.error(f"Unexpected validation error: {error_message}")
            return False, error_message