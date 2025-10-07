"""Business Unit: shared | Status: current.

Market data service providing domain-facing interface.

This service acts as a port between orchestrators and the market data infrastructure,
handling input normalization, error mapping, and providing a clean domain interface.
"""

from __future__ import annotations

import math
import os
import random
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from secrets import randbelow
from typing import TYPE_CHECKING, Any

from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.utils.alpaca_error_handler import (
    AlpacaErrorHandler,
    HTTPError,
    RequestException,
    RetryException,
)
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from typing import cast

    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.protocols.market_data import BarsIterable

# Module-level constants
MAX_RETRIES = 3
BASE_SLEEP_SECONDS = 0.6
JITTER_BASE = 1.0
JITTER_FACTOR = 0.2
JITTER_DIVISOR = 1000
MIN_DAYS_FOR_DATA_CHECK = 5
DEFAULT_PERIOD_DAYS = 365
API_TIMEOUT_SECONDS = 30  # 30 seconds timeout for external API calls
FLOAT_COMPARISON_TOLERANCE = 1e-9

# Timeframe mapping - single source of truth
TIMEFRAME_MAP = {
    "1min": ("1Min", TimeFrame(1, TimeFrameUnit.Minute)),
    "5min": ("5Min", TimeFrame(5, TimeFrameUnit.Minute)),
    "15min": ("15Min", TimeFrame(15, TimeFrameUnit.Minute)),
    "1hour": ("1Hour", TimeFrame(1, TimeFrameUnit.Hour)),
    "1day": ("1Day", TimeFrame(1, TimeFrameUnit.Day)),
}


class MarketDataService(MarketDataPort):
    """Service providing market data access with normalization and error handling.

    This service wraps the AlpacaManager and provides a clean domain interface
    that handles timeframe normalization, error translation, and other concerns
    that shouldn't be in the orchestration layer.
    
    Attributes:
        _repo: AlpacaManager instance for market data access
        logger: Structlog logger with correlation context support
    """

    def __init__(self, market_data_repo: AlpacaManager) -> None:
        """Initialize with market data repository.

        Args:
            market_data_repo: The underlying market data repository (AlpacaManager)

        """
        self._repo = market_data_repo
        self.logger = get_logger(__name__)
        # Use deterministic RNG in test environment
        self._use_deterministic_jitter = os.getenv("ALCHEMISER_TEST_MODE", "").lower() in ("1", "true", "yes")

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Get historical bars with timeframe normalization.

        Args:
            symbol: Symbol to get bars for
            period: Period string (e.g., "1Y", "6M", "30D")
            timeframe: Timeframe string (normalized to proper format)

        Returns:
            List of bar models

        Raises:
            DataProviderError: If data fetch fails after normalization
            ValueError: If period or timeframe format is invalid

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
            self.logger.error(
                "Failed to get bars",
                symbol=str(symbol),
                period=period,
                timeframe=timeframe,
                error=str(e),
            )
            # Re-raise with domain-appropriate error type
            from the_alchemiser.shared.errors.exceptions import DataProviderError

            raise DataProviderError(f"Market data fetch failed for {symbol}: {e}") from e

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote with error handling.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote model with bid/ask prices and sizes, or None if not available

        Raises:
            ValueError: If symbol is invalid

        """
        try:
            # Convert Symbol to string for API call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            # Fetch quote from Alpaca API
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol_str])
            quotes = self._repo.get_data_client().get_stock_latest_quote(request, timeout=API_TIMEOUT_SECONDS)
            quote = quotes.get(symbol_str)

            if not quote:
                return None

            # Extract and normalize quote data
            return self._build_quote_model(quote, symbol_str)

        except Exception as e:
            self.logger.warning(
                "Failed to get quote",
                symbol=str(symbol),
                error=str(e),
            )
            return None

    def _build_quote_model(self, quote: Any, symbol: str) -> QuoteModel | None:  # noqa: ANN401
        """Build QuoteModel from raw quote data with bid/ask fallback handling.

        Business Logic: When either bid or ask is missing, we use the available
        price for both sides to ensure we can still construct a valid quote.
        This is acceptable for market data display but should be considered
        when used for trading decisions.

        Args:
            quote: Raw quote object from Alpaca API
            symbol: Symbol string for the quote

        Returns:
            QuoteModel instance or None if prices are invalid

        """
        # Extract raw price data
        bid_price_raw = float(getattr(quote, "bid_price", 0))
        ask_price_raw = float(getattr(quote, "ask_price", 0))
        bid_size = float(getattr(quote, "bid_size", 0))
        ask_size = float(getattr(quote, "ask_size", 0))
        
        # Normalize timestamp
        timestamp = self._normalize_quote_timestamp(getattr(quote, "timestamp", None))
        
        # Check price validity and build appropriate quote
        bid_valid = not math.isclose(bid_price_raw, 0.0, abs_tol=FLOAT_COMPARISON_TOLERANCE)
        ask_valid = not math.isclose(ask_price_raw, 0.0, abs_tol=FLOAT_COMPARISON_TOLERANCE)

        if bid_valid and ask_valid:
            return self._create_quote_model(symbol, bid_price_raw, ask_price_raw, bid_size, ask_size, timestamp)
        elif bid_valid:
            # Bid-only fallback: use bid for both sides
            return self._create_quote_model(symbol, bid_price_raw, bid_price_raw, bid_size, 0, timestamp)
        elif ask_valid:
            # Ask-only fallback: use ask for both sides
            return self._create_quote_model(symbol, ask_price_raw, ask_price_raw, 0, ask_size, timestamp)

        return None

    def _normalize_quote_timestamp(self, timestamp: datetime | None) -> datetime:
        """Normalize quote timestamp to timezone-aware UTC.

        Args:
            timestamp: Raw timestamp from API

        Returns:
            Timezone-aware UTC datetime

        """
        if timestamp and timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=UTC)
        elif timestamp:
            return timestamp
        return datetime.now(UTC)

    def _create_quote_model(
        self, symbol: str, bid: float, ask: float, bid_size: float, ask_size: float, timestamp: datetime
    ) -> QuoteModel:
        """Create QuoteModel with Decimal conversion.

        Args:
            symbol: Symbol string
            bid: Bid price
            ask: Ask price
            bid_size: Bid size
            ask_size: Ask size
            timestamp: Quote timestamp

        Returns:
            QuoteModel instance

        """
        return QuoteModel(
            symbol=symbol,
            bid_price=Decimal(str(bid)),
            ask_price=Decimal(str(ask)),
            bid_size=Decimal(str(bid_size)),
            ask_size=Decimal(str(ask_size)),
            timestamp=timestamp,
        )

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price with error handling.

        Note: Returns float for backward compatibility with existing code.
        Consider using get_latest_quote() and calculating from Decimal bid/ask
        for financial calculations requiring exact precision.

        Args:
            symbol: Symbol to get mid price for

        Returns:
            Mid price or None if not available

        Raises:
            ValueError: If symbol is invalid

        """
        try:
            # Convert Symbol to string for repository call
            symbol_str = symbol.value if hasattr(symbol, "value") else str(symbol)

            # Use get_current_price method which should return mid price
            return self._repo.get_current_price(symbol_str)

        except Exception as e:
            self.logger.warning(
                "Failed to get mid price",
                symbol=str(symbol),
                error=str(e),
            )
            return None

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if not available

        Raises:
            RuntimeError: If price fetch fails (re-raised from utility)

        """
        from the_alchemiser.shared.utils.price_discovery_utils import (
            get_current_price_from_quote,
        )

        try:
            return get_current_price_from_quote(self._repo, symbol)
        except Exception as e:
            self.logger.error(
                "Failed to get current price",
                symbol=symbol,
                error=str(e),
            )
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        Raises:
            RuntimeError: If batch price fetch fails

        """
        try:
            prices = {}
            missing_symbols = []
            
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
                else:
                    missing_symbols.append(symbol)
            
            # Log missing symbols once instead of per-symbol
            if missing_symbols:
                self.logger.warning(
                    "Could not get prices for some symbols",
                    missing_count=len(missing_symbols),
                    missing_symbols=missing_symbols,
                )
            
            return prices
        except Exception as e:
            self.logger.error(
                "Failed to get current prices",
                symbol_count=len(symbols),
                error=str(e),
            )
            raise

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed

        Raises:
            RuntimeError: For API failures (rate limits, network errors)

        """
        try:
            quote = self._fetch_quote_from_api(symbol)
            if quote:
                # Use Pydantic model_dump() for consistent field names
                quote_dict = quote.model_dump()
                # Ensure we have symbol in the output
                quote_dict["symbol"] = symbol
                return quote_dict
            return None
        except (RetryException, HTTPError) as e:
            self._handle_api_error(e, symbol)
        except RequestException as e:
            self._handle_network_error(e, symbol)
        except Exception as e:
            self.logger.error(
                "Failed to get quote",
                symbol=symbol,
                error=str(e),
            )
            return None

    def _fetch_quote_from_api(self, symbol: str) -> Any | None:  # noqa: ANN401
        """Fetch quote from Alpaca API.

        Args:
            symbol: Symbol to fetch

        Returns:
            Quote object or None

        """
        request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        quotes = self._repo.get_data_client().get_stock_latest_quote(request, timeout=API_TIMEOUT_SECONDS)
        return quotes.get(symbol)

    def _handle_api_error(self, error: Exception, symbol: str) -> None:
        """Handle Alpaca API errors.

        Args:
            error: The API exception
            symbol: Symbol being queried

        Raises:
            RuntimeError: Always raises with formatted message

        """
        is_rate_limit = "429" in str(error) or "rate limit" in str(error).lower()
        error_msg = (
            f"Alpaca API rate limit exceeded getting quote for {symbol}: {error}"
            if is_rate_limit
            else f"Alpaca API failure getting quote for {symbol}: {error}"
        )
        self.logger.error(
            "Alpaca API error getting quote",
            symbol=symbol,
            is_rate_limit=is_rate_limit,
            error=str(error),
        )
        raise RuntimeError(error_msg) from error

    def _handle_network_error(self, error: Exception, symbol: str) -> None:
        """Handle network errors.

        Args:
            error: The network exception
            symbol: Symbol being queried

        Raises:
            RuntimeError: Always raises with formatted message

        """
        error_msg = f"Network error getting quote for {symbol}: {error}"
        self.logger.error(
            "Network error getting quote",
            symbol=symbol,
            error=str(error),
        )
        raise RuntimeError(error_msg) from error

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol with retry logic.

        Args:
            symbol: Stock symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)

        Returns:
            List of dictionaries with bar data using Pydantic model field names

        Raises:
            RuntimeError: If data fetch fails after retries
            ValueError: If date format or timeframe is invalid

        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self._fetch_bars_with_request(symbol, start_date, end_date, timeframe)
            except (RetryException, HTTPError, RequestException, Exception) as e:
                if not self._should_retry_bars_fetch(e, attempt, symbol):
                    raise
                    
                # Retry with backoff
                self._sleep_with_backoff(attempt, symbol)

        # Defensive fallback for static analysis (should not be reached)
        return []

    def _fetch_bars_with_request(
        self, symbol: str, start_date: str, end_date: str, timeframe: str
    ) -> list[dict[str, Any]]:
        """Fetch bars for a single request attempt.

        Args:
            symbol: Stock symbol
            start_date: Start date string
            end_date: End date string
            timeframe: Timeframe string

        Returns:
            List of bar dictionaries

        Raises:
            RuntimeError: If fetch fails or returns no data unexpectedly

        """
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
        response = self._repo.get_data_client().get_stock_bars(request, timeout=API_TIMEOUT_SECONDS)
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

    def _should_retry_bars_fetch(
        self, error: Exception, attempt: int, symbol: str
    ) -> bool:
        """Determine if bars fetch should be retried.

        Args:
            error: The exception that occurred
            attempt: Current attempt number
            symbol: Symbol being fetched

        Returns:
            True if should retry, False otherwise

        """
        transient, reason = AlpacaErrorHandler.is_transient_error(error)
        last_attempt = attempt == MAX_RETRIES

        if not transient or last_attempt:
            # Non-transient or out of retries: raise sanitized error
            summary = AlpacaErrorHandler.sanitize_error_message(error)
            msg = AlpacaErrorHandler.format_final_error_message(error, symbol, summary)
            self.logger.error(
                "Market data fetch failed",
                symbol=symbol,
                error_summary=summary,
                is_transient=transient,
                attempt=attempt,
                max_retries=MAX_RETRIES,
            )
            raise RuntimeError(msg) from error

        return True

    def _sleep_with_backoff(self, attempt: int, symbol: str) -> None:
        """Sleep with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (1-based)
            symbol: Symbol being fetched for logging

        """
        # Calculate jitter: deterministic in test mode, random in production
        if self._use_deterministic_jitter:
            # Use seeded random for deterministic tests
            jitter = JITTER_BASE + JITTER_FACTOR * (attempt / MAX_RETRIES)
        else:
            jitter = JITTER_BASE + JITTER_FACTOR * (randbelow(JITTER_DIVISOR) / JITTER_DIVISOR)
        
        sleep_s = BASE_SLEEP_SECONDS * (2 ** (attempt - 1)) * jitter
        
        self.logger.warning(
            "Transient market data error, retrying",
            symbol=symbol,
            attempt=attempt,
            max_retries=MAX_RETRIES,
            sleep_seconds=round(sleep_s, 2),
        )
        time.sleep(sleep_s)

    # ==================================================================================
    # Private Helper Methods
    # ==================================================================================

    def _normalize_timeframe(self, timeframe: str) -> str:
        """Normalize timeframe format to match expected values.

        Handles case variations like "1day" -> "1Day", "1min" -> "1Min"

        Args:
            timeframe: Input timeframe string

        Returns:
            Normalized timeframe string

        Raises:
            ValueError: If timeframe is not supported

        """
        timeframe_lower = timeframe.lower()
        if timeframe_lower in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[timeframe_lower][0]  # Return normalized string

        # If no mapping found, raise error for invalid input
        valid_timeframes = ", ".join(TIMEFRAME_MAP.keys())
        raise ValueError(f"Unsupported timeframe: {timeframe}. Valid options: {valid_timeframes}")

    def _period_to_dates(self, period: str) -> tuple[str, str]:
        """Convert period string to start and end dates.

        Args:
            period: Period string like "1Y", "6M", "30D"

        Returns:
            Tuple of (start_date, end_date) as strings in YYYY-MM-DD format

        Raises:
            ValueError: If period format is invalid

        """
        end_date = datetime.now(UTC)
        days = DEFAULT_PERIOD_DAYS  # Default fallback

        # Parse period string with validation
        period_upper = period.upper().strip()
        if not period_upper:
            raise ValueError("Period string cannot be empty")

        try:
            if "Y" in period_upper:
                years = int(period_upper.replace("Y", ""))
                if years <= 0:
                    raise ValueError("Years must be positive")
                days = years * 365
            elif "M" in period_upper:
                months = int(period_upper.replace("M", ""))
                if months <= 0:
                    raise ValueError("Months must be positive")
                days = months * 30
            elif "D" in period_upper:
                days = int(period_upper.replace("D", ""))
                if days <= 0:
                    raise ValueError("Days must be positive")
            else:
                raise ValueError(
                    f"Invalid period format: {period}. Expected format: <number><Y|M|D> (e.g., '1Y', '6M', '30D')"
                )
        except (ValueError, AttributeError) as e:
            if "positive" in str(e) or "format" in str(e):
                raise
            raise ValueError(
                f"Invalid period format: {period}. Expected format: <number><Y|M|D> (e.g., '1Y', '6M', '30D')"
            ) from e

        start_date = end_date - timedelta(days=days)

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def _resolve_timeframe_core(self, timeframe: str) -> TimeFrame:
        """Resolve timeframe string to Alpaca TimeFrame object.

        Args:
            timeframe: Timeframe string (case-insensitive)

        Returns:
            Alpaca TimeFrame object

        Raises:
            ValueError: If timeframe is not supported

        """
        timeframe_lower = timeframe.lower()
        if timeframe_lower in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[timeframe_lower][1]  # Return TimeFrame object

        valid_timeframes = ", ".join(TIMEFRAME_MAP.keys())
        raise ValueError(f"Unsupported timeframe: {timeframe}. Valid options: {valid_timeframes}")

    def _extract_bars_from_response_core(self, response: object, symbol: str) -> BarsIterable | None:
        """Extract bars object from various possible response shapes.

        Args:
            response: API response object
            symbol: Stock symbol to extract bars for

        Returns:
            Bars iterable object or None if not found

        """
        from typing import cast

        bars_obj: BarsIterable | None = None
        try:
            # Preferred: BarsBySymbol has a `.data` dict
            data_attr = getattr(response, "data", None)
            if isinstance(data_attr, dict) and symbol in data_attr:
                bars_obj = cast("BarsIterable", data_attr[symbol])
            # Some SDKs expose attributes per symbol
            elif hasattr(response, symbol):
                bars_obj = cast("BarsIterable", getattr(response, symbol))
            # Fallback: mapping-like access
            elif isinstance(response, dict) and symbol in response:
                bars_obj = cast("BarsIterable", response[symbol])
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
        self.logger.debug(
            "Successfully retrieved bars",
            symbol=symbol,
            bar_count=len(bars),
        )

        result: list[dict[str, Any]] = []
        for bar in bars:
            try:
                bar_dict = bar.model_dump()
                result.append(bar_dict)
            except Exception as e:  # pragma: no cover - conversion resilience
                self.logger.warning(
                    "Failed to convert bar",
                    symbol=symbol,
                    error=str(e),
                )
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
        if days_requested > MIN_DAYS_FOR_DATA_CHECK and timeframe.lower() == "1day":
            return True

        self.logger.warning(
            "No historical data found",
            symbol=symbol,
            days_requested=days_requested,
            timeframe=timeframe,
        )
        return False

    def _convert_to_bar_model(self, bar_data: Any, symbol: str) -> BarModel:  # noqa: ANN401
        """Convert raw bar data to BarModel.

        Args:
            bar_data: Raw bar data from repository (dictionary from Pydantic model_dump())
            symbol: Symbol string

        Returns:
            BarModel instance

        Raises:
            ValueError: If bar_data is not a dictionary

        """
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
                open=Decimal(str(open_price)),
                high=Decimal(str(high_price)),
                low=Decimal(str(low_price)),
                close=Decimal(str(close_price)),
                volume=int(volume),
            )

        # This should not happen with clean Pydantic model_dump() data
        raise ValueError(f"Expected dictionary from Pydantic model_dump(), got {type(bar_data)}")
