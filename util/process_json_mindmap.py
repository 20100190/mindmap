import time
import random
import uuid
import json

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

def process_mindmap(json_response):
    json_response_ = traverse_and_update(json_response['data'], is_root=True)
    return {
        "meta": {
            "name": json_response_['topic'],
            "author": "System",
            "version": "1.0"
        },
        "format": "node_tree",
        "data": json_response_
    }

def count_depth(node):
    if 'children' not in node or not node['children']:
        return 1
    return 1 + max(count_depth(child) for child in node['children'])

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