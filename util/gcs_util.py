import os
import json
import logging
from typing import Dict, Any, Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError, NotFound, Forbidden
from google.auth.exceptions import DefaultCredentialsError

from logs_management.log_manager import log_error, get_correlation_id

logger = logging.getLogger(__name__)

class GCSConfig:
    """Configuration for GCS operations."""
    DEFAULT_BUCKET = "mindmap-results"
    DEFAULT_FOLDER = "query_results"
    UPLOAD_TIMEOUT = 30  # seconds
    
config = GCSConfig()

def upload_result_to_gcs(
    result_dict: Dict[str, Any], 
    filename: str,
    bucket_name: Optional[str] = None,
    folder: Optional[str] = None
) -> bool:
    """
    Upload result dictionary to Google Cloud Storage.
    
    Args:
        result_dict: Dictionary to upload as JSON
        filename: Name of the file to create
        bucket_name: GCS bucket name (optional, uses env var or default)
        folder: Folder path within bucket (optional, uses default)
        
    Returns:
        bool: True if upload succeeded, False otherwise
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If upload fails critically
    """
    correlation_id = get_correlation_id()
    
    # Validate inputs
    if not result_dict:
        raise ValueError("Result dictionary cannot be empty")
        
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")
        
    filename = filename.strip()
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Sanitize filename
    filename = _sanitize_filename(filename)
    
    # Get configuration
    bucket_name = bucket_name or os.getenv("RESULTS_BUCKET", config.DEFAULT_BUCKET)
    folder = folder or os.getenv("RESULTS_FOLDER", config.DEFAULT_FOLDER)
    
    full_path = f"{folder}/{filename}" if folder else filename
    
    logger.info(
        f"Starting GCS upload",
        extra={'extra_data': {
            'bucket': bucket_name,
            'path': full_path,
            'data_size': len(str(result_dict)),
            'correlation_id': correlation_id
        }}
    )
    
    try:
        # Initialize client
        try:
            client = storage.Client()
        except DefaultCredentialsError as e:
            logger.error(f"GCS authentication failed: {str(e)}")
            raise RuntimeError(f"GCS authentication failed: {str(e)}") from e
        
        # Get bucket
        try:
            bucket = client.bucket(bucket_name)
            # Check if bucket exists and is accessible
            bucket.reload()
        except NotFound:
            logger.error(f"GCS bucket '{bucket_name}' not found")
            raise RuntimeError(f"GCS bucket '{bucket_name}' not found")
        except Forbidden as e:
            logger.error(f"Access denied to GCS bucket '{bucket_name}': {str(e)}")
            raise RuntimeError(f"Access denied to GCS bucket '{bucket_name}'") from e
        except Exception as e:
            logger.error(f"Failed to access GCS bucket '{bucket_name}': {str(e)}")
            raise RuntimeError(f"Failed to access GCS bucket: {str(e)}") from e
        
        # Prepare data
        try:
            json_data = json.dumps(result_dict, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data to JSON: {str(e)}")
            raise ValueError(f"Data serialization failed: {str(e)}") from e
        
        # Upload file
        blob = bucket.blob(full_path)
        
        try:
            blob.upload_from_string(
                json_data,
                content_type="application/json; charset=utf-8",
                timeout=config.UPLOAD_TIMEOUT
            )
            
            # Verify upload
            if blob.exists():
                file_size = blob.size
                logger.info(
                    f"GCS upload successful",
                    extra={'extra_data': {
                        'bucket': bucket_name,
                        'path': full_path,
                        'file_size': file_size,
                        'correlation_id': correlation_id
                    }}
                )
                return True
            else:
                logger.error("File upload completed but file does not exist in GCS")
                return False
                
        except GoogleCloudError as e:
            logger.error(f"GCS upload failed: {str(e)}")
            raise RuntimeError(f"GCS upload failed: {str(e)}") from e
            
    except ValueError:
        # Re-raise validation errors
        raise
    except RuntimeError:
        # Re-raise runtime errors
        raise
    except Exception as e:
        # Log and wrap unexpected errors
        log_error(logger, e, {
            'operation': 'gcs_upload',
            'bucket': bucket_name,
            'path': full_path,
            'correlation_id': correlation_id
        })
        raise RuntimeError(f"Unexpected error during GCS upload: {str(e)}") from e

def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for GCS upload.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\n', '\r', '\t']
    
    sanitized = filename
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        sanitized = "unnamed_file.json"
    
    # Limit length
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext
    
    return sanitized

def check_gcs_connection(bucket_name: Optional[str] = None) -> bool:
    """
    Check if GCS connection and bucket access are working.
    
    Args:
        bucket_name: Bucket to test (optional, uses default)
        
    Returns:
        bool: True if connection is working, False otherwise
    """
    bucket_name = bucket_name or os.getenv("RESULTS_BUCKET", config.DEFAULT_BUCKET)
    
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        bucket.reload()
        
        logger.info(f"GCS connection to bucket '{bucket_name}' successful")
        return True
        
    except Exception as e:
        logger.error(f"GCS connection test failed: {str(e)}")
        return False