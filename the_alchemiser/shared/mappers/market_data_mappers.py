"""Business Unit: shared | Status: current.

Market Data Mappers.

This module provides transformation functions to convert raw market data from external
sources (e.g., Alpaca API) into domain models with proper Decimal precision for financial
calculations.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.errors.exceptions import ValidationError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel

logger = get_logger(__name__)

# Unix timestamp heuristic: values above this threshold are treated as milliseconds
# This threshold (10^11 seconds) represents approximately year 5138
_UNIX_TIMESTAMP_MS_THRESHOLD = 10**11


def _parse_ts(value: datetime | str | int | float | None) -> datetime | None:
    """Parse various timestamp formats to timezone-aware datetime.

    Accepts multiple timestamp formats and normalizes them to UTC-aware datetime objects.

    Args:
        value: Timestamp in various formats:
            - datetime: returned as-is if already a datetime object
            - str: ISO8601 format (e.g., "2024-01-01T10:00:00Z" or "2024-01-01T10:00:00+00:00")
            - int/float: Unix timestamp in seconds or milliseconds (values > 10^11 treated as ms)

    Returns:
        Timezone-aware datetime in UTC, or None if parsing fails

    Raises:
        Does not raise exceptions - returns None on parse failure for robustness

    Examples:
        >>> _parse_ts(datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC))
        datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        >>> _parse_ts("2024-01-01T10:00:00Z")
        datetime.datetime(2024, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        >>> _parse_ts(1609502400)  # Unix seconds
        datetime.datetime(2021, 1, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)

        >>> _parse_ts("invalid")
        None

    Note:
        Uses a heuristic to distinguish Unix seconds from milliseconds: values greater
        than 10^11 are treated as milliseconds. This works correctly until year 5138.

    """
    try:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            v = value.strip()
            # Handle trailing 'Z' (Zulu/UTC) by mapping to +00:00
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            return datetime.fromisoformat(v)
        if isinstance(value, int | float):
            # Heuristic: treat very large values as milliseconds
            ts_sec = float(value) / (1000.0 if value > _UNIX_TIMESTAMP_MS_THRESHOLD else 1.0)
            return datetime.fromtimestamp(ts_sec, tz=UTC)
    except (ValueError, OSError, OverflowError) as exc:
        logger.debug("Failed to parse timestamp: %s (value: %s)", exc, value)
        return None
    except Exception as exc:
        # Catch unexpected errors but log them for investigation
        logger.warning("Unexpected error parsing timestamp: %s (value: %s)", exc, value)
    return None


def _validate_bar_prices(
    open_price: Decimal, high: Decimal, low: Decimal, close: Decimal, symbol: str
) -> None:
    """Validate OHLC price relationships and sanity checks.

    Args:
        open_price: Opening price for the bar
        high: Highest price during the bar
        low: Lowest price during the bar
        close: Closing price for the bar
        symbol: Symbol for error reporting

    Raises:
        ValidationError: If OHLC relationships are invalid or prices are negative

    """
    # Check for negative prices
    if open_price < 0 or high < 0 or low < 0 or close < 0:
        raise ValidationError(
            f"Negative price detected for {symbol}: open={open_price}, high={high}, low={low}, close={close}",
            field_name="prices",
        )

    # Check OHLC relationships
    if high < low:
        raise ValidationError(
            f"Invalid OHLC: high ({high}) < low ({low}) for {symbol}",
            field_name="ohlc_relationship",
        )

    if open_price < low or open_price > high:
        raise ValidationError(
            f"Invalid OHLC: open ({open_price}) outside [low={low}, high={high}] for {symbol}",
            field_name="ohlc_relationship",
        )

    if close < low or close > high:
        raise ValidationError(
            f"Invalid OHLC: close ({close}) outside [low={low}, high={high}] for {symbol}",
            field_name="ohlc_relationship",
        )


def bars_to_domain(
    rows: Iterable[dict[str, Any]], symbol: str | None = None, correlation_id: str | None = None
) -> list[BarModel]:
    """Convert raw bar data dictionaries to domain BarModel objects.

    Transforms raw market data from external sources (e.g., Alpaca API) into validated
    domain models with Decimal precision for financial calculations. Supports multiple
    key formats (short: t/S/o/h/l/c/v and long: timestamp/symbol/open/high/low/close/volume).

    Args:
        rows: Iterable of dictionaries containing bar data with keys like
              't'/'timestamp'/'time', 'o'/'open', 'h'/'high', 'l'/'low',
              'c'/'close', 'v'/'volume', 'S'/'symbol'
        symbol: Optional default symbol to apply when not present in each row.
                If None and row lacks symbol, raises MarketDataError.
        correlation_id: Optional correlation ID for tracing data flow through the system

    Returns:
        List of validated BarModel objects with timezone-aware timestamps and Decimal prices

    Raises:
        MarketDataError: If row lacks required data (timestamp, symbol, prices)
        ValidationError: If OHLC relationships are invalid or prices are negative
        ValueError: If Decimal conversion fails for price data

    Examples:
        >>> rows = [{
        ...     "t": "2024-01-01T10:00:00Z",
        ...     "S": "AAPL",
        ...     "o": "150.00", "h": "155.00", "l": "149.00", "c": "154.00",
        ...     "v": 1000000
        ... }]
        >>> bars = bars_to_domain(rows)
        >>> len(bars)
        1
        >>> bars[0].symbol
        'AAPL'

    Note:
        - Skips rows with invalid timestamps and logs warnings
        - All prices must be present and non-negative
        - OHLC relationships are validated (high >= low, open/close within range)
        - Missing prices are treated as errors (not defaulted to zero)

    """
    out: list[BarModel] = []
    skipped_count = 0
    processed_count = 0

    for r in rows:
        processed_count += 1
        try:
            # Extract and parse timestamp
            raw_ts = r.get("t") or r.get("timestamp") or r.get("time")
            ts_parsed = _parse_ts(raw_ts)
            if ts_parsed is None:
                skipped_count += 1
                logger.warning(
                    "Skipping bar row with invalid timestamp",
                    extra={
                        "correlation_id": correlation_id,
                        "raw_timestamp": raw_ts,
                        "row_index": processed_count - 1,
                    },
                )
                continue

            # Extract symbol - required field
            bar_symbol = r.get("S") or r.get("symbol") or symbol
            if not bar_symbol:
                skipped_count += 1
                logger.warning(
                    "Skipping bar row with missing symbol",
                    extra={
                        "correlation_id": correlation_id,
                        "timestamp": ts_parsed.isoformat(),
                        "row_index": processed_count - 1,
                    },
                )
                continue

            # Extract and validate prices - all required
            open_raw = r.get("o") or r.get("open")
            high_raw = r.get("h") or r.get("high")
            low_raw = r.get("l") or r.get("low")
            close_raw = r.get("c") or r.get("close")

            if open_raw is None or high_raw is None or low_raw is None or close_raw is None:
                skipped_count += 1
                logger.warning(
                    "Skipping bar row with missing price data",
                    extra={
                        "correlation_id": correlation_id,
                        "symbol": bar_symbol,
                        "timestamp": ts_parsed.isoformat(),
                        "missing_fields": [
                            k
                            for k, v in {
                                "open": open_raw,
                                "high": high_raw,
                                "low": low_raw,
                                "close": close_raw,
                            }.items()
                            if v is None
                        ],
                    },
                )
                continue

            # Convert to Decimal
            open_price = Decimal(str(open_raw))
            high_price = Decimal(str(high_raw))
            low_price = Decimal(str(low_raw))
            close_price = Decimal(str(close_raw))

            # Validate OHLC relationships
            _validate_bar_prices(open_price, high_price, low_price, close_price, bar_symbol)

            # Extract volume (can be zero)
            volume = int(r.get("v") or r.get("volume") or 0)

            out.append(
                BarModel(
                    symbol=bar_symbol,
                    timestamp=ts_parsed,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )

        except (ValidationError, ValueError) as exc:
            # Expected errors - validation failures or conversion errors
            skipped_count += 1
            logger.warning(
                "Failed to convert bar row to domain model",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                    "row_index": processed_count - 1,
                },
            )
            continue
        except Exception as exc:
            # Unexpected errors - log at error level for investigation
            skipped_count += 1
            logger.error(
                "Unexpected error converting bar row to domain model",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                    "row_index": processed_count - 1,
                },
                exc_info=True,
            )
            continue

    # Log summary statistics
    if skipped_count > 0:
        logger.info(
            "Bar conversion completed with skipped rows",
            extra={
                "correlation_id": correlation_id,
                "processed_count": processed_count,
                "successful_count": len(out),
                "skipped_count": skipped_count,
                "success_rate": f"{(len(out) / processed_count * 100):.1f}%"
                if processed_count > 0
                else "0%",
            },
        )

    return out


def quote_to_domain(raw: object, correlation_id: str | None = None) -> QuoteModel | None:
    """Convert raw quote data object to domain QuoteModel.

    Transforms raw quote objects from external sources (e.g., Alpaca SDK) into validated
    domain models with Decimal precision for financial calculations.

    Args:
        raw: Raw quote object with attributes like timestamp, bid_price, ask_price,
             bid_size, ask_size, symbol
        correlation_id: Optional correlation ID for tracing data flow through the system

    Returns:
        QuoteModel with parsed data and Decimal prices, or None if conversion fails
        or required data is missing

    Raises:
        Does not raise exceptions - returns None on conversion failure for robustness

    Examples:
        >>> class MockQuote:
        ...     timestamp = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        ...     symbol = "AAPL"
        ...     bid_price = 150.25
        ...     ask_price = 150.30
        ...     bid_size = 100
        ...     ask_size = 200
        >>> quote = quote_to_domain(MockQuote())
        >>> quote.symbol
        'AAPL'
        >>> quote.bid_price
        Decimal('150.25')

    Note:
        - Uses defensive attribute access with getattr() for robust parsing
        - Returns None if bid_price or ask_price are missing (required fields)
        - Returns None if timestamp is missing or invalid (no fallback to current time)
        - Defaults bid_size and ask_size to 0 if not present
        - Ensures all timestamps are timezone-aware (UTC)

    """
    try:
        if raw is None:
            return None

        # Parse timestamp - required field, no fallback to current time
        ts_any = getattr(raw, "timestamp", None)
        if ts_any is None:
            logger.warning(
                "Quote missing timestamp - skipping",
                extra={
                    "correlation_id": correlation_id,
                    "symbol": getattr(raw, "symbol", "UNKNOWN"),
                },
            )
            return None

        ts_parsed = _parse_ts(ts_any)
        if ts_parsed is None:
            logger.warning(
                "Quote has invalid timestamp - skipping",
                extra={
                    "correlation_id": correlation_id,
                    "symbol": getattr(raw, "symbol", "UNKNOWN"),
                    "raw_timestamp": ts_any,
                },
            )
            return None

        # Ensure timezone-aware
        ts = ts_parsed
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        # Extract prices - required fields
        bid_price = getattr(raw, "bid_price", None)
        ask_price = getattr(raw, "ask_price", None)
        if bid_price is None or ask_price is None:
            logger.debug(
                "Quote missing required price data - skipping",
                extra={
                    "correlation_id": correlation_id,
                    "symbol": getattr(raw, "symbol", "UNKNOWN"),
                    "has_bid": bid_price is not None,
                    "has_ask": ask_price is not None,
                },
            )
            return None

        # Extract sizes (default to 0 if not available)
        bid_size = getattr(raw, "bid_size", 0)
        ask_size = getattr(raw, "ask_size", 0)

        # Extract symbol
        symbol = getattr(raw, "symbol", "UNKNOWN")

        return QuoteModel(
            symbol=str(symbol),
            bid_price=Decimal(str(bid_price)),
            ask_price=Decimal(str(ask_price)),
            bid_size=Decimal(str(bid_size)),
            ask_size=Decimal(str(ask_size)),
            timestamp=ts,
        )

    except (ValueError, TypeError) as exc:
        # Expected errors - conversion failures
        logger.warning(
            "Failed to convert quote to domain model",
            extra={
                "correlation_id": correlation_id,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                "symbol": getattr(raw, "symbol", "UNKNOWN") if raw else "UNKNOWN",
            },
        )
        return None
    except Exception as exc:
        # Unexpected errors - log at error level
        logger.error(
            "Unexpected error converting quote to domain model",
            extra={
                "correlation_id": correlation_id,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                "symbol": getattr(raw, "symbol", "UNKNOWN") if raw else "UNKNOWN",
            },
            exc_info=True,
        )
        return None
