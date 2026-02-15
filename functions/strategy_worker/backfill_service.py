"""Business Unit: strategy | Status: current.

Group backfill evaluation service.

Provides core backfill logic for a single group: parsing strategy files,
evaluating DSL AST bodies for historical dates, computing weighted portfolio
daily returns, and writing results to S3 Parquet via GroupHistoryStore.

This module is intentionally side-effect-free with respect to where it is called.
The Lambda handler (lambda_handler.py) wires the service to its invocation context.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pandas as pd

from the_alchemiser.shared.data_v2.group_history_store import GroupHistoryStore
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from engines.dsl.engine import DslEngine

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INDICATOR_WARMUP_DAYS = 90


# ---------------------------------------------------------------------------
# In-memory market data adapter (zero I/O after pre-load)
# ---------------------------------------------------------------------------


class InMemoryAdapter(MarketDataPort):
    """Market data adapter serving from pre-loaded in-memory DataFrames.

    All data is loaded upfront into a dict of DataFrames.  Bar lookups
    are converted once per symbol and cached as BarModel lists.
    """

    def __init__(self, dataframes: dict[str, pd.DataFrame]) -> None:
        """Initialise with pre-loaded symbol DataFrames."""
        self._data = dataframes
        self._bar_cache: dict[str, list[BarModel]] = {}

    def get_bars(
        self,
        symbol: Symbol,
        period: str,
        timeframe: str,
    ) -> list[BarModel]:
        """Return all bars for a symbol from the in-memory cache."""
        sym = str(symbol)
        if sym in self._bar_cache:
            return self._bar_cache[sym]

        df = self._data.get(sym)
        if df is None or df.empty:
            self._bar_cache[sym] = []
            return []

        df = df.copy()
        if "timestamp" not in df.columns:
            self._bar_cache[sym] = []
            return []

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

        bars: list[BarModel] = []
        for row in df.itertuples(index=False):
            ts = row.timestamp
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            bars.append(
                BarModel(
                    symbol=sym,
                    timestamp=ts,
                    open=Decimal(str(row.open)),
                    high=Decimal(str(row.high)),
                    low=Decimal(str(row.low)),
                    close=Decimal(str(row.close)),
                    volume=int(row.volume),
                )
            )

        self._bar_cache[sym] = bars
        return bars

    def get_latest_bar(self, symbol: Symbol) -> BarModel | None:
        """Return the most recent bar."""
        bars = self.get_bars(symbol, "MAX", "1Day")
        return bars[-1] if bars else None

    def get_quote(self, symbol: Symbol) -> object:
        """Not used for backfill."""
        return None

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Not used for backfill."""
        return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Not used for backfill."""
        return None


# ---------------------------------------------------------------------------
# Market data pre-loading
# ---------------------------------------------------------------------------


def preload_symbols(symbols: set[str]) -> dict[str, pd.DataFrame]:
    """Download symbol data from S3 into memory.

    Args:
        symbols: Set of ticker strings to load.

    Returns:
        Dict mapping symbol -> DataFrame with OHLCV data.

    """
    store = MarketDataStore()
    data: dict[str, pd.DataFrame] = {}
    failed: list[str] = []

    for sym in sorted(symbols):
        try:
            df = store.read_symbol_data(sym, use_cache=True)
            if df is not None and not df.empty:
                data[sym] = df
            else:
                failed.append(sym)
        except Exception as exc:
            failed.append(sym)
            logger.warning(
                "Failed to load symbol",
                symbol=sym,
                error=str(exc),
                error_type=type(exc).__name__,
            )

    logger.info(
        "Pre-loaded symbols",
        loaded=len(data),
        total=len(symbols),
        failed=failed if failed else None,
    )
    return data


# ---------------------------------------------------------------------------
# Trading day helpers
# ---------------------------------------------------------------------------


def get_trading_days(end_date: date, num_calendar_days: int) -> list[date]:
    """Generate weekdays (oldest-first) in a calendar date range."""
    start = end_date - timedelta(days=num_calendar_days)
    days: list[date] = []
    current = start
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def get_trading_days_from_range(start_date: date, end_date: date) -> list[date]:
    """Generate weekdays (oldest-first) from a date range."""
    days: list[date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


# ---------------------------------------------------------------------------
# Single-group evaluation
# ---------------------------------------------------------------------------


def evaluate_group_signal(
    ast_body: list[ASTNode],
    eval_date: date,
    engine: DslEngine,
    correlation_id: str,
) -> dict[str, Decimal]:
    """Evaluate a group body at a point-in-time date and return portfolio weights.

    Sets the engine's as_of_date, evaluates the AST body, and extracts
    the resulting symbol weights (the "signal").

    Args:
        ast_body: AST expressions forming the group body.
        eval_date: The date to evaluate at.
        engine: DSL engine instance.
        correlation_id: Correlation ID for tracing.

    Returns:
        Dictionary of {symbol: weight} for the group's signal on eval_date.

    """
    from engines.dsl.operators.portfolio import collect_weights_from_value

    from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment
    from the_alchemiser.shared.schemas.trace import Trace

    engine.indicator_service.as_of_date = eval_date

    trace = Trace(
        trace_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        strategy_id="backfill",
        started_at=datetime.now(UTC),
    )

    last_result = None
    for expr in ast_body:
        last_result = engine.evaluator._evaluate_node(expr, correlation_id, trace)

    if isinstance(last_result, list) and len(last_result) == 1:
        last_result = last_result[0]

    if isinstance(last_result, PortfolioFragment):
        return dict(last_result.weights)
    if isinstance(last_result, dict):
        return {k: Decimal(str(v)) for k, v in last_result.items()}
    if isinstance(last_result, str):
        return {last_result: Decimal("1")}
    return collect_weights_from_value(last_result) if last_result else {}


def calculate_position_return(
    weights: dict[str, Decimal],
    return_date: date,
    market_data_service: MarketDataPort,
) -> Decimal | None:
    """Calculate the weighted daily return of a held position on a given date.

    Args:
        weights: Symbol-to-weight mapping representing the held position.
        return_date: The date to compute the return for.
        market_data_service: Market data port for bar retrieval.

    Returns:
        Weighted daily return as Decimal, or None if insufficient data.

    """
    weighted_return = Decimal("0")
    total_weight = Decimal("0")
    return_date_str = return_date.isoformat()

    for symbol_str, weight in weights.items():
        if weight <= Decimal("0"):
            continue
        try:
            today = datetime.now(UTC).date()
            days_back = max((today - return_date).days + 5, 30)
            period = f"{days_back}D"
            bars = market_data_service.get_bars(
                symbol=Symbol(symbol_str),
                period=period,
                timeframe="1Day",
            )
            if len(bars) < 2:
                continue

            date_to_idx: dict[str, int] = {}
            for i, bar in enumerate(bars):
                date_to_idx[bar.timestamp.date().isoformat()] = i

            target_idx = date_to_idx.get(return_date_str)
            if target_idx is None:
                for i in range(len(bars) - 1, -1, -1):
                    if bars[i].timestamp.date().isoformat() <= return_date_str:
                        target_idx = i
                        break

            if target_idx is None or target_idx < 1:
                continue

            prev_close = bars[target_idx - 1].close
            curr_close = bars[target_idx].close
            if prev_close and prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                weighted_return += weight * ret
                total_weight += weight
        except (KeyError, IndexError, ValueError, ZeroDivisionError):
            pass
        except Exception as exc:
            logger.warning(
                "Unexpected error computing return",
                symbol=symbol_str,
                return_date=return_date.isoformat(),
                error=str(exc),
                error_type=type(exc).__name__,
            )

    if total_weight <= Decimal("0"):
        return None
    return weighted_return / total_weight


# ---------------------------------------------------------------------------
# Full single-group backfill
# ---------------------------------------------------------------------------


def backfill_single_group(
    group_name: str,
    group_id: str,
    ast_body: list[ASTNode],
    trading_days: list[date],
    engine: DslEngine,
    market_data_service: MarketDataPort,
    correlation_id: str,
) -> dict[str, Any]:
    """Run the position-tracking backfill loop for one group.

    Evaluates the group AST body for each trading day, computes weighted
    portfolio daily returns, and collects records for S3 persistence.

    Args:
        group_name: Human-readable group name.
        group_id: Deterministic cache key.
        ast_body: AST body expressions.
        trading_days: Ordered list of dates to evaluate.
        engine: DslEngine instance.
        market_data_service: Market data port for bar retrieval.
        correlation_id: Tracing identifier.

    Returns:
        Dict with keys: group_name, group_id, records, days_evaluated,
        days_written, days_skipped, days_failed.

    """
    records: list[dict[str, Any]] = []
    skipped = 0
    failed = 0
    prev_weights: dict[str, Decimal] | None = None

    for eval_date in trading_days:
        try:
            today_weights = evaluate_group_signal(
                ast_body,
                eval_date,
                engine,
                correlation_id,
            )

            if prev_weights is None:
                if not today_weights:
                    skipped += 1
                    continue
                prev_weights = today_weights
                continue

            daily_ret = calculate_position_return(
                prev_weights,
                eval_date,
                market_data_service,
            )

            if daily_ret is None:
                skipped += 1
                if today_weights:
                    prev_weights = today_weights
                continue

            held_selections_str = {sym: str(w) for sym, w in prev_weights.items()}
            records.append(
                {
                    "record_date": eval_date.isoformat(),
                    "portfolio_daily_return": str(daily_ret),
                    "selections": json.dumps(held_selections_str),
                }
            )

            if today_weights:
                prev_weights = today_weights

        except Exception as exc:
            logger.warning(
                "Failed to evaluate date for group",
                group_name=group_name,
                eval_date=eval_date.isoformat(),
                error=str(exc),
                error_type=type(exc).__name__,
            )
            failed += 1

    return {
        "group_name": group_name,
        "group_id": group_id,
        "records": records,
        "days_evaluated": len(trading_days),
        "days_written": len(records),
        "days_skipped": skipped,
        "days_failed": failed,
    }


def write_results_to_s3(
    group_id: str,
    records: list[dict[str, Any]],
) -> bool:
    """Write backfill records to S3 Parquet via GroupHistoryStore.

    Args:
        group_id: Group identifier.
        records: List of dicts with record_date, portfolio_daily_return, selections.

    Returns:
        True if successful, False otherwise.

    """
    if not records:
        logger.info("No records to write", group_id=group_id)
        return True

    try:
        store = GroupHistoryStore()
        df = pd.DataFrame(records)
        df = df.sort_values("record_date")
        return store.append_records(group_id, df)
    except Exception as exc:
        logger.error(
            "Failed to write results to S3",
            group_id=group_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        return False
