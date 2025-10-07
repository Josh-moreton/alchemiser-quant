"""Business Unit: shared | Status: current.

Market Data Mappers.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.quote import QuoteModel

logger = get_logger(__name__)


def _parse_ts(value: datetime | str | int | float | None) -> datetime | None:
    """Best-effort parser to datetime.

    Accepts:
    - datetime: returned as-is
    - str (ISO8601, optionally with trailing 'Z'): parsed
    - int/float: treated as unix seconds (<= 10^11) or ms when larger
    Returns None when parsing fails.
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
            ts_sec = float(value) / (1000.0 if value > 10**11 else 1.0)
            return datetime.fromtimestamp(ts_sec, tz=UTC)
    except Exception:
        return None
    return None


def bars_to_domain(
    rows: Iterable[dict[str, Any]], symbol: str | None = None
) -> list[BarModel]:
    """Convert raw bar data dictionaries to domain BarModel objects.

    Args:
        rows: Iterable of dictionaries containing bar data with keys like
              't'/'timestamp'/'time', 'o'/'open', 'h'/'high', 'l'/'low',
              'c'/'close', 'v'/'volume'
        symbol: Optional default symbol to apply when not present in each row

    Returns:
        List of BarModel objects with valid timestamps and decimal prices

    Note:
        Skips rows with invalid timestamps or conversion errors using best-effort mapping

    """
    out: list[BarModel] = []
    for r in rows:
        try:
            raw_ts = r.get("t") or r.get("timestamp") or r.get("time")
            ts_parsed = _parse_ts(raw_ts)
            if ts_parsed is None:
                # Skip rows without a valid timestamp
                continue
            out.append(
                BarModel(
                    symbol=(r.get("S") or r.get("symbol") or symbol or "UNKNOWN"),
                    timestamp=ts_parsed,
                    open=Decimal(str(r.get("o") or r.get("open") or 0)),
                    high=Decimal(str(r.get("h") or r.get("high") or 0)),
                    low=Decimal(str(r.get("l") or r.get("low") or 0)),
                    close=Decimal(str(r.get("c") or r.get("close") or 0)),
                    volume=int(r.get("v") or r.get("volume") or 0),
                )
            )
        except Exception as exc:
            logger.debug("Failed to map bar row to domain: %s", exc)
            continue
    return out


def quote_to_domain(raw: object) -> QuoteModel | None:
    """Convert raw quote data object to domain QuoteModel.

    Args:
        raw: Raw quote object with attributes like timestamp, bid_price, ask_price

    Returns:
        QuoteModel with parsed data, or None if conversion fails or data is invalid

    Note:
        Uses defensive attribute access with getattr() for robust parsing

        Note: This currently creates the legacy QuoteModel without market depth.
        Migrating to the enhanced QuoteModel from shared.types.market_data would
        surface bid_size/ask_size details for richer liquidity analysis.

    """
    try:
        if raw is None:
            return None
        ts_any = getattr(raw, "timestamp", None)
        ts: datetime | None
        if ts_any is None:
            ts = None
        else:
            parsed = _parse_ts(ts_any)
            ts = parsed if parsed is not None else None
        bid = getattr(raw, "bid_price", None)
        ask = getattr(raw, "ask_price", None)
        if bid is None or ask is None:
            return None
        return QuoteModel(ts=ts, bid=Decimal(str(bid)), ask=Decimal(str(ask)))
    except Exception:
        return None
