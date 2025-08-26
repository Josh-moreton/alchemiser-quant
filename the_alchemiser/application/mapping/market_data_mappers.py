"""Mapping utilities between infra/DTOs and domain market data models."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel


def _parse_ts(value: object) -> datetime | None:
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


def bars_to_domain(rows: Iterable[dict[str, Any]]) -> list[BarModel]:
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
                    ts=ts_parsed,
                    open=Decimal(str(r.get("o") or r.get("open") or 0)),
                    high=Decimal(str(r.get("h") or r.get("high") or 0)),
                    low=Decimal(str(r.get("l") or r.get("low") or 0)),
                    close=Decimal(str(r.get("c") or r.get("close") or 0)),
                    volume=Decimal(str(r.get("v") or r.get("volume") or 0)),
                )
            )
        except Exception:
            # Best-effort mapping; skip bad rows
            continue
    return out


def quote_to_domain(raw: object) -> QuoteModel | None:
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
