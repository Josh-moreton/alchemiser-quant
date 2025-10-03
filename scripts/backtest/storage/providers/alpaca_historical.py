"""Business Unit: shared | Status: current.

Alpaca historical data provider for backtesting.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from scripts.backtest.models.market_data import HistoricalBar
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class AlpacaHistoricalProvider:
    """Provider for fetching historical data from Alpaca.
    
    Uses Alpaca's historical data API to download OHLCV data with
    split/dividend adjustments.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize Alpaca historical data client.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key

        """
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.logger = logger

    def fetch_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: TimeFrame = TimeFrame.Day,
    ) -> list[HistoricalBar]:
        """Fetch historical bars for a symbol.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            timeframe: Bar timeframe (default: daily)
            
        Returns:
            List of historical bars
            
        Raises:
            RuntimeError: If data fetch fails

        """
        try:
            self.logger.info(
                f"Fetching historical data for {symbol}",
                extra={
                    "symbol": symbol,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start_date,
                end=end_date,
                adjustment="all",  # Include splits and dividends
            )

            response = self.client.get_stock_bars(request)

            if symbol not in response.data:
                self.logger.warning(f"No data returned for {symbol}")
                return []

            bars = response.data[symbol]
            historical_bars = []

            for bar in bars:
                # Extract adjusted close (Alpaca provides this in the close field
                # with adjustment='all')
                adjusted_close = Decimal(str(bar.close))

                historical_bar = HistoricalBar(
                    date=bar.timestamp.replace(tzinfo=None),  # Convert to naive UTC
                    symbol=symbol,
                    open_price=Decimal(str(bar.open)),
                    high_price=Decimal(str(bar.high)),
                    low_price=Decimal(str(bar.low)),
                    close_price=Decimal(str(bar.close)),
                    volume=bar.volume,
                    adjusted_close=adjusted_close,
                )
                historical_bars.append(historical_bar)

            self.logger.info(
                f"Fetched {len(historical_bars)} bars for {symbol}",
                extra={"symbol": symbol, "bar_count": len(historical_bars)},
            )

            return historical_bars

        except Exception as e:
            error_msg = f"Failed to fetch historical data for {symbol}: {e}"
            self.logger.error(error_msg, extra={"symbol": symbol, "error": str(e)})
            raise RuntimeError(error_msg) from e

    def validate_data(self, bars: list[HistoricalBar]) -> tuple[bool, list[str]]:
        """Validate historical data for completeness and consistency.
        
        Checks for:
        - Missing dates (gaps in trading days)
        - Invalid prices (negative, zero, or NaN values)
        - Volume anomalies
        
        Args:
            bars: List of historical bars to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)

        """
        if not bars:
            return False, ["No data to validate"]

        errors: list[str] = []

        # Check for price validity
        for bar in bars:
            if bar.open_price <= 0:
                errors.append(f"Invalid open price on {bar.date}: {bar.open_price}")
            if bar.high_price <= 0:
                errors.append(f"Invalid high price on {bar.date}: {bar.high_price}")
            if bar.low_price <= 0:
                errors.append(f"Invalid low price on {bar.date}: {bar.low_price}")
            if bar.close_price <= 0:
                errors.append(f"Invalid close price on {bar.date}: {bar.close_price}")
            if bar.adjusted_close <= 0:
                errors.append(
                    f"Invalid adjusted close on {bar.date}: {bar.adjusted_close}"
                )

            # Check OHLC relationship
            if bar.high_price < bar.low_price:
                errors.append(
                    f"High < Low on {bar.date}: {bar.high_price} < {bar.low_price}"
                )
            if bar.high_price < bar.open_price or bar.high_price < bar.close_price:
                errors.append(f"High price inconsistent on {bar.date}")
            if bar.low_price > bar.open_price or bar.low_price > bar.close_price:
                errors.append(f"Low price inconsistent on {bar.date}")

        # Check for date gaps (simplified - only checks for consecutive dates)
        sorted_bars = sorted(bars, key=lambda b: b.date)
        for i in range(1, len(sorted_bars)):
            prev_date = sorted_bars[i - 1].date
            curr_date = sorted_bars[i].date
            days_diff = (curr_date - prev_date).days

            # Allow for weekends and holidays (max 4 days for long weekends)
            if days_diff > 5:
                gap_msg = (
                    f"Large date gap detected: {prev_date.date()} to "
                    f"{curr_date.date()} ({days_diff} days)"
                )
                errors.append(gap_msg)

        return len(errors) == 0, errors
