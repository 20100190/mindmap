import time
import random
import uuid
import json
import logging
import jsonschema
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_json_structure(response: Dict[str, Any], expected_schema) -> tuple[bool, Optional[str]]:
    """Validate JSON response structure"""
    try:
        jsonschema.validate(instance=response, schema=expected_schema)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        error_message = f"JSON validation failed: {e.message}"
        return False, error_message
    except Exception as e:
        error_message = f"Validation error: {str(e)}"
        return False, error_message

class IDGenerator:
    def __init__(self):
        self.counter = 0

    def generate(self):
        self.counter += 1
        return f"node_{int(time.time() * 1000)}_{self.counter}"

def generate_uuid():
    return f"node_{uuid.uuid4().hex[:16]}"

def generate_id():
    return f"node_{int(time.time() * 1000)}_{random.randint(100, 999)}"

used_ids = set()
def generate_id_deduplicated():
    while True:
        new_id = f"node_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        if new_id not in used_ids:
            used_ids.add(new_id)
            return new_id

def traverse_and_update(node, is_root=False):
    try:
        # Set defaults
        node.setdefault("id", "root" if is_root else generate_uuid())
        node.setdefault("expanded", True)
        if not is_root:
            node.setdefault("direction", "right")

        # Recurse through children if any
        children = node.get("children", [])
        for child in children:
            traverse_and_update(child)

        return node
    except Exception as e:
        logger.exception(f"Error in Json processing. Error {e}")
        raise

def process_mindmap(json_response):
    try:
        json_response_ = traverse_and_update(json_response['mindmap-data'], is_root=True)
        return {
            "meta": {
                "name": json_response_['topic'],
                "author": "System",
                "version": "1.0"
            },
            "format": "node_tree",
            "data": json_response_
        }
    except Exception as e:
        logger.exception(f"Error in Json processing. Error {e}")
        raise


def count_depth(node):
    if 'children' not in node or not node['children']:
        return 1
    return 1 + max(count_depth(child) for child in node['children'])


def extract_first_json_chunk(s: str) -> str:
    """Extracts the first complete JSON object from a string, ignoring any trailing data."""
    try:
        open_braces = 0
        in_string = False
        escape = False

        for i, char in enumerate(s):
            if char == '"' and not escape:
                in_string = not in_string
            if char == '\\' and not escape:
                escape = True
                continue
            escape = False

            if not in_string:
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        first_json_chunk = s[:i + 1]
                        try:
                            first_valid_json = json.loads(first_json_chunk)
                            return first_valid_json
                        except json.JSONDecodeError as e:
                            logger.error(f"No valid Json in first chunk. Error: {e}")
                        except json.JSONDecodeError as e:
                            logger.error(f"No valid Json in last chunk. Error: {e}")
        raise RuntimeError("No valid Json")
    except Exception as e:
        logger.error(f"Could not parse Json. Error: {e}")


def normalize_llm_response(llm_response: str) -> Dict[str, Any]:
    """
    Accepts a raw string from LLM (`message.content`)
    - Tries to parse it
    - If nested JSON inside 'data.response', parses that too
    """
    try:
        parsed = json.loads(llm_response)
    except json.JSONDecodeError as e:
        logger.error(f"Top-level LLM response is not valid JSON: {e}")
        return {}

    # Check if nested JSON string is inside 'data.response'
    response_field = parsed.get("data", {}).get("response")
    if isinstance(response_field, str):
        try:
            inner_data = json.loads(response_field)
            return inner_data
        except json.JSONDecodeError:
            logger.warning("Nested response was not valid JSON; skipping normalization")

    return parsed

if __name__ == "__main__":
    # Example usage
    sample_json = {
        "status": "success",
        "topic": "Sample Mindmap",
        "data": {
            "topic": "Root Node",
            "children": [
                {"topic": "Child Node 1"},
                {"topic": "Child Node 2", "children": [{"topic": "Grandchild Node"}]}
            ]
        }
    }

    processed = process_mindmap(sample_json)
    print(json.dumps(processed, indent=2))