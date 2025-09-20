import json
import logging
from typing import Dict, Any, Optional
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from core.config import config

logger = logging.getLogger(__name__)


class GCSClient:
    """Client for Google Cloud Storage operations."""

    def __init__(self):
        self.bucket_name = config.gcs.bucket_name
        self.client = None
        self.bucket = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the GCS client and bucket."""
        try:
            if not self.bucket_name:
                logger.warning("GCS bucket name not configured, storage operations will be disabled")
                return

            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"GCS client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None
            self.bucket = None

    async def upload_json(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Upload JSON data to GCS.
        
        Args:
            data: Dictionary to upload as JSON
            filename: Name of the file in GCS
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.warning("GCS not configured, skipping upload")
            return False

        try:
            blob = self.bucket.blob(filename)
            json_string = json.dumps(data, indent=2)
            
            blob.upload_from_string(
                json_string,
                content_type='application/json'
            )
            
            logger.info(f"Successfully uploaded {filename} to GCS")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"GCS error uploading {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {filename}: {e}")
            return False

    async def upload_text(self, text: str, filename: str) -> bool:
        """
        Upload text data to GCS.
        
        Args:
            text: Text content to upload
            filename: Name of the file in GCS
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.warning("GCS not configured, skipping upload")
            return False

        try:
            blob = self.bucket.blob(filename)
            blob.upload_from_string(text, content_type='text/plain')
            
            logger.info(f"Successfully uploaded {filename} to GCS")
            return True
            
        except GoogleCloudError as e:
            logger.error(f"GCS error uploading {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {filename}: {e}")
            return False

    async def download_json(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Download JSON data from GCS.
        
        Args:
            filename: Name of the file in GCS
            
        Returns:
            Dictionary if successful, None otherwise
        """
        if not self.bucket:
            logger.warning("GCS not configured, cannot download")
            return None

        try:
            blob = self.bucket.blob(filename)
            
            if not blob.exists():
                logger.warning(f"File {filename} does not exist in GCS")
                return None
                
            json_string = blob.download_as_text()
            return json.loads(json_string)
            
        except GoogleCloudError as e:
            logger.error(f"GCS error downloading {filename}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            return None

    def is_configured(self) -> bool:
        """Check if GCS is properly configured."""
        return self.client is not None and self.bucket is not None