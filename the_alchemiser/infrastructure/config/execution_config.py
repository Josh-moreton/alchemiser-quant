"""
MIGRATION SHIM: This module has moved to the_alchemiser.shared.config
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy infrastructure.config.execution_config to new shared.config.execution_config"
)

# Issue deprecation warning
warnings.warn(
    "infrastructure.config.execution_config has moved to shared.config.execution_config. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.shared.config.execution_config import *