"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.orders
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy application.execution.order_request_builder to new execution.orders.builder"
)

# Issue deprecation warning
warnings.warn(
    "application.execution.order_request_builder has moved to execution.orders.builder. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.orders.builder import *