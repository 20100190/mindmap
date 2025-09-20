# Legacy compatibility package
# This package is deprecated. Please use the new structure:
# - utils.mindmap_processor instead of util.process_json_mindmap
# - infrastructure.storage.gcs_client instead of util.gcs_util

import warnings

warnings.warn(
    "The 'util' package is deprecated. Please update your imports to use the new structure.",
    DeprecationWarning,
    stacklevel=2
)