# Legacy compatibility module
# This module is deprecated. Please use infrastructure.storage.gcs_client instead.

import warnings
from utils.gcs_legacy import upload_result_to_gcs

warnings.warn(
    "util.gcs_util is deprecated. Please use infrastructure.storage.gcs_client.GCSClient instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
__all__ = ["upload_result_to_gcs"]