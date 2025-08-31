"""Business Unit: portfolio assessment & management | Status: current

Market data adapter that wraps TradingServiceManager for Portfolio context.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.application.trading.service_manager import TradingServiceManager
from the_alchemiser.portfolio.application.ports import MarketDataPort
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


class TradingServiceMarketDataAdapter(MarketDataPort):
    """Adapter that wraps TradingServiceManager to provide market data via port.
    
    This adapter encapsulates the dependency on TradingServiceManager and prevents
    Portfolio application services from directly importing anti-corruption modules.
    """
    
    def __init__(self, trading_service_manager: TradingServiceManager) -> None:
        """Initialize with trading service manager.
        
        Args:
            trading_service_manager: Trading service manager to wrap
            
        """
        self._trading_service_manager = trading_service_manager
        
    def get_current_price(self, symbol: Symbol) -> Decimal:
        """Get current market price for symbol.
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Current market price
            
        Raises:
            MarketDataError: Price lookup failure
            
        """
        # TODO: Implement current price lookup via trading service manager
        # For now, return a placeholder to break the direct import dependency
        raise NotImplementedError("Current price lookup not yet implemented")
        
    def get_portfolio_value(self) -> dict[str, Any]:
        """Get current total portfolio value.
        
        Returns:
            Portfolio value information
            
        Raises:
            MarketDataError: Portfolio value calculation failure
            
        """
        return self._trading_service_manager.get_portfolio_value()