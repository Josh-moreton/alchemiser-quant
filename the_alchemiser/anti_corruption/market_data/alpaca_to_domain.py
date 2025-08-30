"""Business Unit: utilities | Status: current

Anti-corruption layer for Alpaca market data to domain object mapping.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.domain.value_objects.market_bar_vo import MarketBarVO


class AlpacaMarketDataMapper:
    """Maps Alpaca API responses to domain value objects."""
    
    def alpaca_bar_to_market_bar_vo(
        self, 
        alpaca_bar: Any, 
        symbol: Symbol, 
        timeframe: str
    ) -> MarketBarVO:
        """Convert Alpaca bar to MarketBarVO.
        
        Args:
            alpaca_bar: Alpaca bar object from API
            symbol: Symbol value object
            timeframe: String timeframe identifier
            
        Returns:
            MarketBarVO with converted data
            
        Raises:
            ValueError: Invalid price data

        """
        return MarketBarVO(
            symbol=symbol,
            timestamp=datetime.fromisoformat(str(alpaca_bar.timestamp).replace("Z", "+00:00")),
            open_price=Decimal(str(alpaca_bar.open)),
            high_price=Decimal(str(alpaca_bar.high)),
            low_price=Decimal(str(alpaca_bar.low)),
            close_price=Decimal(str(alpaca_bar.close)),
            volume=Decimal(str(alpaca_bar.volume)),
            timeframe=timeframe
        )