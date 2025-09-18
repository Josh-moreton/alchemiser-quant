"""Business Unit: shared | Status: current.

Alpaca broker integration package.

This package provides a modular implementation of Alpaca broker functionality,
decomposed from the original monolithic alpaca_manager.py for better maintainability,
testability, and separation of concerns.

Core modules:
- client: Base client configuration and authentication
- config: Environment and configuration management
- accounts: Account information and portfolio data
- positions: Position management and tracking
- orders: Order placement, management, and execution
- market_data: Historical and real-time market data
- streaming: WebSocket connections and event handling
- exceptions: Normalized error handling
- models: Data transfer objects and type definitions
- mappers: Response transformation utilities
- utils: Shared utility functions
- rate_limit: Request rate limiting
- retry: Retry policies and backoff strategies

The original AlpacaManager is maintained as a facade for backward compatibility.
"""

from __future__ import annotations

# The facade import is handled in the parent package to manage dependencies
# Individual modules can be imported directly for new code:
# from .config import AlpacaConfig
# from .client import AlpacaClient
# etc.

__all__ = []