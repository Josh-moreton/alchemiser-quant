#!/usr/bin/env python3
"""
Order Error Categories for structured error classification.

This module defines the high-level categories for order-related errors,
enabling consistent classification and handling across the trading system.
"""

from enum import Enum


class OrderErrorCategory(Enum):
    """High-level categories for order-related errors.

    These categories enable deterministic branching and richer analytics
    on failure modes across the order lifecycle.
    """

    VALIDATION = "validation"
    """Order validation failures (invalid symbols, quantities, etc.)"""

    LIQUIDITY = "liquidity"
    """Market liquidity related issues (wide spreads, insufficient liquidity)"""

    RISK_MANAGEMENT = "risk_management"
    """Risk control failures (insufficient buying power, position limits)"""

    MARKET_CONDITIONS = "market_conditions"
    """Market status related issues (halts, auctions, LULD)"""

    SYSTEM = "system"
    """Internal system errors (service failures, timeouts)"""

    CONNECTIVITY = "connectivity"
    """Network and broker API connectivity issues"""

    AUTHORIZATION = "authorization"
    """Authentication and permission related errors"""

    CONFIGURATION = "configuration"
    """Configuration and setup related errors"""
