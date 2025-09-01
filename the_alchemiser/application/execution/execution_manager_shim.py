"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.core
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.execution_manager to new execution.core.executor"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.execution_manager has moved to execution.core.executor. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.core.executor import *