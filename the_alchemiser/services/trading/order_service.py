"""Business Unit: execution; Status: legacy.

CRITICAL: This module has moved to the_alchemiser.execution.orders
This shim maintains backward compatibility for execution systems.
"""

import logging

# Import everything from the new location
from the_alchemiser.execution.orders.service import *  # noqa: F403, F401

# Log the redirection for audit purposes
logging.getLogger(__name__).info(
    "Import redirected from legacy path to execution.orders module"
)
