"""Business Unit: utilities; Status: current.

Legacy compatibility types for the original domain shared kernel namespace.

Only the ``ActionType`` enum is defined here; value objects now live in the
new ``the_alchemiser.shared_kernel`` package and are re-exported by
``the_alchemiser.domain.shared_kernel.__init__``. Keep this lightweight to
allow incremental migration of import paths.
"""

from __future__ import annotations

from enum import Enum


class ActionType(str, Enum):
    """Enumerates high-level trading actions emitted by strategies.

    Using ``str`` ensures enum values are directly serializable.
    """

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


__all__ = ["ActionType"]
