import time
import random
import uuid
from typing import Set


class IDGenerator:
    """Generator for unique node IDs."""
    
    def __init__(self):
        self.counter = 0
        self.used_ids: Set[str] = set()

    def generate_timestamp_based(self) -> str:
        """Generate timestamp-based ID."""
        self.counter += 1
        return f"node_{int(time.time() * 1000)}_{self.counter}"

    def generate_uuid_based(self) -> str:
        """Generate UUID-based ID."""
        return f"node_{uuid.uuid4().hex[:16]}"

    def generate_random_based(self) -> str:
        """Generate random-based ID."""
        return f"node_{int(time.time() * 1000)}_{random.randint(100, 999)}"

    def generate_deduplicated(self) -> str:
        """Generate deduped ID."""
        while True:
            new_id = self.generate_random_based()
            if new_id not in self.used_ids:
                self.used_ids.add(new_id)
                return new_id

    def generate_root_id(self) -> str:
        """Generate root node ID."""
        return "root"

    def clear_used_ids(self) -> None:
        """Clear the used IDs set."""
        self.used_ids.clear()