#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Order Error Classification System for The Alchemiser Trading System.

This module provides structured error classification for order lifecycle and execution paths,
enabling deterministic branching, richer analytics, and improved user-facing messaging.
"""

from .classifier import (
    OrderErrorClassifier,
    classify_alpaca_error,
    classify_exception,
    classify_validation_failure,
)
from .error_categories import OrderErrorCategory
from .error_codes import OrderErrorCode
from .order_error import OrderError

__all__ = [
    "OrderError",
    "OrderErrorCategory",
    "OrderErrorClassifier",
    "OrderErrorCode",
    "classify_alpaca_error",
    "classify_exception",
    "classify_validation_failure",
]
