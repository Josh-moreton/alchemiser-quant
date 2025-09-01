"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.utils
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.spread_assessment to new execution.utils.spread"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.spread_assessment has moved to execution.utils.spread. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.utils.spread import *
