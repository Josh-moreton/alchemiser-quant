"""
MIGRATION SHIM: This module has moved to the_alchemiser.execution.brokers
This shim maintains backward compatibility during the execution module migration.
"""
import logging
import warnings

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy services.repository.alpaca_manager to new execution.brokers.alpaca.adapter"
)

# Issue deprecation warning
warnings.warn(
    "services.repository.alpaca_manager has moved to execution.brokers.alpaca.adapter. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new location
from the_alchemiser.execution.brokers.alpaca.adapter import *


