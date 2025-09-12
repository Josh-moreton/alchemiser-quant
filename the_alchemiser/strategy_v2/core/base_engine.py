"""Business Unit: strategy | Status: current

Base strategy engine implementation.

Provides a concrete base class for strategy engines to inherit from,
implementing common initialization patterns.
"""

from __future__ import annotations

from the_alchemiser.shared.types.market_data_port import MarketDataPort


class BaseStrategyEngine:
    """Base implementation for strategy engines."""
    
    def __init__(self, name: str, market_data_port: MarketDataPort) -> None:
        """Initialize base strategy engine.
        
        Args:
            name: Strategy name
            market_data_port: Market data port for data access
        """
        import logging
        
        self.name = name
        self.strategy_name = name  # For backward compatibility
        self.market_data_port = market_data_port
        self.logger = logging.getLogger(f"{__name__}.{name}")