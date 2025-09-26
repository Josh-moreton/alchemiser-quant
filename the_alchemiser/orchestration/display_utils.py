"""Deprecated module placeholder.

This module previously exposed CLI display utilities for the traditional
orchestration path. The event-driven workflow now logs consolidated signals and
rebalance plans directly from their handlers, so these helpers are intentionally
removed. Importing this module will raise a RuntimeError to surface accidental
usage.
"""

raise RuntimeError(
    "the_alchemiser.orchestration.display_utils has been removed. "
    "Use event-driven logging from the handlers instead."
)
