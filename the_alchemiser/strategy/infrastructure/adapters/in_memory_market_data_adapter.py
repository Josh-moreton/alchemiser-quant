"""Business Unit: strategy & signal generation | Status: current

In-memory market data adapter for testing and development.

TODO: Replace with production market data adapter (e.g., Alpaca, Yahoo Finance)
FIXME: This simplified adapter only provides deterministic test data
"""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.application.ports import MarketDataPort
from the_alchemiser.strategy.domain.exceptions import SymbolNotFoundError
from the_alchemiser.strategy.domain.value_objects.market_bar_vo import MarketBarVO


class InMemoryMarketDataAdapter(MarketDataPort):
    """Simple in-memory market data provider for testing.
    
    TODO: Replace with production adapter that connects to real market data API
    FIXME: Only supports limited symbols with synthetic data
    """
    
    def __init__(self) -> None:
        # TODO: Replace hardcoded symbols with configurable symbol list
        # FIXME: Pre-seed with some test data - replace with real data source
        self._bars: dict[str, list[MarketBarVO]] = {
            "AAPL": self._generate_test_bars("AAPL"),
            "MSFT": self._generate_test_bars("MSFT"),
            "GOOGL": self._generate_test_bars("GOOGL"),
        }
    
    def get_latest_bar(self, symbol: Symbol, timeframe: str) -> MarketBarVO:
        """Get most recent bar from test data."""
        bars = self._bars.get(symbol.value, [])
        if not bars:
            raise SymbolNotFoundError(f"No data for symbol: {symbol}")
        return bars[-1]
    
    def get_history(
        self, 
        symbol: Symbol, 
        timeframe: str, 
        limit: int,
        end_time: datetime | None = None
    ) -> Sequence[MarketBarVO]:
        """Get historical bars from test data."""
        bars = self._bars.get(symbol.value, [])
        if not bars:
            raise SymbolNotFoundError(f"No data for symbol: {symbol}")
        
        # Apply end_time filter if provided
        if end_time:
            bars = [bar for bar in bars if bar.timestamp <= end_time]
        
        # Return last 'limit' bars
        return bars[-limit:] if len(bars) > limit else bars
    
    def _generate_test_bars(self, symbol_str: str) -> list[MarketBarVO]:
        """Generate deterministic test data.
        
        TODO: Replace with real historical data fetcher
        FIXME: Current implementation generates synthetic uptrend data only
        """
        bars = []
        base_price = Decimal("100.00")
        base_time = datetime.now(UTC) - timedelta(days=100)
        
        for i in range(100):
            timestamp = base_time + timedelta(days=i)
            price = base_price + Decimal(str(i * 0.5))  # TODO: Replace linear trend with realistic price movements
            
            bar = MarketBarVO(
                symbol=Symbol(symbol_str),
                timestamp=timestamp,
                open_price=price,
                high_price=price + Decimal("2.00"),
                low_price=price - Decimal("1.00"),
                close_price=price + Decimal("0.50"),
                volume=Decimal("1000000"),
                timeframe="1Day"
            )
            bars.append(bar)
        
        return bars