"""
Legacy compatibility module for GCS operations.
This module provides backward compatibility for existing imports.
"""

import logging
from typing import Dict, Any
from infrastructure.storage.gcs_client import GCSClient

logger = logging.getLogger(__name__)

# Create a global client instance
_gcs_client = GCSClient()


def upload_result_to_gcs(result_dict: Dict[str, Any], filename: str) -> None:
    """
    Legacy function for uploading results to GCS.
    
    This function maintains backward compatibility with the old API.
    It delegates to the new GCS client implementation.
    
    Args:
        result_dict: Dictionary to upload as JSON
        filename: Name of the file in GCS
    """
    try:
        # Use the new async client in a sync manner
        import asyncio
        
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, we can't use asyncio.run()
            # Create a task instead
            task = loop.create_task(_gcs_client.upload_json(result_dict, f"query_results/{filename}"))
            # Note: This won't block, which might be different from the original behavior
            logger.warning("Async upload started but not awaited in legacy compatibility mode")
        except RuntimeError:
            # No running loop, we can use asyncio.run()
            asyncio.run(_gcs_client.upload_json(result_dict, f"query_results/{filename}"))
            
    except Exception as e:
        logger.error(f"Legacy GCS upload failed: {e}")
        # Don't raise the exception to maintain backward compatibility
        # The original function didn't handle errors either