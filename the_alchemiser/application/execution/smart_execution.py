"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.strategies
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.smart_execution to new execution.strategies.smart_execution"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.smart_execution has moved to execution.strategies.smart_execution. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.strategies.smart_execution import *