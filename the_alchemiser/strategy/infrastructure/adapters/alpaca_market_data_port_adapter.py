"""Business Unit: strategy & signal generation | Status: current

Alpaca market data adapter implementing MarketDataPort.
"""

import logging
from collections.abc import Sequence
from datetime import datetime

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from the_alchemiser.anti_corruption.market_data.alpaca_to_domain import AlpacaMarketDataMapper
from the_alchemiser.shared_kernel.exceptions.base_exceptions import DataAccessError
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.application.ports import MarketDataPort
from the_alchemiser.strategy.domain.exceptions import SymbolNotFoundError
from the_alchemiser.strategy.domain.value_objects.market_bar_vo import MarketBarVO

logger = logging.getLogger(__name__)

class AlpacaMarketDataAdapter(MarketDataPort):
    """Alpaca market data adapter with error handling and mapping."""
    
    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize Alpaca client with credentials.
        
        Args:
            api_key: Alpaca API key from environment
            secret_key: Alpaca secret key from environment

        """
        self._client = StockHistoricalDataClient(api_key, secret_key)
        self._mapper = AlpacaMarketDataMapper()
        self._logger = logger.bind(component="AlpacaMarketDataAdapter")
    
    def get_latest_bar(self, symbol: Symbol, timeframe: str) -> MarketBarVO:
        """Get most recent price bar from Alpaca.
        
        Args:
            symbol: Symbol to fetch (e.g., AAPL, MSFT)
            timeframe: Period (1Day, 1Hour, 15Min, 5Min, 1Min)
            
        Returns:
            MarketBarVO with OHLCV data
            
        Raises:
            DataAccessError: Alpaca API failure
            SymbolNotFoundError: Invalid symbol

        """
        try:
            # Convert timeframe to Alpaca format
            alpaca_timeframe = self._convert_timeframe(timeframe)
            
            # Request last 1 bar
            request = StockBarsRequest(
                symbol_or_symbols=[symbol.value],
                timeframe=alpaca_timeframe,
                limit=1,
                end=datetime.utcnow()
            )
            
            self._logger.info(
                "Fetching latest bar",
                symbol=symbol.value,
                timeframe=timeframe
            )
            
            response = self._client.get_stock_bars(request)
            
            if symbol.value not in response.data or not response.data[symbol.value]:
                raise SymbolNotFoundError(
                    f"No data returned for symbol: {symbol.value}"
                )
            
            # Get the latest (only) bar
            alpaca_bar = response.data[symbol.value][0]
            
            # Convert via anti-corruption layer
            market_bar = self._mapper.alpaca_bar_to_market_bar_vo(
                alpaca_bar, symbol, timeframe
            )
            
            self._logger.debug(
                "Successfully fetched latest bar",
                symbol=symbol.value,
                timestamp=market_bar.timestamp,
                close_price=str(market_bar.close_price)
            )
            
            return market_bar
            
        except SymbolNotFoundError:
            raise  # Re-raise domain exception as-is
        except Exception as e:
            self._logger.error(
                "Failed to fetch latest bar",
                symbol=symbol.value,
                timeframe=timeframe,
                error=str(e)
            )
            raise DataAccessError(
                f"Alpaca API error fetching latest bar for {symbol.value}: {e}"
            ) from e
    
    def get_history(
        self, 
        symbol: Symbol, 
        timeframe: str, 
        limit: int,
        end_time: datetime | None = None
    ) -> Sequence[MarketBarVO]:
        """Get historical price bars from Alpaca.
        
        Args:
            symbol: Symbol to fetch
            timeframe: Period (1Day, 1Hour, etc.)
            limit: Maximum bars (1-10000)
            end_time: End timestamp (None = latest)
            
        Returns:
            Sequence of MarketBarVO ordered chronologically
            
        Raises:
            DataAccessError: Alpaca API failure
            SymbolNotFoundError: Invalid symbol
            ValueError: Invalid parameters

        """
        if not (1 <= limit <= 10000):
            raise ValueError(f"Limit must be 1-10000, got: {limit}")
        
        try:
            alpaca_timeframe = self._convert_timeframe(timeframe)
            
            request = StockBarsRequest(
                symbol_or_symbols=[symbol.value],
                timeframe=alpaca_timeframe,
                limit=limit,
                end=end_time or datetime.utcnow()
            )
            
            self._logger.info(
                "Fetching historical bars",
                symbol=symbol.value,
                timeframe=timeframe,
                limit=limit,
                end_time=end_time
            )
            
            response = self._client.get_stock_bars(request)
            
            if symbol.value not in response.data or not response.data[symbol.value]:
                raise SymbolNotFoundError(
                    f"No historical data for symbol: {symbol.value}"
                )
            
            # Convert all bars via anti-corruption layer
            bars = []
            for alpaca_bar in response.data[symbol.value]:
                market_bar = self._mapper.alpaca_bar_to_market_bar_vo(
                    alpaca_bar, symbol, timeframe
                )
                bars.append(market_bar)
            
            # Ensure chronological order (oldest first)
            bars.sort(key=lambda bar: bar.timestamp)
            
            self._logger.debug(
                "Successfully fetched historical bars",
                symbol=symbol.value,
                returned_count=len(bars),
                first_timestamp=bars[0].timestamp if bars else None,
                last_timestamp=bars[-1].timestamp if bars else None
            )
            
            return bars
            
        except (SymbolNotFoundError, ValueError):
            raise  # Re-raise domain exceptions as-is
        except Exception as e:
            self._logger.error(
                "Failed to fetch historical bars",
                symbol=symbol.value,
                timeframe=timeframe,
                limit=limit,
                error=str(e)
            )
            raise DataAccessError(
                f"Alpaca API error fetching history for {symbol.value}: {e}"
            ) from e
    
    def _convert_timeframe(self, timeframe: str) -> TimeFrame:
        """Convert string timeframe to Alpaca TimeFrame object.
        
        Args:
            timeframe: String like "1Day", "1Hour", "15Min"
            
        Returns:
            Alpaca TimeFrame object
            
        Raises:
            ValueError: Unsupported timeframe

        """
        timeframe_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "30Min": TimeFrame(30, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1Day": TimeFrame(1, TimeFrameUnit.Day),
            "1Week": TimeFrame(1, TimeFrameUnit.Week),
            "1Month": TimeFrame(1, TimeFrameUnit.Month)
        }
        
        if timeframe not in timeframe_map:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}. "
                f"Supported: {list(timeframe_map.keys())}"
            )
        
        return timeframe_map[timeframe]