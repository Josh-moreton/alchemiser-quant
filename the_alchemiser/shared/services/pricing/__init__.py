"""Business Unit: shared | Status: current.

Real-time pricing service package with modular architecture.

This package provides real-time stock price updates via Alpaca's WebSocket streams
for accurate limit order pricing. The monolithic service has been split into
focused modules for better maintainability and testability.

Public API:
    RealTimePricingService: Main service facade maintaining backward compatibility
    RealTimeQuote: Legacy quote data structure (for compatibility)
"""

from .compat import convert_quote_model_to_legacy, get_best_price_from_quote, validate_quote_spread
from .facade import RealTimePricingService
from .models import RealTimeQuote

__all__ = [
    "RealTimePricingService",
    "RealTimeQuote",
    "convert_quote_model_to_legacy",
    "get_best_price_from_quote", 
    "validate_quote_spread",
]