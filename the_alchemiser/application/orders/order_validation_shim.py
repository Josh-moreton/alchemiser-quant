"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.orders
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.orders.order_validation to new execution.orders.validator"
)

# Issue deprecation warning
warnings.warn(
    "application.orders.order_validation has moved to execution.orders.validator. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.orders.validator import *