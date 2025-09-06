"""Business Unit: shared | Status: current.

Order status type definitions for shared use across modules.
"""

from typing import Literal

OrderStatusLiteral = Literal[
    "new",
    "partially_filled", 
    "filled",
    "canceled",
    "expired",
    "rejected",
]