"""Business Unit: strategy | Status: current.

Group scoring and on-demand backfill infrastructure for DSL filter evaluation.

This module owns the question "how do we score a named group (portfolio) for
a filter operator?"  It provides:

- **Cache-based scoring** -- query DynamoDB for pre-computed historical returns
  and compute the requested metric (moving-average-return, stdev-return, etc.)
- **In-process scoring** -- re-evaluate the group's AST body for historical
  dates when DynamoDB cache is unavailable (local debug runs)
- **On-demand backfill** -- when the cache has insufficient data, transparently
  re-evaluate the group for each missing trading day, compute daily portfolio
  returns, and write them to DynamoDB
- **Portfolio metric computation** -- pure functions that mirror
  ``TechnicalIndicators`` but operate on a pre-built return series

Module-level mutable state
--------------------------
Four module-level stores provide cross-call memoization within a single
strategy evaluation run:

- ``_BACKFILL_IN_PROGRESS`` -- recursion guard (set of group_ids)
- ``_AST_BODY_STORE`` -- group AST bodies keyed by fragment_id (ephemeral)
- ``_AST_BODY_BY_GROUP_ID`` -- group AST bodies keyed by stable group_id
- ``_IN_PROCESS_RETURN_MEMO`` -- (group_id, date) -> daily return memoization

**Invariant:** These are cleared at the start of each ``evaluate()`` call via
``clear_evaluation_caches()``.  Any code path that bypasses ``evaluate()``
(e.g. direct operator testing, warm Lambda reuse with manual invocation) will
inherit stale state from a previous run.  The ``_BACKFILL_IN_PROGRESS`` set is
the recursion guard and must always be empty before a new evaluation begins.
"""

from __future__ import annotations

import hashlib
import math
import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from engines.dsl.context import DslContext
from engines.dsl.operators.group_cache_lookup import (
    is_cache_available,
    lookup_historical_returns,
    write_historical_return,
)
from engines.dsl.types import DslEvaluationError, DSLValue

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Pattern matching valid trading symbols (1-5 uppercase letters/digits,
# plus optional share-class suffix like /B or .B for BRK/B, BF.B etc.).
# Anything that does NOT match is treated as a named portfolio/strategy
# group requiring proper historical composite scoring.
_TICKER_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9]{0,4}([/.][A-Z])?$")

# Maximum number of calendar days to backfill in a single on-demand run.
# Keeps Lambda execution time bounded (each day requires re-evaluation
# of the full group AST + bar fetches for every holding).
_MAX_BACKFILL_CALENDAR_DAYS = 45

# Minimum number of return data points required for metric computation.
# If fewer returns are available, fail closed (return None).
_MIN_RETURNS_FOR_METRIC = 3

# DSL operator names -> canonical metric identifiers used for dispatch.
_METRIC_DISPATCH: dict[str, str] = {
    "moving-average-return": "moving_average_return",
    "cumulative-return": "cumulative_return",
    "stdev-return": "stdev_return",
    "max-drawdown": "max_drawdown",
    "rsi": "rsi",
}

# Annualisation factor for stdev (matches TechnicalIndicators.stdev_return).
_ANNUALISATION_SQRT_252 = Decimal("15.8745078664")  # sqrt(252) to 10dp


# ---------------------------------------------------------------------------
# Module-level mutable state (see module docstring for invariants)
# ---------------------------------------------------------------------------

# Set of group_ids currently being backfilled in this invocation.
# Guards against infinite recursion: if _score_portfolio triggers backfill,
# and backfill re-evaluates the group body, the inner evaluation must NOT
# attempt another backfill for the same group.
_BACKFILL_IN_PROGRESS: set[str] = set()

# Transient store for group AST bodies, keyed by PortfolioFragment.fragment_id.
# Populated by the ``group()`` operator and consumed by ``_fetch_or_backfill_returns``
# during on-demand backfill.  Kept out of PortfolioFragment.metadata to avoid
# leaking non-serialisable ASTNode objects into EventBridge payloads.
_AST_BODY_STORE: dict[str, list[ASTNode]] = {}

# AST body store keyed by stable group_id (not ephemeral fragment_id).
# Populated by ``group()`` alongside ``_AST_BODY_STORE``.  Ensures that
# re-evaluations during in-process scoring can locate AST bodies even
# when ``weight_equal`` / ``filter`` generate new fragment_ids (uuid4).
_AST_BODY_BY_GROUP_ID: dict[str, list[ASTNode]] = {}

# Memoization cache for in-process group signal evaluations.
# Key: (group_id, date_iso_str) -> dict of weights (signal) or None.
# Signal evaluation is deterministic (same group + same date = same
# signal), so this is safe to cache across calls.  Prevents exponential
# recursion in deeply nested strategies where inner groups would otherwise
# trigger their own full backfill loops for every outer evaluation date.
# Cleared between strategy runs via ``clear_evaluation_caches()``.
_IN_PROCESS_SIGNAL_MEMO: dict[tuple[str, str], dict[str, Decimal] | None] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clear_evaluation_caches() -> None:
    """Clear all module-level caches between strategy evaluation runs.

    Must be called at the start of each strategy evaluation to prevent
    stale memoization data from a previous run leaking into the current
    one.  Safe to call multiple times.
    """
    _AST_BODY_STORE.clear()
    _AST_BODY_BY_GROUP_ID.clear()
    _IN_PROCESS_SIGNAL_MEMO.clear()
    _BACKFILL_IN_PROGRESS.clear()


def register_ast_body(fragment_id: str, group_name: str, body: list[ASTNode]) -> None:
    """Register a group's AST body for later backfill/in-process scoring.

    Called by the ``group()`` operator after evaluating the group body.
    Stores the body in both the ephemeral (fragment_id) and stable
    (group_id) stores so that subsequent scoring can locate it regardless
    of whether ``weight_equal`` / ``filter`` generate new fragment_ids.

    Args:
        fragment_id: Ephemeral PortfolioFragment.fragment_id.
        group_name: Human-readable group name from the DSL.
        body: Raw AST body expressions from the group operator.

    """
    _AST_BODY_STORE[fragment_id] = list(body)
    _AST_BODY_BY_GROUP_ID[derive_group_id(group_name)] = list(body)


def derive_group_id(group_name: str) -> str:
    """Derive a deterministic cache-compatible group_id from a DSL group name.

    Uses a sanitised slug of the group name combined with a short SHA-256
    hash prefix for uniqueness. The slug provides human readability while
    the hash prevents collisions between similarly-named groups.

    Examples:
        "MAX DD: TQQQ vs UVXY" -> "max_dd_tqqq_vs_uvxy_a1b2c3d4"
        "WAM Updated Package: Muted WAMCore" -> "wam_updated_package_muted_wamcore_e5f6a7b8"

    Args:
        group_name: The raw group name from the DSL (group ...) expression.

    Returns:
        A deterministic, DynamoDB-safe group_id string.

    """
    # Create slug: lowercase, collapse non-alphanum to underscores, trim edges
    slug = re.sub(r"[^a-z0-9]+", "_", group_name.lower()).strip("_")
    # Truncate slug to keep DynamoDB key reasonable
    slug = slug[:60]
    # Hash for uniqueness
    hash_prefix = hashlib.sha256(group_name.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{hash_prefix}"


def is_bare_asset_fragment(fragment: PortfolioFragment, group_name: object) -> bool:
    """Return True if the fragment is a bare symbol, not a named portfolio.

    A fragment is a bare asset when ALL of the following hold:

    1. ``source_step`` is ``"asset"`` (set by ``_normalize_portfolio_items``
       when wrapping a raw ``(asset "TQQQ")`` string).
    2. ``group_name`` matches a trading symbol pattern (1-5 uppercase
       letters/digits, with optional share-class suffix like ``/B`` or
       ``.B`` for BRK/B, BF.B).

    Real strategy/portfolio groups (NOVA, WYLD, etc.) have
    ``source_step="group"`` even though their names may look like tickers,
    so the ``source_step`` check prevents false positives.

    Args:
        fragment: The portfolio fragment to check.
        group_name: The group_name metadata value (may be ``None``).

    Returns:
        True only for bare-asset fragments created by normalization.

    """
    if fragment.source_step != "asset":
        return False
    if not isinstance(group_name, str) or not group_name:
        return False
    return bool(_TICKER_SYMBOL_RE.match(group_name))


# ---------------------------------------------------------------------------
# Scoring pipeline
# ---------------------------------------------------------------------------


def try_cache_scoring(
    fragment: PortfolioFragment,
    condition_expr: ASTNode,
    context: DslContext,
    *,
    group_name: object,
    op_name: str | None,
    should_invert: bool,
) -> float | None:
    """Attempt to score a portfolio fragment using the DynamoDB cache.

    Returns the computed score if the cache path succeeds, or ``None``
    if the caller should fall through to per-symbol fallback scoring.

    ``None`` is returned when:
    - The fragment has no group name (not a named group).
    - The DynamoDB cache table is unavailable.
    - The window or metric cannot be extracted from the condition.
    - Insufficient cached returns exist even after on-demand backfill
      (the caller then falls back to today-only per-symbol scoring).
    - The metric computation itself yields no result.
    """
    if not isinstance(group_name, str) or not group_name:
        return None

    group_id = derive_group_id(group_name)

    if not is_cache_available():
        logger.error(
            "DSL filter: DynamoDB group cache is NOT available "
            "-- infrastructure may be misconfigured. Falling back to "
            "today-only snapshot scoring (NOT Composer-parity).",
            extra={
                "group_name": group_name,
                "group_id": group_id,
                "correlation_id": context.correlation_id,
            },
        )
        return None

    window = _extract_window_from_condition(condition_expr, context)
    canonical_metric = _METRIC_DISPATCH.get(op_name or "") if op_name else None

    if not window or not canonical_metric:
        logger.warning(
            "DSL filter: could not extract window or metric from condition "
            "for cached group scoring -- falling back to today-only snapshot",
            extra={
                "group_name": group_name,
                "group_id": group_id,
                "op_name": op_name,
                "window": window,
                "canonical_metric": canonical_metric,
                "correlation_id": context.correlation_id,
            },
        )
        return None

    historical_returns = _fetch_or_backfill_returns(
        fragment,
        group_id,
        group_name,
        window,
        context,
    )

    if len(historical_returns) < window:
        # Insufficient data: fall back to per-symbol scoring in _score_portfolio.
        logger.warning(
            "DSL filter: insufficient cached returns for group scoring "
            "(falling back to per-symbol weighted average)",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "metric": canonical_metric,
                "window": window,
                "returns_available": len(historical_returns),
                "has_ast_body": bool(_AST_BODY_STORE.get(fragment.fragment_id)),
                "correlation_id": context.correlation_id,
            },
        )
        return None

    score = _compute_portfolio_metric(
        returns=historical_returns,
        metric_name=canonical_metric,
        window=window,
    )
    if score is None:
        logger.warning(
            "DSL filter: metric computation returned None",
            extra={
                "group_id": group_id,
                "metric": canonical_metric,
                "returns_count": len(historical_returns),
                "correlation_id": context.correlation_id,
            },
        )
        return None

    if should_invert:
        score = -score

    logger.info(
        "DSL filter: scored group from cached historical returns",
        extra={
            "group_name": group_name,
            "group_id": group_id,
            "metric": canonical_metric,
            "window": window,
            "returns_available": len(historical_returns),
            "score": score,
            "inverted": should_invert,
            "correlation_id": context.correlation_id,
        },
    )
    return score


def try_in_process_scoring(
    fragment: PortfolioFragment,
    condition_expr: ASTNode,
    context: DslContext,
    *,
    group_name: str,
    op_name: str | None,
    should_invert: bool,
) -> float | None:
    """Score a portfolio by re-evaluating its AST body in-process (no DynamoDB).

    This fallback is used when:
    - The DynamoDB group cache is unavailable (local debug runs)
    - Cache scoring failed but the group has a stored AST body

    It re-evaluates the group for each historical trading day in the
    lookback window, computes daily portfolio returns, then applies
    the requested metric (moving-average-return, stdev-return, etc.).

    Returns the score if successful, or ``None`` to fall through to
    per-symbol fallback.
    """
    ast_body = _AST_BODY_STORE.get(fragment.fragment_id)
    if not ast_body:
        # Fragment ID may have changed (uuid4 in weight_equal).
        # Fall back to stable group_id-based lookup.
        ast_body = _AST_BODY_BY_GROUP_ID.get(derive_group_id(group_name))
    if not ast_body:
        logger.debug(
            "In-process scoring: no AST body found for group '%s' "
            "(fragment_id=%s) -- cannot re-evaluate historically",
            group_name,
            fragment.fragment_id,
        )
        return None
    if not context.market_data_service:
        logger.debug(
            "In-process scoring: no market_data_service on context for group '%s' -- skipping",
            group_name,
        )
        return None

    indicator_svc = context.indicator_service
    if not hasattr(indicator_svc, "as_of_date"):
        logger.debug(
            "In-process scoring: indicator_service lacks as_of_date for group '%s' -- skipping",
            group_name,
        )
        return None

    window = _extract_window_from_condition(condition_expr, context)
    canonical_metric = _METRIC_DISPATCH.get(op_name or "") if op_name else None
    if not window or not canonical_metric:
        logger.debug(
            "In-process scoring: could not extract window or metric "
            "for group '%s' (window=%s, metric=%s) -- skipping",
            group_name,
            window,
            canonical_metric,
        )
        return None

    group_id = derive_group_id(group_name)
    if group_id in _BACKFILL_IN_PROGRESS:
        logger.debug(
            "In-process scoring: recursion guard hit for group '%s' "
            "(group_id=%s) -- already being backfilled",
            group_name,
            group_id,
        )
        return None

    _BACKFILL_IN_PROGRESS.add(group_id)
    original_as_of_date = getattr(indicator_svc, "as_of_date", None)
    try:
        anchor_date = original_as_of_date or datetime.now(UTC).date()
        calendar_days = min(int(window * 2.5) + 10, _MAX_BACKFILL_CALENDAR_DAYS)
        trading_days = _get_trading_days(anchor_date, calendar_days)

        returns = _collect_in_process_returns(ast_body, trading_days, group_name, context)

        if len(returns) < window:
            logger.info(
                "In-process scoring: insufficient returns for %s (%d available, %d needed)",
                group_name,
                len(returns),
                window,
            )
            return None

        score = _compute_portfolio_metric(
            returns=returns,
            metric_name=canonical_metric,
            window=window,
        )
        if score is None:
            logger.debug(
                "In-process scoring: metric computation returned None "
                "for group '%s' (metric=%s, returns=%d)",
                group_name,
                canonical_metric,
                len(returns),
            )
            return None

        if should_invert:
            score = -score

        logger.info(
            "DSL filter: scored group via in-process historical evaluation",
            extra={
                "group_name": group_name,
                "metric": canonical_metric,
                "window": window,
                "returns_evaluated": len(returns),
                "score": score,
                "correlation_id": context.correlation_id,
            },
        )
        return score

    finally:
        if hasattr(indicator_svc, "as_of_date"):
            indicator_svc.as_of_date = original_as_of_date
        _BACKFILL_IN_PROGRESS.discard(group_id)


# ---------------------------------------------------------------------------
# Helpers: window extraction
# ---------------------------------------------------------------------------


def _extract_window_from_condition(
    condition_expr: ASTNode,
    context: DslContext,
) -> int | None:
    """Extract the window size from a filter condition expression.

    Parses expressions like (moving-average-return {:window 10}) or
    (stdev-return {:window 12}) to extract the window value.

    Returns None if window cannot be extracted.
    """
    if not condition_expr.is_list() or len(condition_expr.children) < 2:
        return None

    try:
        params_val = context.evaluate_node(
            condition_expr.children[1],
            context.correlation_id,
            context.trace,
        )
        if isinstance(params_val, dict):
            window = params_val.get("window")
            if isinstance(window, Decimal):
                return int(window)
            if isinstance(window, int):
                return window
            if isinstance(window, float):
                return int(window)
    except (DslEvaluationError, ValueError, TypeError):
        pass

    return None


# ---------------------------------------------------------------------------
# Helpers: trading days
# ---------------------------------------------------------------------------


def _get_trading_days(end_date: date, num_calendar_days: int) -> list[date]:
    """Generate a list of expected trading days (weekdays) in a date range.

    Excludes weekends. Does NOT exclude US market holidays because the
    market data API itself handles missing data gracefully (bars just
    won't exist for holidays, so the return computation skips them).

    Args:
        end_date: The most recent date (inclusive).
        num_calendar_days: How many calendar days back to look.

    Returns:
        List of date objects (oldest-first) that are weekdays.

    """
    start = end_date - timedelta(days=num_calendar_days)
    days: list[date] = []
    current = start
    while current <= end_date:
        if current.weekday() < 5:  # Monday=0 .. Friday=4
            days.append(current)
        current += timedelta(days=1)
    return days


# ---------------------------------------------------------------------------
# Helpers: daily return computation
# ---------------------------------------------------------------------------


def _compute_daily_return_for_portfolio(
    selections: dict[str, Decimal],
    record_date: date,
    context: DslContext,
) -> Decimal | None:
    """Compute weighted portfolio daily return for a single date.

    For each symbol in the portfolio, fetches bars from the market data
    service and computes close-to-close return.  The portfolio return is
    the weight-normalised sum of individual returns.

    Args:
        selections: Symbol-to-weight mapping (Decimal weights).
        record_date: The date for which to compute the return.
        context: DSL context (must have market_data_service set).

    Returns:
        Portfolio daily return as Decimal, or None if insufficient data.

    """
    if not context.market_data_service:
        return None

    from the_alchemiser.shared.value_objects.symbol import Symbol

    weighted_return = Decimal("0")
    total_weight = Decimal("0")
    record_date_str = record_date.isoformat()

    for symbol_str, weight in selections.items():
        if weight <= Decimal("0"):
            continue
        try:
            # Derive a period that covers from today back through record_date
            # plus a small buffer.  The fixed "30D" was insufficient for dates
            # older than 30 calendar days, which the backfill window can reach.
            today = datetime.now(UTC).date()
            days_back = max((today - record_date).days + 5, 30)
            period = f"{days_back}D"

            bars = context.market_data_service.get_bars(
                symbol=Symbol(symbol_str),
                period=period,
                timeframe="1Day",
            )
            if len(bars) < 2:
                continue

            # Find bar for record_date and its predecessor
            daily_return = _extract_bar_return(bars, record_date_str)
            if daily_return is not None:
                weighted_return += weight * daily_return
                total_weight += weight
        except Exception as exc:
            logger.warning(
                "Backfill: failed to get bars for %s on %s: %s",
                symbol_str,
                record_date_str,
                exc,
            )

    if total_weight <= Decimal("0"):
        return None
    return weighted_return / total_weight


def _extract_bar_return(bars: list[Any], record_date_str: str) -> Decimal | None:
    """Extract close-to-close daily return for a date from a bar series.

    Extracts close-to-close daily return from bar objects that have
    .timestamp and .close attributes.

    Args:
        bars: Chronologically ordered bars with .timestamp and .close.
        record_date_str: ISO date string (YYYY-MM-DD).

    Returns:
        Daily return as Decimal, or None.

    """
    # Build date-indexed map
    date_to_idx: dict[str, int] = {}
    for i, bar in enumerate(bars):
        bar_date = bar.timestamp.date().isoformat()
        date_to_idx[bar_date] = i

    target_idx = date_to_idx.get(record_date_str)
    if target_idx is None:
        # Fall back to most recent bar on or before the date
        for i in range(len(bars) - 1, -1, -1):
            if bars[i].timestamp.date().isoformat() <= record_date_str:
                target_idx = i
                break

    if target_idx is None or target_idx < 1:
        return None

    current_close = bars[target_idx].close
    prev_close = bars[target_idx - 1].close
    if prev_close == Decimal("0"):
        return None
    result: Decimal = (current_close / prev_close) - Decimal("1")
    return result


# ---------------------------------------------------------------------------
# On-demand backfill
# ---------------------------------------------------------------------------


def _backfill_group_cache(
    group_id: str,
    group_name: str,
    ast_body: list[ASTNode],
    window: int,
    context: DslContext,
) -> list[Decimal]:
    """On-demand backfill: re-evaluate a group for historical dates.

    When the cache has insufficient data for a group, this function:
    1. Determines which trading days need backfilling
    2. For each missing day, sets as_of_date on the indicator service,
       re-evaluates the group AST body, extracts the resulting weights,
       fetches bars to compute the portfolio's daily return
    3. Writes each result to DynamoDB

    The recursion guard ``_BACKFILL_IN_PROGRESS`` prevents infinite
    loops: if re-evaluating the group body triggers another filter that
    tries to score this same group, the inner call sees the guard and
    falls back to today-only scoring.

    Args:
        group_id: Cache key for DynamoDB.
        group_name: Human-readable group name (for logging).
        ast_body: The raw AST body expressions from the group operator.
        window: Lookback window (trading days) needed by the metric.
        context: DSL context (must have market_data_service and
            indicator_service with as_of_date support).

    Returns:
        List of historical daily returns (oldest-first) that were
        backfilled + any that were already in the cache, up to the
        requested window.

    """
    if group_id in _BACKFILL_IN_PROGRESS:
        logger.warning(
            "Backfill guard: %s (%s) already in progress -- recursive "
            "backfill detected, falling back to today-only scoring",
            group_id,
            group_name,
            extra={"group_id": group_id, "group_name": group_name},
        )
        return []

    if not context.market_data_service:
        logger.warning(
            "Backfill skipped: no market_data_service on context",
            extra={"group_id": group_id},
        )
        return []

    indicator_svc = context.indicator_service
    if not hasattr(indicator_svc, "as_of_date"):
        logger.warning(
            "Backfill skipped: indicator_service lacks as_of_date",
            extra={"group_id": group_id},
        )
        return []

    _BACKFILL_IN_PROGRESS.add(group_id)
    original_as_of_date = getattr(indicator_svc, "as_of_date", None)
    try:
        anchor_date = original_as_of_date or datetime.now(UTC).date()
        calendar_days = min(int(window * 2.5) + 10, _MAX_BACKFILL_CALENDAR_DAYS)
        trading_days = _get_trading_days(anchor_date, calendar_days)

        existing_returns = _check_existing_cache(group_id, calendar_days, anchor_date, window)
        if existing_returns is not None:
            return existing_returns

        backfilled_returns = _backfill_trading_days(
            group_id,
            group_name,
            ast_body,
            trading_days,
            context,
        )

        logger.info(
            "On-demand backfill completed",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "days_backfilled": len(backfilled_returns),
                "correlation_id": context.correlation_id,
            },
        )

        refreshed = lookup_historical_returns(
            group_id=group_id,
            lookback_days=calendar_days,
            end_date=anchor_date,
        )

        _validate_backfill(group_id, group_name, backfilled_returns, refreshed, context)
        return list(refreshed)

    finally:
        if hasattr(indicator_svc, "as_of_date"):
            indicator_svc.as_of_date = original_as_of_date
        _BACKFILL_IN_PROGRESS.discard(group_id)


def _check_existing_cache(
    group_id: str,
    calendar_days: int,
    anchor_date: date,
    window: int,
) -> list[Decimal] | None:
    """Check if the cache already has enough returns. Returns them or None."""
    existing_returns = lookup_historical_returns(
        group_id=group_id,
        lookback_days=calendar_days,
        end_date=anchor_date,
    )
    if len(existing_returns) >= window:
        logger.info(
            "Backfill not needed: cache already has %d returns (need %d)",
            len(existing_returns),
            window,
            extra={"group_id": group_id},
        )
        return list(existing_returns)
    return None


def _backfill_trading_days(
    group_id: str,
    group_name: str,
    ast_body: list[ASTNode],
    trading_days: list[date],
    context: DslContext,
) -> list[tuple[str, Decimal]]:
    """Evaluate a group for each trading day and write results to DynamoDB.

    Tracks position state across days: the return for day D is the
    performance of the position determined by the signal at close of
    day D-1 (the previous trading day).  On the first day, only the
    signal is recorded -- no return is produced.

    Returns list of (date_iso, daily_return) tuples for successfully
    persisted entries only.
    """
    backfilled_returns: list[tuple[str, Decimal]] = []

    logger.info(
        "Starting on-demand backfill",
        extra={
            "group_id": group_id,
            "group_name": group_name,
            "trading_days_to_evaluate": len(trading_days),
            "correlation_id": context.correlation_id,
        },
    )

    prev_weights: dict[str, Decimal] | None = None

    for eval_date in trading_days:
        try:
            # Step 1: Evaluate today's signal
            today_weights = _evaluate_group_signal_for_date(
                ast_body,
                eval_date,
                context,
            )

            if not today_weights and prev_weights is None:
                continue

            # Step 2: If we have a previous signal, compute its return today
            if prev_weights is None:
                # First actionable day -- record signal, no return yet
                prev_weights = today_weights
                continue

            daily_ret = _compute_daily_return_for_portfolio(
                selections=prev_weights,
                record_date=eval_date,
                context=context,
            )

            logger.debug(
                "Backfill: group resolved for date",
                extra={
                    "group_id": group_id,
                    "group_name": group_name,
                    "eval_date": eval_date.isoformat(),
                    "held_count": len(prev_weights),
                    "held_symbols": sorted(prev_weights.keys()),
                    "new_count": len(today_weights) if today_weights else 0,
                    "daily_return": str(daily_ret) if daily_ret is not None else "None",
                    "correlation_id": context.correlation_id,
                },
            )

            if daily_ret is not None:
                # Write the return of the held position
                held_selections_str = {sym: str(w) for sym, w in prev_weights.items()}
                write_ok = write_historical_return(
                    group_id=group_id,
                    record_date=eval_date.isoformat(),
                    selections=held_selections_str,
                    portfolio_daily_return=daily_ret,
                )
                if not write_ok:
                    logger.warning(
                        "Backfill: failed to persist cache entry to DynamoDB "
                        "-- data computed but NOT saved",
                        extra={
                            "group_id": group_id,
                            "group_name": group_name,
                            "eval_date": eval_date.isoformat(),
                            "daily_return": str(daily_ret),
                            "correlation_id": context.correlation_id,
                        },
                    )
                else:
                    backfilled_returns.append((eval_date.isoformat(), daily_ret))

            # Update signal for next iteration
            if today_weights:
                prev_weights = today_weights

        except Exception as exc:
            logger.warning(
                "Backfill: failed to evaluate date %s for group %s (%s): %s",
                eval_date.isoformat(),
                group_name,
                group_id,
                exc,
                exc_info=True,
            )

    return backfilled_returns


def _validate_backfill(
    group_id: str,
    group_name: str,
    backfilled_returns: list[tuple[str, Decimal]],
    refreshed: list[Decimal],
    context: DslContext,
) -> None:
    """Validate that backfilled returns were persisted to DynamoDB."""
    if backfilled_returns and len(refreshed) == 0:
        logger.error(
            "CRITICAL: on-demand backfill computed %d returns but "
            "DynamoDB re-query returned ZERO -- cache writes are "
            "silently failing. Check IAM permissions, table name, "
            "and GROUP_HISTORY_TABLE environment variable.",
            len(backfilled_returns),
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "days_computed": len(backfilled_returns),
                "days_persisted": 0,
                "correlation_id": context.correlation_id,
            },
        )
    elif backfilled_returns and len(refreshed) < len(backfilled_returns):
        logger.warning(
            "Post-backfill validation: only %d of %d computed returns persisted to DynamoDB cache",
            len(refreshed),
            len(backfilled_returns),
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "days_computed": len(backfilled_returns),
                "days_persisted": len(refreshed),
                "correlation_id": context.correlation_id,
            },
        )


# ---------------------------------------------------------------------------
# Helpers: in-process evaluation
# ---------------------------------------------------------------------------


def _evaluate_group_signal_for_date(
    ast_body: list[ASTNode],
    eval_date: date,
    context: DslContext,
) -> dict[str, Decimal]:
    """Evaluate a group AST body for a single historical date.

    Sets ``as_of_date`` on the indicator service, re-evaluates the
    body, and extracts the resulting portfolio weights (signal).

    Does NOT compute returns -- use ``_compute_daily_return_for_portfolio``
    separately to compute the return of a held position.

    The caller must save/restore ``as_of_date`` around this call.

    Returns:
        Dictionary of {symbol: weight} for the group's signal on eval_date.
        Empty dict if evaluation produces no weights.

    """
    from engines.dsl.operators.portfolio import collect_weights_from_value

    context.indicator_service.as_of_date = eval_date

    last_result: DSLValue = None
    for expr in ast_body:
        last_result = context.evaluate_node(
            expr,
            context.correlation_id,
            context.trace,
        )
    last_result = unwrap_single_element_list(last_result)

    if isinstance(last_result, PortfolioFragment):
        return dict(last_result.weights)
    return collect_weights_from_value(last_result) if last_result else {}


def _collect_in_process_returns(
    ast_body: list[ASTNode],
    trading_days: list[date],
    group_name: str,
    context: DslContext,
) -> list[Decimal]:
    """Collect daily returns by re-evaluating a group body for each trading day.

    Tracks position state across days: the return for day D is the
    performance of the position determined by the signal at close of
    day D-1.  Uses ``(group_id, date)`` memoization for signal evaluations
    to ensure each group-date pair is evaluated at most once across the
    entire strategy run.  This prevents exponential recursion in deeply
    nested group hierarchies (e.g. FTL Starburst with 5+ nesting levels)
    where inner groups would otherwise trigger their own full backfill
    loops for every outer evaluation date.
    """
    group_id = derive_group_id(group_name)
    returns: list[Decimal] = []
    prev_weights: dict[str, Decimal] | None = None

    for eval_date in trading_days:
        memo_key = (group_id, eval_date.isoformat())
        try:
            # Evaluate today's signal (memoized)
            if memo_key in _IN_PROCESS_SIGNAL_MEMO:
                today_weights = _IN_PROCESS_SIGNAL_MEMO[memo_key] or {}
            else:
                today_weights = _evaluate_group_signal_for_date(
                    ast_body,
                    eval_date,
                    context,
                )
                _IN_PROCESS_SIGNAL_MEMO[memo_key] = today_weights if today_weights else None

            if prev_weights is None:
                # First actionable day -- no return yet
                if today_weights:
                    prev_weights = today_weights
                continue

            # Calculate return of previous position during today
            daily_ret = _compute_daily_return_for_portfolio(
                selections=prev_weights,
                record_date=eval_date,
                context=context,
            )
            if daily_ret is not None:
                returns.append(daily_ret)

            # Update signal for next iteration
            if today_weights:
                prev_weights = today_weights

        except Exception:
            _IN_PROCESS_SIGNAL_MEMO[memo_key] = None
            logger.warning(
                "In-process scoring: failed to evaluate %s for %s",
                group_name,
                eval_date.isoformat(),
                exc_info=True,
            )
    return returns


def _fetch_or_backfill_returns(
    fragment: PortfolioFragment,
    group_id: str,
    group_name: str,
    window: int,
    context: DslContext,
) -> list[Decimal]:
    """Fetch historical returns from cache, triggering backfill on miss.

    On cache miss, attempts Lambda-based backfill first (if DATA_FUNCTION_NAME
    is set). Falls back to in-process backfill when running locally or when
    Lambda invocation fails.
    """
    lookback_calendar_days = int(window * 2.5) + 10

    # When running inside a nested backfill, the indicator service has
    # as_of_date set to the outer evaluation date.  Bound the cache
    # lookup to that date to prevent look-ahead bias.
    anchor_date: date | None = getattr(context.indicator_service, "as_of_date", None)

    historical_returns = lookup_historical_returns(
        group_id=group_id,
        lookback_days=lookback_calendar_days,
        end_date=anchor_date,
    )

    if len(historical_returns) >= window:
        return historical_returns

    # On-demand backfill: re-evaluate group for historical dates
    ast_body = _AST_BODY_STORE.get(fragment.fragment_id)
    if not ast_body:
        ast_body = _AST_BODY_BY_GROUP_ID.get(group_id)
    if not ast_body:
        return historical_returns

    logger.info(
        "DSL filter: cache miss for group -- triggering on-demand backfill",
        extra={
            "group_id": group_id,
            "group_name": group_name,
            "returns_available": len(historical_returns),
            "window_needed": window,
            "correlation_id": context.correlation_id,
        },
    )

    # Attempt Lambda-based backfill (production path)
    lambda_result = _try_lambda_backfill(
        group_id=group_id,
        group_name=group_name,
        lookback_days=lookback_calendar_days,
        correlation_id=context.correlation_id,
    )
    if lambda_result is not None:
        # Re-read from cache after Lambda backfill
        refreshed = lookup_historical_returns(
            group_id=group_id,
            lookback_days=lookback_calendar_days,
            end_date=anchor_date,
        )
        if len(refreshed) >= window:
            return refreshed
        logger.warning(
            "Lambda backfill completed but insufficient returns in cache",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "returns_after_lambda": len(refreshed),
                "window_needed": window,
                "correlation_id": context.correlation_id,
            },
        )

    # Fallback: in-process backfill (local runs or Lambda failure)
    return _backfill_group_cache(
        group_id=group_id,
        group_name=group_name,
        ast_body=ast_body,
        window=window,
        context=context,
    )


def _try_lambda_backfill(
    group_id: str,
    group_name: str,
    lookback_days: int,
    correlation_id: str,
) -> bool | None:
    """Invoke Data Lambda to backfill a single group via the orchestrator.

    Returns True if invocation succeeded, False if it failed, or None if
    Lambda-based backfill is not available (no DATA_FUNCTION_NAME env var).

    The Data Lambda routes the request to the group backfill orchestrator,
    which fans out to a dedicated worker Lambda for this group.

    Args:
        group_id: Deterministic group cache key.
        group_name: Human-readable group name.
        lookback_days: Calendar days to backfill.
        correlation_id: Tracing identifier.

    Returns:
        True on success, False on failure, None if not available.

    """
    import json
    import os

    data_function_name = os.environ.get("DATA_FUNCTION_NAME", "")
    if not data_function_name:
        return None

    # Discover strategy file from context
    strategy_file = os.environ.get("CURRENT_STRATEGY_FILE", "")
    if not strategy_file:
        logger.debug(
            "Lambda backfill skipped: no CURRENT_STRATEGY_FILE env var",
            extra={"group_id": group_id},
        )
        return None

    try:
        import boto3
        from botocore.config import Config

        config = Config(
            read_timeout=910,
            connect_timeout=10,
            retries={"max_attempts": 0},
        )
        lambda_client = boto3.client("lambda", config=config)

        payload = {
            "action": "group_backfill",
            "strategy_file": strategy_file,
            "groups": [
                {
                    "group_id": group_id,
                    "group_name": group_name,
                    "depth": 0,
                    "parent_filter_metric": "unknown",
                },
            ],
            "lookback_days": lookback_days,
            "correlation_id": correlation_id,
            "requesting_component": "group_scoring",
        }

        logger.info(
            "Invoking Data Lambda for group backfill",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "function_name": data_function_name,
                "correlation_id": correlation_id,
            },
        )

        response = lambda_client.invoke(
            FunctionName=data_function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )

        status_code = response.get("StatusCode", 500)
        if status_code != 200:
            logger.warning(
                "Data Lambda returned non-200 status for group backfill",
                extra={
                    "group_id": group_id,
                    "status_code": status_code,
                    "correlation_id": correlation_id,
                },
            )
            return False

        response_payload = json.loads(response["Payload"].read().decode())
        body = response_payload.get("body", {})
        groups_processed = body.get("groups_processed", 0)
        groups_failed = body.get("groups_failed", 0)

        logger.info(
            "Data Lambda group backfill completed",
            extra={
                "group_id": group_id,
                "groups_processed": groups_processed,
                "groups_failed": groups_failed,
                "correlation_id": correlation_id,
            },
        )

        return groups_processed > 0 and groups_failed == 0

    except Exception as exc:
        logger.warning(
            "Lambda-based group backfill failed, will fall back to in-process",
            extra={
                "group_id": group_id,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "correlation_id": correlation_id,
            },
        )
        return False


# ---------------------------------------------------------------------------
# Helpers: DSL value unwrapping
# ---------------------------------------------------------------------------


def unwrap_single_element_list(value: DSLValue) -> DSLValue:
    """Recursively unwrap single-element lists.

    DSL evaluation sometimes produces nested lists like [[PortfolioFragment]]
    when the syntax uses brackets around single expressions. This function
    unwraps those to get the actual value.
    """
    while isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value


# ---------------------------------------------------------------------------
# Portfolio metric computation
# ---------------------------------------------------------------------------


def _compute_portfolio_metric(
    returns: list[Decimal],
    metric_name: str,
    window: int,
) -> float | None:
    """Compute a portfolio-level metric from a series of daily returns.

    Mirrors the formulas in ``TechnicalIndicators`` but operates on a
    pre-built return series rather than a raw price series.

    The *returns* list is expected to be sorted oldest-first and each
    element is a fractional daily return (e.g., Decimal("0.0153") = +1.53%).

    Args:
        returns: Daily portfolio returns, oldest-first.
        metric_name: One of ``moving_average_return``, ``cumulative_return``,
            ``stdev_return``, ``max_drawdown``, ``rsi``.
        window: Lookback window size (number of trading days).

    Returns:
        Computed score as float (in percentage terms to match existing
        per-symbol indicator output), or None if insufficient data.

    """
    if len(returns) < _MIN_RETURNS_FOR_METRIC:
        return None

    # Use up to *window* most recent returns
    series = returns[-window:] if len(returns) >= window else returns

    if metric_name == "moving_average_return":
        return _metric_moving_average_return(series, window)
    if metric_name == "cumulative_return":
        return _metric_cumulative_return(series, window)
    if metric_name == "stdev_return":
        return _metric_stdev_return(series, window)
    if metric_name == "max_drawdown":
        return _metric_max_drawdown(series, window)
    if metric_name == "rsi":
        return _metric_rsi(series, window)

    logger.warning("Unknown portfolio metric: %s", metric_name)
    return None


def _metric_moving_average_return(series: list[Decimal], window: int) -> float:
    """Mean of daily returns, expressed as a percentage.

    Matches ``TechnicalIndicators.moving_average_return`` which computes
    ``pct_change().rolling(window).mean() * 100``.
    """
    total = sum(series)
    mean = total / Decimal(str(len(series)))
    return float(mean * Decimal("100"))


def _metric_cumulative_return(series: list[Decimal], window: int) -> float:
    """Compound return over the series, expressed as a percentage.

    Matches ``TechnicalIndicators.cumulative_return`` which computes
    ``(price / price.shift(window) - 1) * 100``, equivalent to
    ``(prod(1 + r_i) - 1) * 100`` on a return series.
    """
    cumulative = Decimal("1")
    for r in series:
        cumulative *= Decimal("1") + r
    return float((cumulative - Decimal("1")) * Decimal("100"))


def _metric_stdev_return(series: list[Decimal], window: int) -> float:
    """Annualised population standard deviation of daily returns.

    Matches ``TechnicalIndicators.stdev_return`` which computes
    ``pct_change() * 100 |> rolling(window).std(ddof=0) * sqrt(252)``.
    """
    n = len(series)
    # Convert to percentage returns first (matching TechnicalIndicators)
    pct_series = [r * Decimal("100") for r in series]
    mean = sum(pct_series) / Decimal(str(n))
    variance = sum((x - mean) ** 2 for x in pct_series) / Decimal(str(n))
    std = Decimal(str(math.sqrt(float(variance))))
    annualised = std * _ANNUALISATION_SQRT_252
    return float(annualised)


def _metric_max_drawdown(series: list[Decimal], window: int) -> float:
    """Maximum peak-to-trough decline from equity curve, as percentage.

    Reconstructs a cumulative equity curve from the return series, then
    computes the maximum drawdown.  Matches the semantics of
    ``TechnicalIndicators.max_drawdown``.
    """
    # Build equity curve (start at 1.0)
    equity = Decimal("1")
    peak = equity
    max_dd = Decimal("0")

    for r in series:
        equity *= Decimal("1") + r
        if equity > peak:
            peak = equity
        if peak > Decimal("0"):
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd

    return float(max_dd * Decimal("100"))


def _metric_rsi(series: list[Decimal], window: int) -> float:
    """RSI of a synthetic price series reconstructed from daily returns.

    Rebuilds a price series from fractional daily returns, then applies
    Wilder's smoothing (EWM with alpha = 1/window) to match the formula
    in ``TechnicalIndicators.rsi``.
    """
    # Reconstruct price series: P[0]=100, P[i] = P[i-1] * (1 + r[i])
    prices: list[Decimal] = [Decimal("100")]
    for r in series:
        prices.append(prices[-1] * (Decimal("1") + r))

    # Compute price deltas
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    if not deltas:
        return 50.0  # Neutral RSI when no data

    # Separate gains and losses
    gains = [max(d, Decimal("0")) for d in deltas]
    losses = [max(-d, Decimal("0")) for d in deltas]

    # Wilder's EWM (alpha = 1/window, adjust=False)
    alpha = Decimal("1") / Decimal(str(window))
    one_minus_alpha = Decimal("1") - alpha

    avg_gain = gains[0]
    avg_loss = losses[0]
    for i in range(1, len(gains)):
        avg_gain = alpha * gains[i] + one_minus_alpha * avg_gain
        avg_loss = alpha * losses[i] + one_minus_alpha * avg_loss

    # Compute RSI
    if avg_loss == Decimal("0"):
        return 100.0
    rs = avg_gain / avg_loss
    rsi_val = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
    return float(rsi_val)
