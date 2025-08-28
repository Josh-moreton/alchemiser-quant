"""Business Unit: order execution/placement; Status: current.

Order-related exceptions for execution domain.
"""

from __future__ import annotations


class OrderValidationError(Exception):
    """Exception raised when order validation fails."""


class OrderOperationError(Exception):
    """Exception raised when an order operation (e.g. liquidation) fails."""