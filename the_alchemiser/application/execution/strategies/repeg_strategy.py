"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.strategies
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.strategies.repeg_strategy to new execution.strategies.repeg_strategy"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.strategies.repeg_strategy has moved to execution.strategies.repeg_strategy. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.strategies.repeg_strategy import *