"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.strategies
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.strategies.config to new execution.strategies.config"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.strategies.config has moved to execution.strategies.config. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.strategies.config import *