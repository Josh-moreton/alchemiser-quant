"""Business Unit: portfolio assessment & management | Status: current

Trading data adapter that wraps TradingServiceManager for Portfolio context.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.application.trading.service_manager import TradingServiceManager
from the_alchemiser.portfolio.application.ports import TradingDataPort


class TradingServiceDataAdapter(TradingDataPort):
    """Adapter that wraps TradingServiceManager to provide trading data via port.
    
    This adapter encapsulates the dependency on TradingServiceManager and prevents
    Portfolio application services from directly importing anti-corruption modules.
    """
    
    def __init__(self, trading_service_manager: TradingServiceManager) -> None:
        """Initialize with trading service manager.
        
        Args:
            trading_service_manager: Trading service manager to wrap
            
        """
        self._trading_service_manager = trading_service_manager
        
    def get_all_positions(self) -> list[dict[str, Any]]:
        """Get all current position holdings from trading system.
        
        Returns:
            List of position data from trading system
            
        Raises:
            TradingDataError: Position data retrieval failure
            
        """
        return self._trading_service_manager.get_all_positions()