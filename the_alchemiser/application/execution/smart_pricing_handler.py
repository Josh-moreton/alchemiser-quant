"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.utils
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.smart_pricing_handler to new execution.utils.pricing"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.smart_pricing_handler has moved to execution.utils.pricing. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.utils.pricing import *
