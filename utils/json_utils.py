import json
import logging
from typing import Any, Dict, Optional, Union
from decimal import Decimal
from datetime import datetime, date

logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles additional types."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def safe_json_loads(json_string: str) -> Optional[Dict[str, Any]]:
    """
    Safely load JSON with error handling.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return None


def safe_json_dumps(
    data: Any, 
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
    default_fallback: bool = True
) -> Optional[str]:
    """
    Safely dump data to JSON string with error handling.
    
    Args:
        data: Data to serialize
        indent: Indentation for pretty printing
        ensure_ascii: Whether to escape non-ASCII characters
        default_fallback: Whether to use fallback for non-serializable objects
        
    Returns:
        JSON string or None if serialization fails
    """
    try:
        if default_fallback:
            return json.dumps(
                data, 
                cls=JSONEncoder,
                indent=indent,
                ensure_ascii=ensure_ascii
            )
        else:
            return json.dumps(
                data,
                indent=indent,
                ensure_ascii=ensure_ascii
            )
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error serializing JSON: {e}")
        return None


def pretty_print_json(data: Any) -> str:
    """
    Pretty print JSON data.
    
    Args:
        data: Data to format
        
    Returns:
        Pretty formatted JSON string
    """
    json_str = safe_json_dumps(data, indent=2)
    return json_str if json_str is not None else str(data)


def flatten_json(
    data: Dict[str, Any], 
    separator: str = ".",
    prefix: str = ""
) -> Dict[str, Any]:
    """
    Flatten a nested JSON object.
    
    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        prefix: Prefix for keys
        
    Returns:
        Flattened dictionary
    """
    flattened = {}
    
    for key, value in data.items():
        new_key = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            flattened.update(flatten_json(value, separator, new_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    flattened.update(flatten_json(item, separator, f"{new_key}[{i}]"))
                else:
                    flattened[f"{new_key}[{i}]"] = item
        else:
            flattened[new_key] = value
    
    return flattened


def merge_json_objects(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two JSON objects.
    
    Args:
        obj1: First object (base)
        obj2: Second object (overlay)
        
    Returns:
        Merged dictionary
    """
    result = obj1.copy()
    
    for key, value in obj2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_json_structure(
    data: Dict[str, Any], 
    required_keys: list,
    optional_keys: Optional[list] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate JSON object structure.
    
    Args:
        data: Dictionary to validate
        required_keys: Keys that must be present
        optional_keys: Keys that may be present
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Data is not a dictionary"
    
    # Check required keys
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Missing required keys: {missing_keys}"
    
    # Check for unexpected keys if optional_keys is provided
    if optional_keys is not None:
        allowed_keys = set(required_keys + optional_keys)
        unexpected_keys = [key for key in data.keys() if key not in allowed_keys]
        if unexpected_keys:
            return False, f"Unexpected keys found: {unexpected_keys}"
    
    return True, None