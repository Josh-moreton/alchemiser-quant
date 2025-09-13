"""Business Unit: shared | Status: current.

Market data service providing domain-facing interface.

This service acts as a port between orchestrators and the market data infrastructure,
handling input normalization, error mapping, and providing a clean domain interface.
"""

from __future__ import annotations

from datetime import UTC
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager


class MarketDataService(MarketDataPort):
    """Service providing market data access with normalization and error handling.

    This service wraps the AlpacaManager and provides a clean domain interface
    that handles timeframe normalization, error translation, and other concerns
    that shouldn't be in the orchestration layer.
    """

    def __init__(self, market_data_repo: AlpacaManager) -> None:
        """Initialize with market data repository.

        Args:
            market_data_repo: The underlying market data repository (AlpacaManager)

        """
        self._repo = market_data_repo
        self.logger = get_logger(__name__)

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Get historical bars with timeframe normalization.

        Args:
            symbol: Symbol to get bars for
            period: Period string (e.g., "1Y", "6M")
            timeframe: Timeframe string (normalized to proper format)

        Returns:
            List of bar models

        Raises:
            DataProviderError: If data fetch fails after normalization

        """
        try:
            # Normalize timeframe format (e.g., "1day" -> "1Day")
            normalized_timeframe = self._normalize_timeframe(timeframe)

            # Convert Symbol to string for repository call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            # Convert period to date range for AlpacaManager
            start_date, end_date = self._period_to_dates(period)

            # Call AlpacaManager's get_historical_bars method
            bars_data = self._repo.get_historical_bars(
                symbol_str, start_date, end_date, normalized_timeframe
            )

            # Convert to BarModel list if needed
            if isinstance(bars_data, list):
                return [self._convert_to_bar_model(bar, symbol_str) for bar in bars_data]

            return []

        except Exception as e:
            self.logger.error(f"Failed to get bars for {symbol} ({period}, {timeframe}): {e}")
            # Re-raise with domain-appropriate error type
            from the_alchemiser.shared.types.exceptions import DataProviderError

            raise DataProviderError(f"Market data fetch failed for {symbol}: {e}") from e

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote with error handling.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote model or None if not available

        """
        try:
            # Convert Symbol to string for repository call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            quote_data = self._repo.get_latest_quote(symbol_str)
            if quote_data is None:
                return None

            # Convert tuple to QuoteModel if needed
            if isinstance(quote_data, tuple) and len(quote_data) == 2:
                from decimal import Decimal

                bid, ask = quote_data
                return QuoteModel(ts=None, bid=Decimal(str(bid)), ask=Decimal(str(ask)))

            return quote_data

        except Exception as e:
            self.logger.warning(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price with error handling.

        Args:
            symbol: Symbol to get mid price for

        Returns:
            Mid price or None if not available

        """
        try:
            # Convert Symbol to string for repository call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            # Use get_current_price method which should return mid price
            return self._repo.get_current_price(symbol_str)

        except Exception as e:
            self.logger.warning(f"Failed to get mid price for {symbol}: {e}")
            return None

    def _normalize_timeframe(self, timeframe: str) -> str:
        """Normalize timeframe format to match expected values.

        Handles case variations like "1day" -> "1Day", "1min" -> "1Min"

        Args:
            timeframe: Input timeframe string

        Returns:
            Normalized timeframe string

        """
        # Mapping of lowercase timeframe to proper case
        timeframe_mapping = {
            "1min": "1Min",
            "5min": "5Min",
            "15min": "15Min",
            "1hour": "1Hour",
            "1day": "1Day",
        }

        normalized = timeframe_mapping.get(timeframe.lower())
        if normalized:
            return normalized

        # If no mapping found, return as-is and let repository handle validation
        return timeframe

    def _period_to_dates(self, period: str) -> tuple[str, str]:
        """Convert period string to start and end dates.

        Args:
            period: Period string like "1Y", "6M", "30D"

        Returns:
            Tuple of (start_date, end_date) as strings

        """
        from datetime import datetime, timedelta

        end_date = datetime.now(UTC)

        # Simple period mapping
        if "Y" in period:
            days = int(period.replace("Y", "")) * 365
        elif "M" in period:
            days = int(period.replace("M", "")) * 30
        elif "D" in period:
            days = int(period.replace("D", ""))
        else:
            days = 365  # Default to 1 year

        start_date = end_date - timedelta(days=days)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def _convert_to_bar_model(self, bar_data: Any, symbol: str) -> BarModel:  # noqa: ANN401
        """Convert raw bar data to BarModel.

        Args:
            bar_data: Raw bar data from repository (now using full field names from Pydantic models)
            symbol: Symbol string

        Returns:
            BarModel instance

        """
        from datetime import datetime

        # Handle different bar data formats
        if hasattr(bar_data, "__dict__"):
            # Object with attributes (Pydantic model or similar)
            return BarModel(
                symbol=symbol,
                timestamp=getattr(bar_data, "timestamp", datetime.now(UTC)),
                open=float(getattr(bar_data, "open", 0)),
                high=float(getattr(bar_data, "high", 0)),
                low=float(getattr(bar_data, "low", 0)),
                close=float(getattr(bar_data, "close", 0)),
                volume=int(getattr(bar_data, "volume", 0)),
            )

        if isinstance(bar_data, dict):
            # Dictionary format - now using full field names from Pydantic model_dump()
            timestamp = bar_data.get("timestamp", datetime.now(UTC))
            open_price = bar_data.get("open", 0)
            high_price = bar_data.get("high", 0)
            low_price = bar_data.get("low", 0)
            close_price = bar_data.get("close", 0)
            volume = bar_data.get("volume", 0)

            return BarModel(
                symbol=symbol,
                timestamp=timestamp if isinstance(timestamp, datetime) else datetime.now(UTC),
                open=float(open_price),
                high=float(high_price),
                low=float(low_price),
                close=float(close_price),
                volume=int(volume),
            )

        # Fallback - create empty bar
        return BarModel(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            open=0.0,
            high=0.0,
            low=0.0,
            close=0.0,
            volume=0,
        )
