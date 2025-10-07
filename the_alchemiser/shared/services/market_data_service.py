"""Business Unit: shared | Status: current.

Market data service providing domain-facing interface.

This service acts as a port between orchestrators and the market data infrastructure,
handling input normalization, error mapping, and providing a clean domain interface.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from secrets import randbelow
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.utils.alpaca_error_handler import (
    AlpacaErrorHandler,
    HTTPError,
    RequestException,
    RetryException,
)
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
            from the_alchemiser.shared.errors.exceptions import DataProviderError

            raise DataProviderError(f"Market data fetch failed for {symbol}: {e}") from e

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote with error handling.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote model or None if not available

        Note: This still relies on the legacy QuoteModel from shared.types.quote. The
        enhanced QuoteModel in shared.types.market_data offers bid_size/ask_size for
        richer depth analytics, and migrating to it will unblock improved spread
        calculations.

        """
        try:
            # Convert Symbol to string for API call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            # Call Alpaca API directly to avoid circular calls (AlpacaManager delegates back to us)
            from alpaca.data.requests import StockLatestQuoteRequest

            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol_str])
            quotes = self._repo.get_data_client().get_stock_latest_quote(request)
            quote = quotes.get(symbol_str)

            if quote:
                from decimal import Decimal

                bid = float(getattr(quote, "bid_price", 0))
                ask = float(getattr(quote, "ask_price", 0))

                if bid > 0 and ask > 0:
                    return QuoteModel(ts=None, bid=Decimal(str(bid)), ask=Decimal(str(ask)))
                if bid > 0:
                    return QuoteModel(ts=None, bid=Decimal(str(bid)), ask=Decimal(str(bid)))
                if ask > 0:
                    return QuoteModel(ts=None, bid=Decimal(str(ask)), ask=Decimal(str(ask)))

            return None

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

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if not available

        """
        from the_alchemiser.shared.utils.price_discovery_utils import (
            get_current_price_from_quote,
        )

        try:
            return get_current_price_from_quote(self._repo, symbol)
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        """
        try:
            prices = {}
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
                else:
                    self.logger.warning(f"Could not get price for {symbol}")
            return prices
        except Exception as e:
            self.logger.error(f"Failed to get current prices for {symbols}: {e}")
            raise

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed

        """
        try:
            # Import dependencies locally to avoid circular imports
            from alpaca.data.requests import StockLatestQuoteRequest

            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._repo.get_data_client().get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                # Use Pydantic model_dump() for consistent field names
                quote_dict = quote.model_dump()
                # Ensure we have symbol in the output
                quote_dict["symbol"] = symbol
                return quote_dict
            return None
        except (RetryException, HTTPError) as e:
            # These are specific API failures that should not be silent
            error_msg = f"Alpaca API failure getting quote for {symbol}: {e}"
            if "429" in str(e) or "rate limit" in str(e).lower():
                error_msg = f"Alpaca API rate limit exceeded getting quote for {symbol}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except RequestException as e:
            # Other network/HTTP errors
            error_msg = f"Network error getting quote for {symbol}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            self.logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol with retry logic.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)

        Returns:
            List of dictionaries with bar data using Pydantic model field names

        """
        # Import dependencies locally to avoid circular imports
        from alpaca.data.requests import StockBarsRequest

        # Retry with exponential backoff and jitter for transient upstream failures
        max_retries = 3
        base_sleep = 0.6  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Resolve timeframe and create request
                resolved_timeframe = self._resolve_timeframe_core(timeframe)

                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)

                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=resolved_timeframe,
                    start=start_dt,
                    end=end_dt,
                )

                # Make API call and extract bars
                response = self._repo.get_data_client().get_stock_bars(request)
                bars_obj = self._extract_bars_from_response_core(response, symbol)

                if not bars_obj:
                    if self._should_raise_missing_data_error_core(
                        start_date, end_date, timeframe, symbol
                    ):
                        error_msg = f"No historical data returned for {symbol}"
                        # Treat as transient in retry path, many times this is upstream glitch
                        raise RuntimeError(error_msg)
                    return []

                # Convert bars to dictionaries and return
                return self._convert_bars_to_dicts_core(bars_obj, symbol)

            except (RetryException, HTTPError, RequestException, Exception) as e:
                transient, reason = AlpacaErrorHandler.is_transient_error(e)
                last_attempt = attempt == max_retries

                if transient and not last_attempt:
                    jitter = 1.0 + 0.2 * (randbelow(1000) / 1000.0)
                    sleep_s = base_sleep * (2 ** (attempt - 1)) * jitter
                    self.logger.warning(
                        f"Transient market data error for {symbol} ({reason}); retry {attempt}/{max_retries} in {sleep_s:.2f}s"
                    )
                    time.sleep(sleep_s)
                    continue

                # Non-transient or out of retries: raise sanitized error
                summary = AlpacaErrorHandler.sanitize_error_message(e)
                msg = AlpacaErrorHandler.format_final_error_message(e, symbol, summary)
                self.logger.error(msg)
                raise RuntimeError(msg)

        # Defensive fallback for static analysis (should not be reached)
        return []

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
        from datetime import datetime

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

    def _resolve_timeframe_core(self, timeframe: str) -> Any:  # noqa: ANN401
        """Resolve timeframe string to Alpaca TimeFrame object.

        Args:
            timeframe: Timeframe string (case-insensitive)

        Returns:
            Alpaca TimeFrame object

        Raises:
            ValueError: If timeframe is not supported

        """
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

        timeframe_map = {
            "1min": TimeFrame(1, TimeFrameUnit.Minute),
            "5min": TimeFrame(5, TimeFrameUnit.Minute),
            "15min": TimeFrame(15, TimeFrameUnit.Minute),
            "1hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1day": TimeFrame(1, TimeFrameUnit.Day),
        }

        timeframe_lower = timeframe.lower()
        if timeframe_lower not in timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        return timeframe_map[timeframe_lower]

    def _extract_bars_from_response_core(self, response: object, symbol: str) -> Any | None:  # noqa: ANN401
        """Extract bars object from various possible response shapes.

        Args:
            response: API response object
            symbol: Stock symbol to extract bars for

        Returns:
            Bars object or None if not found

        """
        from typing import cast

        from the_alchemiser.shared.protocols.market_data import BarsIterable

        bars_obj: BarsIterable | None = None
        try:
            # Preferred: BarsBySymbol has a `.data` dict
            data_attr = getattr(response, "data", None)
            if isinstance(data_attr, dict) and symbol in data_attr:
                bars_obj = cast(BarsIterable, data_attr[symbol])
            # Some SDKs expose attributes per symbol
            elif hasattr(response, symbol):
                bars_obj = cast(BarsIterable, getattr(response, symbol))
            # Fallback: mapping-like access
            elif isinstance(response, dict) and symbol in response:
                bars_obj = cast(BarsIterable, response[symbol])
        except Exception:
            bars_obj = None

        return bars_obj

    def _convert_bars_to_dicts_core(self, bars_obj: Any, symbol: str) -> list[dict[str, Any]]:  # noqa: ANN401
        """Convert bars object to list of dictionaries using Pydantic model_dump.

        Args:
            bars_obj: Bars object from API response
            symbol: Stock symbol for logging

        Returns:
            List of dictionaries with bar data

        """
        bars = list(bars_obj)
        self.logger.debug(f"Successfully retrieved {len(bars)} bars for {symbol}")

        result: list[dict[str, Any]] = []
        for bar in bars:
            try:
                bar_dict = bar.model_dump()
                result.append(bar_dict)
            except Exception as e:  # pragma: no cover - conversion resilience
                self.logger.warning(f"Failed to convert bar for {symbol}: {e}")
                continue
        return result

    def _should_raise_missing_data_error_core(
        self, start_date: str, end_date: str, timeframe: str, symbol: str
    ) -> bool:
        """Check if missing data should raise an error for retry.

        Args:
            start_date: Start date string
            end_date: End date string
            timeframe: Timeframe string
            symbol: Stock symbol for logging

        Returns:
            True if should raise error (will be retried), False if should return empty list

        """
        start_dt_local = datetime.fromisoformat(start_date)
        end_dt_local = datetime.fromisoformat(end_date)
        days_requested = (end_dt_local - start_dt_local).days

        # For daily data over a reasonable period, we should expect some bars
        if days_requested > 5 and timeframe.lower() == "1day":
            return True

        self.logger.warning(f"No historical data found for {symbol}")
        return False

    def _convert_to_bar_model(self, bar_data: Any, symbol: str) -> BarModel:  # noqa: ANN401
        """Convert raw bar data to BarModel.

        Args:
            bar_data: Raw bar data from repository (dictionary from Pydantic model_dump())
            symbol: Symbol string

        Returns:
            BarModel instance

        """
        from datetime import datetime

        if isinstance(bar_data, dict):
            # Dictionary format from Pydantic model_dump() with full field names
            timestamp = bar_data.get("timestamp", datetime.now(UTC))
            open_price = bar_data.get("open", 0)
            high_price = bar_data.get("high", 0)
            low_price = bar_data.get("low", 0)
            close_price = bar_data.get("close", 0)
            volume = bar_data.get("volume", 0)

            return BarModel(
                symbol=symbol,
                timestamp=(timestamp if isinstance(timestamp, datetime) else datetime.now(UTC)),
                open=float(open_price),
                high=float(high_price),
                low=float(low_price),
                close=float(close_price),
                volume=int(volume),
            )

        # This should not happen with clean Pydantic model_dump() data
        raise ValueError(f"Expected dictionary from Pydantic model_dump(), got {type(bar_data)}")
