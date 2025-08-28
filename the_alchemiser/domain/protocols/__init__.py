"""Business Unit: utilities; Status: current.

Common protocols for attribute access patterns throughout the system.
"""

from .account_like import AccountLikeProtocol
from .order_like import OrderLikeProtocol
from .position_like import PositionLikeProtocol

__all__ = [
    "AccountLikeProtocol",
    "OrderLikeProtocol",
    "PositionLikeProtocol",
]
