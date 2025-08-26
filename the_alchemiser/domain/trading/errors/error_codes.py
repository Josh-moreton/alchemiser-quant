#!/usr/bin/env python3
"""
Specific Order Error Codes mapped to categories.

This module defines specific error codes that provide precise classification
of order failures, enabling targeted remediation and analytics.
"""

from enum import Enum


class OrderErrorCode(Enum):
    """Specific error codes for order failures, mapped to categories."""
    
    # VALIDATION category errors
    INVALID_SYMBOL = "invalid_symbol"
    """Symbol is not valid or not supported"""
    
    UNSUPPORTED_ORDER_TYPE = "unsupported_order_type"
    """Order type is not supported for this symbol or market"""
    
    INVALID_QUANTITY = "invalid_quantity"
    """Quantity is invalid (negative, zero, or exceeds limits)"""
    
    FRACTIONAL_NOT_ALLOWED = "fractional_not_allowed"
    """Fractional shares not allowed for this symbol"""
    
    PRICE_OUT_OF_BOUNDS = "price_out_of_bounds"
    """Price is outside acceptable bounds (too high/low, wrong format)"""
    
    DUPLICATE_CLIENT_ORDER_ID = "duplicate_client_order_id"
    """Client order ID is already in use"""
    
    # LIQUIDITY category errors
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    """Not enough liquidity available to fill the order"""
    
    WIDE_SPREAD = "wide_spread"
    """Bid-ask spread is too wide for safe execution"""
    
    NO_MARKET_MAKERS = "no_market_makers"
    """No market makers available for this symbol"""
    
    # RISK_MANAGEMENT category errors
    INSUFFICIENT_BUYING_POWER = "insufficient_buying_power"
    """Account does not have sufficient buying power"""
    
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    """Order would exceed position size limits"""
    
    ORDER_VALUE_LIMIT_EXCEEDED = "order_value_limit_exceeded"
    """Order value exceeds maximum allowed"""
    
    MAX_DAILY_TRADES_EXCEEDED = "max_daily_trades_exceeded"
    """Maximum number of daily trades exceeded"""
    
    # MARKET_CONDITIONS category errors
    MARKET_HALTED = "market_halted"
    """Trading is halted for this symbol"""
    
    LIMIT_UP_DOWN_BREACH = "limit_up_down_breach"
    """Price limit up/down circuit breaker triggered"""
    
    AUCTION_TRANSITION = "auction_transition"
    """Market is in auction mode, continuous trading unavailable"""
    
    # SYSTEM category errors
    INTERNAL_SERVICE_ERROR = "internal_service_error"
    """Internal service or processing error"""
    
    SERIALIZATION_FAILURE = "serialization_failure"
    """Failed to serialize/deserialize order data"""
    
    TIMEOUT = "timeout"
    """Operation timed out before completion"""
    
    # CONNECTIVITY category errors
    NETWORK_UNREACHABLE = "network_unreachable"
    """Network connectivity issues"""
    
    BROKER_API_UNAVAILABLE = "broker_api_unavailable"
    """Broker API is unavailable or unreachable"""
    
    RATE_LIMITED = "rate_limited"
    """Request rate limit exceeded"""
    
    # AUTHORIZATION category errors
    INVALID_API_KEYS = "invalid_api_keys"
    """API keys are invalid or expired"""
    
    PERMISSION_DENIED = "permission_denied"
    """Insufficient permissions for this operation"""
    
    # CONFIGURATION category errors
    MISSING_CONFIGURATION = "missing_configuration"
    """Required configuration is missing"""
    
    UNSUPPORTED_ASSET_CLASS = "unsupported_asset_class"
    """Asset class is not supported"""