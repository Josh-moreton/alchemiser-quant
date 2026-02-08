#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Portfolio construction operators for DSL evaluation.

Implements DSL operators for building portfolio allocations:
- weight-equal: Equal weight allocation across assets
- weight-specified: Specified weight allocation with explicit weights
- weight-inverse-volatility: Inverse volatility weighting scheme
- group: Aggregate and combine portfolio fragments
- asset: Single asset reference
- filter: Asset filtering based on conditions
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from engines.dsl.context import DslContext, FilterCandidate, FilterTrace, ScoringPath
from engines.dsl.dispatcher import DslDispatcher
from engines.dsl.operators.control_flow import create_indicator_with_symbol
from engines.dsl.operators.group_cache_lookup import (
    is_cache_available,
    lookup_historical_returns,
    write_historical_return,
)
from engines.dsl.types import DslEvaluationError, DSLValue

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.ast_node import ASTNode
from the_alchemiser.shared.schemas.indicator_request import (
    IndicatorRequest,
    PortfolioFragment,
)

logger = get_logger(__name__)

# Volatility calculation constants
STDEV_RETURN_6_WINDOW = 6  # Standard 6-period volatility window

# Pattern matching valid trading symbols (1-5 uppercase letters/digits,
# plus optional share-class suffix like /B or .B for BRK/B, BF.B etc.).
# Anything that does NOT match is treated as a named portfolio/strategy
# group requiring proper historical composite scoring.
_TICKER_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9]{0,4}([/.][A-Z])?$")


def _derive_group_id(group_name: str) -> str:
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


def _is_bare_asset_fragment(fragment: PortfolioFragment, group_name: object) -> bool:
    """Return True if the fragment is a bare symbol, not a named portfolio.

    The check is intentionally simple: if the ``group_name`` looks like a
    trading symbol (1-5 uppercase letters/digits, with optional share-class
    suffix like ``/B`` or ``.B`` for BRK/B, BF.B) it is a bare asset that
    was wrapped by ``_normalize_portfolio_items``.  Anything else -- long
    names, mixed case, spaces, apostrophes -- is a real strategy /
    portfolio group that must go through cache or in-process scoring so
    its historical composite return stream is properly reconstructed.

    This avoids fragile heuristics based on ``_AST_BODY_STORE`` presence or
    ``source_step``, which can break when fragments are re-wrapped across
    evaluation layers.

    Args:
        fragment: The portfolio fragment to check.
        group_name: The group_name metadata value (may be ``None``).

    Returns:
        True when the group_name matches a ticker-symbol pattern.

    """
    if not isinstance(group_name, str) or not group_name:
        return False
    return bool(_TICKER_SYMBOL_RE.match(group_name))


# ---------- On-demand group cache backfill ----------

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

# Maximum number of calendar days to backfill in a single on-demand run.
# Keeps Lambda execution time bounded (each day requires re-evaluation
# of the full group AST + bar fetches for every holding).
_MAX_BACKFILL_CALENDAR_DAYS = 45


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
            logger.debug(
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
        # Use as_of_date as the anchor when running inside a nested
        # backfill (e.g. WYLD's body triggers OFR inner-group backfill).
        # This prevents look-ahead bias: inner groups must only see data
        # available up to the outer evaluation date, not real today.
        anchor_date = original_as_of_date or datetime.now(UTC).date()
        calendar_days = min(int(window * 2.5) + 10, _MAX_BACKFILL_CALENDAR_DAYS)
        trading_days = _get_trading_days(anchor_date, calendar_days)

        # Check which dates already exist in cache
        existing_returns = lookup_historical_returns(
            group_id=group_id,
            lookback_days=calendar_days,
            end_date=anchor_date,
        )
        # We don't have per-date info from lookup_historical_returns, so
        # we just check the count.  If we already have enough, return early.
        if len(existing_returns) >= window:
            logger.info(
                "Backfill not needed: cache already has %d returns (need %d)",
                len(existing_returns),
                window,
                extra={"group_id": group_id},
            )
            return list(existing_returns)

        backfilled_returns: list[tuple[str, Decimal]] = []

        logger.info(
            "Starting on-demand backfill",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "trading_days_to_evaluate": len(trading_days),
                "window_needed": window,
                "correlation_id": context.correlation_id,
            },
        )

        for eval_date in trading_days:
            try:
                # Set point-in-time evaluation date
                indicator_svc.as_of_date = eval_date

                # Re-evaluate the group body AST to get that day's selections
                last_result: DSLValue = None
                for expr in ast_body:
                    last_result = context.evaluate_node(expr, context.correlation_id, context.trace)

                last_result = _unwrap_single_element_list(last_result)

                # Extract weights from the evaluation result
                if isinstance(last_result, PortfolioFragment):
                    day_weights = dict(last_result.weights)
                else:
                    day_weights = collect_weights_from_value(last_result) if last_result else {}

                if not day_weights:
                    continue

                # Compute portfolio return for this date
                daily_ret = _compute_daily_return_for_portfolio(
                    selections=day_weights,
                    record_date=eval_date,
                    context=context,
                )

                logger.info(
                    "Backfill: group resolved for date",
                    extra={
                        "group_id": group_id,
                        "group_name": group_name,
                        "eval_date": eval_date.isoformat(),
                        "selections": {k: str(v) for k, v in day_weights.items()},
                        "daily_return": str(daily_ret) if daily_ret is not None else "None",
                        "correlation_id": context.correlation_id,
                    },
                )

                if daily_ret is None:
                    continue

                # Write to DynamoDB cache
                selections_str = {sym: str(w) for sym, w in day_weights.items()}
                write_historical_return(
                    group_id=group_id,
                    record_date=eval_date.isoformat(),
                    selections=selections_str,
                    portfolio_daily_return=daily_ret,
                )
                backfilled_returns.append((eval_date.isoformat(), daily_ret))

            except Exception as exc:
                logger.warning(
                    "Backfill: failed to evaluate date %s for group %s (%s): %s",
                    eval_date.isoformat(),
                    group_name,
                    group_id,
                    exc,
                    exc_info=True,
                )

        # Restore original as_of_date is handled in the finally block

        logger.info(
            "On-demand backfill completed",
            extra={
                "group_id": group_id,
                "group_name": group_name,
                "days_backfilled": len(backfilled_returns),
                "correlation_id": context.correlation_id,
            },
        )

        # Return the full set of returns (existing + new), oldest-first
        # Re-query the cache to get a clean sorted series, bounded by
        # the anchor date to prevent look-ahead bias in nested backfill.
        refreshed = lookup_historical_returns(
            group_id=group_id,
            lookback_days=calendar_days,
            end_date=anchor_date,
        )
        return list(refreshed)

    finally:
        # Always restore as_of_date to prevent the shared indicator_service
        # from staying pinned to a historical date after an exception.
        if hasattr(indicator_svc, "as_of_date"):
            indicator_svc.as_of_date = original_as_of_date
        _BACKFILL_IN_PROGRESS.discard(group_id)


# ---------- Shared helpers ----------


def _describe_filter_condition(condition_expr: ASTNode, context: DslContext) -> dict[str, object]:
    """Create a compact, structured description of a filter condition.

    Intended for debug tracing only.
    """
    if not condition_expr.is_list() or not condition_expr.children:
        return {"type": "unknown"}

    head = condition_expr.children[0]
    func_name = head.get_symbol_name() if head.is_symbol() else None
    desc: dict[str, object] = {"type": "indicator", "func": func_name or "unknown"}

    # Many filter conditions are of the form: (indicator {:window N})
    if len(condition_expr.children) > 1:
        try:
            params_val = context.evaluate_node(
                condition_expr.children[1], context.correlation_id, context.trace
            )
            if isinstance(params_val, dict):
                desc["params"] = params_val
        except (DslEvaluationError, ValueError, TypeError) as exc:  # Debug-only: never fail eval
            logger.debug("DSL filter: failed to evaluate condition params for tracing: %s", exc)

    return desc


def _extract_window_from_condition(condition_expr: ASTNode, context: DslContext) -> int | None:
    """Extract the window size from a filter condition expression.

    Parses expressions like (moving-average-return {:window 10}) or
    (stdev-return {:window 12}) to extract the window value.

    Returns None if window cannot be extracted.
    """
    if not condition_expr.is_list() or len(condition_expr.children) < 2:
        return None

    try:
        params_val = context.evaluate_node(
            condition_expr.children[1], context.correlation_id, context.trace
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


# ---------- Cached portfolio metric computation ----------

# Minimum number of return data points required for metric computation.
# If fewer returns are available, fail closed (return None).
_MIN_RETURNS_FOR_METRIC = 3

# DSL operator names → canonical metric identifiers used for dispatch.
_METRIC_DISPATCH: dict[str, str] = {
    "moving-average-return": "moving_average_return",
    "cumulative-return": "cumulative_return",
    "stdev-return": "stdev_return",
    "max-drawdown": "max_drawdown",
    "rsi": "rsi",
}

# Annualisation factor for stdev (matches TechnicalIndicators.stdev_return).
_ANNUALISATION_SQRT_252 = Decimal("15.8745078664")  # sqrt(252) to 10dp


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
    # Use float sqrt for precision - Decimal doesn't have native sqrt
    import math

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


def collect_assets_from_value(value: DSLValue) -> list[str]:
    """Recursively extract all asset symbols from a DSLValue.

    Handles `PortfolioFragment`, single symbol strings, and nested lists.
    NOTE: This discards weight information - use collect_weights_from_value
    when you need to preserve weights.
    """
    if isinstance(value, PortfolioFragment):
        return list(value.weights.keys())
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        symbols: list[str] = []
        for item in value:
            symbols.extend(collect_assets_from_value(item))
        return symbols
    return []


def collect_weights_from_value(value: DSLValue) -> dict[str, Decimal]:
    """Recursively extract all asset weights from a DSLValue.

    Handles `PortfolioFragment`, single symbol strings, and nested lists.
    Preserves weight information from PortfolioFragments.
    For bare symbols, assigns weight of 1.0 (to be normalized later).
    For lists, merges weights by addition.
    """
    if isinstance(value, PortfolioFragment):
        return dict(value.weights)
    if isinstance(value, str):
        return {value: Decimal("1.0")}
    if isinstance(value, list):
        merged: dict[str, Decimal] = {}
        for item in value:
            item_weights = collect_weights_from_value(item)
            for sym, w in item_weights.items():
                merged[sym] = merged.get(sym, Decimal("0")) + w
        return merged
    return {}


def parse_selection(sel_expr: ASTNode | None, context: DslContext) -> tuple[bool, int | None]:
    """Parse optional selection expression returning (take_top, take_n).

    - take_top: True implies sort descending; False ascending (select-bottom)
    - take_n: Optional limit; None if not parseable
    """
    take_top = True
    take_n: int | None = None
    if sel_expr:
        sel_name = (
            sel_expr.children[0].get_symbol_name()
            if sel_expr.is_list() and sel_expr.children
            else None
        )
        if sel_name == "select-bottom":
            take_top = False
        n_val = context.evaluate_node(sel_expr, context.correlation_id, context.trace)
        try:
            take_n = (
                int(n_val) if isinstance(n_val, int | float) else int(context.as_decimal(n_val))
            )
        except (ValueError, TypeError) as exc:
            logger.warning("DSL parse_selection: Failed to parse selection limit: %s", exc)
            take_n = None
    return take_top, take_n


def score_candidates(
    symbols: list[str],
    condition_expr: ASTNode,
    context: DslContext,
) -> list[tuple[str, float]]:
    """Evaluate condition for each candidate symbol and return (symbol, score)."""
    scored: list[tuple[str, float]] = []
    for sym in symbols:
        try:
            metric_expr = create_indicator_with_symbol(condition_expr, sym)
            metric_val = context.evaluate_node(metric_expr, context.correlation_id, context.trace)
            metric_val = (
                float(metric_val)
                if isinstance(metric_val, int | float)
                else float(context.as_decimal(metric_val))
            )
            scored.append((sym, metric_val))
        except (ValueError, TypeError, DslEvaluationError) as exc:
            logger.warning(
                "DSL filter: condition evaluation failed for symbol %s: %s",
                sym,
                exc,
            )
    return scored


# Score proximity threshold for flagging fragile rankings (1% of score range)
SCORE_PROXIMITY_THRESHOLD_PCT = 0.01


def _deterministic_symbol_sort(
    scored: list[tuple[str, float]], order: Literal["top", "bottom"]
) -> list[tuple[str, float]]:
    """Sort scored candidates with deterministic tiebreaker.

    Primary sort: by score (descending for top, ascending for bottom).
    Secondary sort: by symbol name alphabetically (ascending) when scores
    are identical. This prevents non-deterministic ordering when multiple
    candidates share the same score, which causes ranking instability
    in strategies like rains_em_dancer where safe-asset RSI values are
    very close.

    Args:
        scored: List of (symbol, score) tuples
        order: "top" for descending score order, "bottom" for ascending

    Returns:
        Sorted list of (symbol, score) tuples

    """
    if order == "top":
        scored.sort(key=lambda x: (-x[1], x[0]))
    else:
        scored.sort(key=lambda x: (x[1], x[0]))
    return scored


def _log_score_proximity(
    scored: list[tuple[str, float]],
    limit: int | None,
    context: DslContext,
    condition_expr: ASTNode | None = None,
) -> None:
    """Log warning when top candidates have very close scores.

    When the score gap between the selected cutoff and the next
    candidate is very small, the ranking is fragile and may diverge
    from Composer due to minor indicator computation differences.

    Args:
        scored: Sorted list of (candidate_id, score) tuples
        limit: How many items are being selected
        context: DSL evaluation context for logging
        condition_expr: Optional AST node for the filter condition (indicator)

    """
    if limit is None or limit <= 0 or limit >= len(scored):
        return

    last_selected_sym = scored[limit - 1][0]
    last_selected_score = scored[limit - 1][1]
    first_rejected_sym = scored[limit][0]
    first_rejected_score = scored[limit][1]

    score_range = abs(scored[0][1] - scored[-1][1]) if len(scored) > 1 else 1.0
    if score_range < 1e-10:
        score_range = 1.0  # Avoid division by zero

    gap = abs(last_selected_score - first_rejected_score)
    relative_gap = gap / score_range

    if relative_gap < SCORE_PROXIMITY_THRESHOLD_PCT:
        # Extract indicator name from condition expression
        indicator = "unknown"
        if condition_expr and condition_expr.is_list() and condition_expr.children:
            head = condition_expr.children[0]
            indicator = head.get_symbol_name() or "unknown"

        all_symbols = [sym for sym, _ in scored]
        logger.warning(
            "FRAGILE RANKING: score gap at boundary < 1%% of range, may diverge from Composer",
            strategy=context.trace.strategy_id,
            indicator=indicator,
            last_selected=last_selected_sym,
            last_selected_score=round(last_selected_score, 6),
            first_rejected=first_rejected_sym,
            first_rejected_score=round(first_rejected_score, 6),
            gap=round(gap, 6),
            score_range=round(score_range, 6),
            relative_gap=round(relative_gap, 4),
            all_candidates=all_symbols,
            correlation_id=context.correlation_id,
        )


def _log_portfolio_score_proximity(
    scored: list[tuple[PortfolioFragment, float, ScoringPath]],
    limit: int | None,
    context: DslContext,
    condition_expr: ASTNode | None = None,
) -> None:
    """Log warning when portfolio scores near the selection boundary are close.

    When the score gap between the last selected and first rejected portfolio
    is very small relative to the total score range, the ranking is fragile.

    Args:
        scored: Sorted list of (portfolio, score, scoring_path) tuples
        limit: How many portfolios are being selected
        context: DSL evaluation context for logging
        condition_expr: Optional AST node for the filter condition (indicator)

    """
    if limit is None or limit <= 0 or limit >= len(scored):
        return

    last_selected_score = scored[limit - 1][1]
    first_rejected_score = scored[limit][1]

    score_range = abs(scored[0][1] - scored[-1][1]) if len(scored) > 1 else 1.0
    if score_range < 1e-10:
        score_range = 1.0

    gap = abs(last_selected_score - first_rejected_score)
    relative_gap = gap / score_range

    if relative_gap < SCORE_PROXIMITY_THRESHOLD_PCT:
        last_name = scored[limit - 1][0].metadata.get("group_name", "unnamed")
        next_name = scored[limit][0].metadata.get("group_name", "unnamed")

        # Extract indicator name from condition expression
        indicator = "unknown"
        if condition_expr and condition_expr.is_list() and condition_expr.children:
            head = condition_expr.children[0]
            indicator = head.get_symbol_name() or "unknown"

        logger.warning(
            "FRAGILE PORTFOLIO RANKING: score gap at boundary < 1%% of range, may diverge from Composer",
            strategy=context.trace.strategy_id,
            indicator=indicator,
            last_selected=last_name,
            last_selected_score=round(last_selected_score, 6),
            first_rejected=next_name,
            first_rejected_score=round(first_rejected_score, 6),
            gap=round(gap, 6),
            score_range=round(score_range, 6),
            relative_gap=round(relative_gap, 4),
            correlation_id=context.correlation_id,
        )


def select_symbols(
    condition_expr: ASTNode,
    symbols: list[str],
    order: Literal["top", "bottom"],
    limit: int | None,
    context: DslContext,
) -> PortfolioFragment:
    """Score, sort, and select symbols based on selection parameters.

    order: "top" sorts descending (highest first); "bottom" ascending.
    limit: optional number of items to return.

    Returns a PortfolioFragment with equal weights for selected symbols.
    """
    scored = score_candidates(symbols, condition_expr, context)
    if not scored:
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )
    scored = _deterministic_symbol_sort(scored, order)
    full_sorted = list(scored)
    _log_score_proximity(scored, limit, context)
    if limit is not None and limit >= 0:
        scored = scored[:limit]

    # Create equal-weighted fragment for selected symbols
    selected_symbols = [sym for sym, _ in scored]

    # Trace ranking/selection for parity debugging
    symbol_trace: FilterTrace = {
        "mode": "symbol",
        "order": order,
        "limit": limit,
        "condition": _describe_filter_condition(condition_expr, context),
        "scored_candidates": [
            FilterCandidate(
                candidate_id=sym,
                candidate_type="symbol",
                candidate_name=None,
                score=float(score),
                rank=rank,
                symbol_count=1,
                symbols_sample=[sym],
            )
            for rank, (sym, score) in enumerate(full_sorted)
        ],
        "selected_candidate_ids": list(selected_symbols),
    }
    context.add_filter_trace(symbol_trace)

    if not selected_symbols:
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )

    weight_per_asset = Decimal("1") / Decimal(str(len(selected_symbols)))
    weights = dict.fromkeys(selected_symbols, weight_per_asset)

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="filter",
        weights=weights,
    )


def _normalize_fragment_weights(value: DSLValue, context: DslContext) -> dict[str, Decimal]:
    """Convert a DSLValue into a normalized weights dict using Decimal arithmetic.

    COMPOSER BEHAVIOR: Each PortfolioFragment is treated as a single unit.
    When a list contains multiple PortfolioFragments, they are merged with
    equal weight per fragment (not per symbol).

    - str → {symbol: Decimal("1.0")}
    - PortfolioFragment → normalized weights (already Decimal)
    - list → each PortfolioFragment gets equal share, internal weights preserved
    """
    if isinstance(value, str):
        return {value: Decimal("1.0")}
    if isinstance(value, PortfolioFragment):
        frag = value.normalize_weights()
        return dict(frag.weights)  # Already Decimal after Phase 1
    if isinstance(value, list):
        # COMPOSER BEHAVIOR: Each item (fragment or symbol) gets equal share
        # We don't recursively extract symbols from PortfolioFragments
        items: list[dict[str, Decimal]] = []
        for item in value:
            # Unwrap single-element lists (syntax artifact)
            while isinstance(item, list) and len(item) == 1:
                item = item[0]

            if isinstance(item, PortfolioFragment):
                frag = item.normalize_weights()
                items.append(dict(frag.weights))
            elif isinstance(item, str):
                items.append({item: Decimal("1.0")})
            elif isinstance(item, list):
                # Nested list - recursively process but keep as one item
                nested = _normalize_fragment_weights(item, context)
                if nested:
                    items.append(nested)
            # Other types ignored

        if not items:
            return {}

        # Each item gets equal share
        item_share = Decimal("1") / Decimal(str(len(items)))
        merged: dict[str, Decimal] = {}
        for item_weights in items:
            for sym, w in item_weights.items():
                merged[sym] = merged.get(sym, Decimal("0")) + w * item_share

        return merged
    return {}


def _process_weight_asset_pairs(pairs: list[ASTNode], context: DslContext) -> dict[str, Decimal]:
    """Process (w1 a1 w2 a2 ...) pairs into consolidated weights using Decimal arithmetic."""
    consolidated: dict[str, Decimal] = {}
    for i in range(0, len(pairs), 2):
        weight_node, asset_node = pairs[i], pairs[i + 1]
        weight_val = context.evaluate_node(weight_node, context.correlation_id, context.trace)
        # Convert to Decimal
        if isinstance(weight_val, Decimal):
            weight_decimal = weight_val
        elif isinstance(weight_val, int | float):
            weight_decimal = Decimal(str(weight_val))
        else:
            weight_decimal = context.as_decimal(weight_val)
        asset_val = context.evaluate_node(asset_node, context.correlation_id, context.trace)
        normalized_assets = _normalize_fragment_weights(asset_val, context)
        if not normalized_assets:
            raise DslEvaluationError(f"Expected asset symbol or fragment, got {type(asset_val)}")
        for sym, base_w in normalized_assets.items():
            scaled = base_w * weight_decimal  # Decimal multiplication!
            consolidated[sym] = consolidated.get(sym, Decimal("0")) + scaled
    return consolidated


def _flatten_to_weight_dicts(value: DSLValue) -> list[dict[str, Decimal]]:
    """Convert a DSLValue into a list of normalized weight dictionaries.

    COMPOSER BEHAVIOR: Each PortfolioFragment is treated as a SINGLE child
    (atomic unit). Weight operators apply weights to groups, not to individual
    symbols extracted from groups.

    For a PortfolioFragment: returns single-item list (the group's normalized weights)
    For a string: returns single-item list with symbol at 100%
    For a list: each PortfolioFragment/string in the list becomes ONE child
                (no recursive extraction of symbols from PortfolioFragments)

    This matches Composer.trade behavior where filter/sort operations pass
    groups up to parent weight operators as single units.
    """
    if isinstance(value, PortfolioFragment):
        frag = value.normalize_weights()
        return [dict(frag.weights)]
    if isinstance(value, str):
        return [{value: Decimal("1.0")}]
    if isinstance(value, list):
        result: list[dict[str, Decimal]] = []
        for item in value:
            # COMPOSER BEHAVIOR: Don't recursively flatten PortfolioFragments
            # Each item (fragment or symbol) becomes exactly one child
            if isinstance(item, PortfolioFragment):
                frag = item.normalize_weights()
                result.append(dict(frag.weights))
            elif isinstance(item, str):
                result.append({item: Decimal("1.0")})
            elif isinstance(item, list):
                # Nested lists are still flattened (syntax artifact like [[group]])
                result.extend(_flatten_to_weight_dicts(item))
            # Other types (int, float, etc.) are ignored
        return result
    return []


# ---------- Operators ----------


def weight_equal(args: list[ASTNode], context: DslContext) -> PortfolioFragment:
    """Evaluate weight-equal - allocate equal weight to all children.

    Each child (argument) of weight-equal receives an equal share of the total
    weight (1/n where n = number of children). The child's internal weights
    are scaled by this share.

    This is the correct Composer behavior: weight-equal distributes weight
    equally among its children, regardless of how many assets each child contains.

    IMPORTANT: When a single argument evaluates to a list, each item in that
    list is treated as a separate child for equal weighting. This handles the
    common pattern: (weight-equal [(group ...) (group ...) ...])

    Example:
        (weight-equal [child1, child2])
        - child1 evaluates to {A: 100%}
        - child2 evaluates to {B: 60%, C: 40%}
        - Result: child1 gets 50%, child2 gets 50%
        - Final: {A: 50%, B: 30%, C: 20%}

    This prevents weight accumulation in deeply nested structures where
    the same asset (e.g., BIL) appears in multiple branches.

    """
    if not args:
        raise DslEvaluationError(
            "weight-equal requires at least one asset argument. "
            "DSL strategies must always produce a non-empty allocation."
        )

    # Evaluate all arguments and flatten lists into separate children
    evaluated_children: list[dict[str, Decimal]] = []
    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)
        # Flatten the result - if it's a list, each item becomes a separate child
        child_weight_dicts = _flatten_to_weight_dicts(result)
        for child_weights in child_weight_dicts:
            if child_weights:
                # Normalize child weights to sum to 1.0 before scaling
                child_total = sum(child_weights.values())
                if child_total > Decimal("0"):
                    child_weights = {sym: w / child_total for sym, w in child_weights.items()}
                evaluated_children.append(child_weights)

    if not evaluated_children:
        raise DslEvaluationError(
            "DSL weight-equal received no assets after evaluation. "
            "Strategies must always produce a non-empty allocation."
        )

    # Each child gets equal weight
    child_share = Decimal("1") / Decimal(str(len(evaluated_children)))

    # Scale each child's weights by their share and merge
    all_weights: dict[str, Decimal] = {}
    for child_weights in evaluated_children:
        for sym, w in child_weights.items():
            scaled_weight = w * child_share
            all_weights[sym] = all_weights.get(sym, Decimal("0")) + scaled_weight

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_equal",
        weights=all_weights,
    )


# ---------- Weight specified ----------


def _validate_weight_specified_args(args: list[ASTNode]) -> None:
    """Validate `weight-specified` arguments follow (w1 a1 w2 a2 ...).

    Requires at least one pair and an even number of arguments.
    """
    invalid_arg_count = len(args) < 2
    not_pairs = (len(args) % 2) != 0
    if invalid_arg_count or not_pairs:
        raise DslEvaluationError("weight-specified requires pairs of weight and asset arguments")


def weight_specified(args: list[ASTNode], context: DslContext) -> PortfolioFragment:
    """Evaluate weight-specified: (weight-specified w1 asset1 w2 asset2 ...)."""
    _validate_weight_specified_args(args)
    weights = _process_weight_asset_pairs(args, context)
    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_specified",
        weights=weights,
    )


def _collect_assets_from_args(args: list[ASTNode], context: DslContext) -> list[str]:
    """Collect assets from DSL arguments (flat mode - extracts individual symbols).

    Args:
        args: List of AST nodes (excluding window parameter)
        context: DSL evaluation context

    Returns:
        List of asset symbols

    """
    all_assets: list[str] = []

    def _extract_assets(value: DSLValue) -> None:
        """Recursively extract asset symbols from a DSL value."""
        if isinstance(value, PortfolioFragment):
            all_assets.extend(value.weights.keys())
        elif isinstance(value, list):
            for item in value:
                _extract_assets(item)
        elif isinstance(value, str):
            all_assets.append(value)

    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)
        _extract_assets(result)

    return all_assets


def _collect_groups_from_args(
    args: list[ASTNode], context: DslContext
) -> tuple[bool, list[PortfolioFragment]]:
    """Collect PortfolioFragment groups from DSL arguments (grouped mode).

    Returns (is_grouped_mode, list_of_fragments).
    Grouped mode is True when all evaluated args are PortfolioFragments.

    Args:
        args: List of AST nodes (excluding window parameter)
        context: DSL evaluation context

    Returns:
        Tuple of (is_grouped_mode, fragments)

    """
    fragments: list[PortfolioFragment] = []

    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)

        # Unwrap single-element lists (syntax artifact like [[group]])
        while isinstance(result, list) and len(result) == 1:
            result = result[0]

        if isinstance(result, PortfolioFragment):
            fragments.append(result)
        elif isinstance(result, list):
            # List of items - check if all are PortfolioFragments
            for item in result:
                # Unwrap nested single-element lists
                while isinstance(item, list) and len(item) == 1:
                    item = item[0]
                if isinstance(item, PortfolioFragment):
                    fragments.append(item)
                elif isinstance(item, str):
                    # Mixed mode: has bare symbols, not grouped
                    return False, []
                else:
                    # Mixed or unexpected type inside list: not grouped mode
                    return False, []
        elif isinstance(result, str):
            # Bare symbol = not grouped mode
            return False, []
        else:
            # Any other unexpected type: fall back to flat mode
            return False, []

    return bool(fragments), fragments


def _calculate_group_volatility(
    fragment: PortfolioFragment, window: float, context: DslContext
) -> float | None:
    """Calculate weighted-average volatility for a PortfolioFragment group.

    Args:
        fragment: The portfolio fragment (group)
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Weighted-average volatility or None if no valid volatilities

    """
    weights = fragment.weights
    if not weights:
        return None

    total_weight = Decimal("0")
    weighted_vol_sum = Decimal("0")

    for sym, weight in weights.items():
        volatility = _get_volatility_for_asset(sym, window, context)
        if volatility is not None:
            weighted_vol_sum += weight * Decimal(str(volatility))
            total_weight += weight

    if total_weight > Decimal("0"):
        return float(weighted_vol_sum / total_weight)
    return None


def _distribute_group_shares(
    group_weights: list[tuple[PortfolioFragment, Decimal]], total_inverse: Decimal
) -> dict[str, Decimal]:
    """Distribute group-level weights to individual symbols.

    Normalizes group weights and scales internal symbol weights by each
    group's share of the total.

    Args:
        group_weights: List of (fragment, inverse_weight) tuples
        total_inverse: Sum of all inverse weights for normalization

    Returns:
        Dictionary mapping symbols to their final weights

    """
    final_weights: dict[str, Decimal] = {}

    for group, inverse_weight in group_weights:
        group_share = inverse_weight / total_inverse
        # Scale internal weights by group's share
        for sym, sym_weight in group.weights.items():
            contribution = group_share * sym_weight
            final_weights[sym] = final_weights.get(sym, Decimal("0")) + contribution

    return final_weights


def _calculate_inverse_weights_grouped(
    groups: list[PortfolioFragment], window: float, context: DslContext
) -> dict[str, Decimal]:
    """Calculate inverse volatility weights for groups (atomic units).

    GROUPED MODE - Used when children are PortfolioFragments.

    Per Composer's behavior:
    - Each group is treated as ONE atomic unit (not individual assets)
    - Group volatility = weighted-average volatility of its holdings
    - Groups are weighted against each other by 1/group_vol
    - Internal weights within each group are PRESERVED and scaled

    With 1 group: That group gets 100% -> internal weights pass through unchanged
    With N groups: Each group weighted by inverse of its volatility

    Example with 2 groups:
    - Group A (low vol): gets 80% share, internal weights scaled by 0.8
    - Group B (high vol): gets 20% share, internal weights scaled by 0.2

    NOTE: See _calculate_inverse_weights() docstring for DAMPENING EXPONENT
    history and reversal guide. The same reversal steps apply to this function
    (change the inverse_vol calculation below).

    Args:
        groups: List of PortfolioFragment groups
        window: Lookback window for volatility calculation (days)
        context: DSL evaluation context

    Returns:
        Dictionary mapping symbols to final weights (sum to 1.0)

    """
    group_weights: list[tuple[PortfolioFragment, Decimal]] = []
    total_inverse = Decimal("0")

    for group in groups:
        group_vol = _calculate_group_volatility(group, window, context)
        if group_vol is not None and group_vol > 0:
            vol_decimal = Decimal(str(group_vol))
            inverse_vol = Decimal("1") / vol_decimal
            group_weights.append((group, inverse_vol))
            total_inverse += inverse_vol
            logger.debug(
                "DSL weight-inverse-volatility grouped: group vol=%.6f, inverse_vol=%.6f",
                group_vol,
                float(inverse_vol),
            )

    if not group_weights or total_inverse < Decimal("1e-10"):
        logger.warning("DSL weight-inverse-volatility: No valid volatilities for any groups")
        return {}

    final_weights = _distribute_group_shares(group_weights, total_inverse)

    logger.debug(
        "DSL weight-inverse-volatility grouped: Applied group-level inverse-vol weights",
        extra={
            "num_groups": len(group_weights),
            "final_weights": {k: float(v) for k, v in final_weights.items()},
        },
    )

    return final_weights


def _get_volatility_for_asset(asset: str, window: float, context: DslContext) -> float | None:
    """Get volatility value for a single asset.

    Args:
        asset: Asset symbol
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Volatility value or None if unavailable/invalid

    """
    try:
        # Request volatility (stdev_return) for this asset using the window parameter
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            correlation_id=context.correlation_id,
            symbol=asset,
            indicator_type="stdev_return",
            parameters={"window": int(window)},
        )

        # Get volatility indicator from IndicatorService
        indicator = context.indicator_service.get_indicator(request)

        # Extract volatility value from indicator
        volatility = None

        # Check specific field for the window if available
        if int(window) == STDEV_RETURN_6_WINDOW and indicator.stdev_return_6 is not None:
            volatility = indicator.stdev_return_6
        # Fallback to metadata value
        elif indicator.metadata and "value" in indicator.metadata:
            try:
                volatility = float(indicator.metadata["value"])
            except (ValueError, TypeError):
                logger.warning(
                    "DSL weight-inverse-volatility: Failed to parse volatility from metadata for %s",
                    asset,
                )
                return None

        if volatility is None or volatility <= 0:
            logger.warning(
                "DSL weight-inverse-volatility: No valid volatility for %s, skipping",
                asset,
            )
            return None

        # Emit IndicatorComputed event for observability
        context.event_publisher.publish_indicator_computed(
            request_id=request.request_id,
            indicator=indicator,
            computation_time_ms=0.0,  # Not measuring computation time in this operator
            correlation_id=context.correlation_id,
        )

        return volatility

    except (ValueError, TypeError, AttributeError) as exc:
        logger.warning(
            "DSL weight-inverse-volatility: Failed to get volatility for %s: %s",
            asset,
            exc,
        )
        return None


def _calculate_inverse_weights(
    assets: list[str], window: float, context: DslContext
) -> dict[str, Decimal]:
    """Calculate inverse volatility weights for individual assets.

    FLAT MODE - Used when children are bare symbols, not groups.

    Per Composer's specification:
    - Volatility = standard deviation of percent returns over lookback window
    - Inverse volatility = 1 / volatility
    - Weight = inverse_vol / sum(all inverse_vols)

    This produces EXTREME concentration in low-vol assets. For example:
    - BIL (0.01% vol) vs LABU (4.3% vol) -> BIL gets ~99% weight

    ============================================================================
    DAMPENING EXPONENT HISTORY AND REVERSAL GUIDE
    ============================================================================
    PREVIOUSLY: weight proportional to (1/volatility)^0.25 (dampened inverse)
    CURRENTLY:  weight proportional to 1/volatility (pure inverse, no dampening)

    The 0.25 dampening exponent was INTENTIONALLY REMOVED to match Composer's
    exact behavior. Dampening reduces concentration by raising inverse_vol to
    a fractional power:
    - Exponent 0.25: weight = inverse_vol^0.25 (moderate concentration)
    - Exponent 1.0:  weight = inverse_vol      (extreme concentration, current)

    RATIONALE FOR REMOVAL:
    Composer's weight-inverse-volatility uses pure 1/vol without dampening.
    Our parity testing confirmed Composer produces extreme concentration in
    low-vol assets (e.g., BIL vs LABU). Dampening was a deviation from spec.

    TO REVERT (add 0.25 dampening back if needed):
    1. Add constant at module level:
       DAMPENING_EXPONENT = Decimal("0.25")
    2. Change this line below:
       inverse_vol = Decimal("1") / vol_decimal
       To:
       inverse_vol = (Decimal("1") / vol_decimal) ** DAMPENING_EXPONENT
    3. Apply the same change in _calculate_inverse_weights_grouped()
    4. Run strategy tests with weight-inverse-volatility to verify behavior

    Dampening may be desirable for risk management (less extreme concentration)
    but diverges from Composer parity. Document any reversion clearly.
    ============================================================================

    Args:
        assets: List of asset symbols (bare strings)
        window: Lookback window for volatility calculation (days)
        context: DSL evaluation context

    Returns:
        Dictionary mapping symbols to normalized weights (sum to 1.0)

    """
    inverse_weights: dict[str, Decimal] = {}
    total_inverse = Decimal("0")

    for asset in assets:
        volatility = _get_volatility_for_asset(asset, window, context)
        if volatility is not None:
            vol_decimal = Decimal(str(volatility))
            inverse_vol = Decimal("1") / vol_decimal
            inverse_weights[asset] = inverse_vol
            total_inverse += inverse_vol

    if not inverse_weights or total_inverse < Decimal("1e-10"):
        logger.warning(
            "DSL weight-inverse-volatility: No valid volatilities obtained for any assets"
        )
        return {}

    # Normalize: weight = inverse_vol / total_inverse_vol
    normalized = {
        asset: inv_weight / total_inverse for asset, inv_weight in inverse_weights.items()
    }

    logger.debug(
        "DSL weight-inverse-volatility: Computed pure inverse volatility weights",
        extra={
            "assets": assets,
            "weights": {k: float(v) for k, v in normalized.items()},
        },
    )

    return normalized


def _extract_window(args: list[ASTNode], context: DslContext) -> float:
    """Extract and validate window parameter from arguments.

    Args:
        args: List of AST nodes
        context: DSL evaluation context

    Returns:
        Window parameter as float

    Raises:
        DslEvaluationError: If window is invalid

    """
    if not args:
        raise DslEvaluationError("weight-inverse-volatility requires window and assets")

    window_node = args[0]
    window = context.evaluate_node(window_node, context.correlation_id, context.trace)

    if not isinstance(window, int | float):
        window = context.as_decimal(window)
        window = float(window)

    return float(window)


def weight_inverse_volatility(args: list[ASTNode], context: DslContext) -> PortfolioFragment:
    """Evaluate weight-inverse-volatility - inverse volatility weighting.

    Format: (weight-inverse-volatility window [assets...])

    COMPOSER BEHAVIOR: When children are PortfolioFragments (groups), the groups
    are treated as atomic units. We calculate weighted-average volatility per group,
    then apply inverse-vol weights to the groups. Internal weights are preserved.

    When children are bare symbols, we apply inverse-vol to each symbol individually.
    """
    # Extract and validate window parameter
    window = _extract_window(args, context)

    # Check if we're in grouped mode (all children are PortfolioFragments)
    is_grouped, groups = _collect_groups_from_args(args[1:], context)

    if is_grouped and groups:
        # GROUPED MODE: Apply inverse-vol to groups, preserve internal weights
        logger.info(
            "DSL weight-inverse-volatility: GROUPED MODE with %d groups",
            len(groups),
        )
        normalized_weights = _calculate_inverse_weights_grouped(groups, window, context)

        if not normalized_weights:
            raise DslEvaluationError(
                f"DSL weight-inverse-volatility could not compute valid weights for {len(groups)} groups. "
                "All volatility calculations failed."
            )

        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_inverse_volatility",
            weights=normalized_weights,
        )

    # FLAT MODE: Collect assets and apply inverse-vol to each symbol
    all_assets = _collect_assets_from_args(args[1:], context)

    if not all_assets:
        raise DslEvaluationError(
            "DSL weight-inverse-volatility received no assets. "
            "Strategies must always produce a non-empty allocation."
        )

    # Calculate and normalize inverse volatility weights
    normalized_weights = _calculate_inverse_weights(all_assets, window, context)

    if not normalized_weights:
        raise DslEvaluationError(
            f"DSL weight-inverse-volatility could not compute valid weights for assets: {all_assets}. "
            "All volatility calculations failed."
        )

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_inverse_volatility",
        weights=normalized_weights,
    )


# ---------- Group and asset ----------


def group(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Evaluate group - logical grouping that passes through results unchanged.

    Groups are purely organisational containers in the DSL that provide
    naming/documentation for sub-expressions. They evaluate their body
    expressions sequentially and return the last result unchanged,
    following Clojure's do-block semantics where only the final form's
    value is returned.

    IMPORTANT: Groups do NOT merge or modify weights. They simply pass
    through whatever the body expressions produce. Weight manipulation
    should be done explicitly via weight-equal, weight-specified, etc.
    """
    if len(args) < 2:
        raise DslEvaluationError("group requires at least 2 arguments")

    # Group name is used for debugging/traceability only.
    group_name_val = context.evaluate_node(args[0], context.correlation_id, context.trace)
    group_name = group_name_val if isinstance(group_name_val, str) else str(group_name_val)
    body = args[1:]

    # Evaluate each expression sequentially, return the last result
    last_result: DSLValue = None
    for expr in body:
        last_result = context.evaluate_node(expr, context.correlation_id, context.trace)

    # Pass through the last result unchanged - no weight merging.
    # If the result is a PortfolioFragment, attach the group name to metadata for tracing.
    if last_result is None:
        return PortfolioFragment(fragment_id=str(uuid.uuid4()), source_step="group", weights={})

    # DSL vectors like [(weight-equal ...)] evaluate to [PortfolioFragment].
    # Unwrap single-element lists so the isinstance check below succeeds
    # and group_name metadata is attached for cache-based filter scoring.
    last_result = _unwrap_single_element_list(last_result)

    if isinstance(last_result, PortfolioFragment):
        merged_metadata: dict[str, Any] = {
            **last_result.metadata,
            "group_name": group_name,
        }
        # Store raw AST body in module-level transient store (NOT in metadata)
        # so _fetch_or_backfill_returns can re-evaluate the group for historical
        # dates.  Keeping it out of metadata prevents non-serialisable ASTNode
        # objects from leaking into EventBridge via DecisionEvaluated payloads.
        _AST_BODY_STORE[last_result.fragment_id] = list(body)
        return last_result.model_copy(update={"metadata": merged_metadata})

    return last_result


def asset(args: list[ASTNode], context: DslContext) -> str:
    """Evaluate asset - single asset allocation."""
    if not args:
        raise DslEvaluationError("asset requires at least 1 argument")

    symbol_node = args[0]
    symbol = context.evaluate_node(symbol_node, context.correlation_id, context.trace)

    if not isinstance(symbol, str):
        raise DslEvaluationError(f"Asset symbol must be string, got {type(symbol)}")

    # Return just the symbol string - weight-equal will handle creating the fragment
    return symbol


# ---------- Filter operator ----------


def _unwrap_single_element_list(value: DSLValue) -> DSLValue:
    """Recursively unwrap single-element lists.

    DSL evaluation sometimes produces nested lists like [[PortfolioFragment]]
    when the syntax uses brackets around single expressions. This function
    unwraps those to get the actual value.
    """
    while isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value


def _normalize_portfolio_items(value: list[DSLValue]) -> list[PortfolioFragment]:
    """Normalize a list of portfolio items by unwrapping nested lists.

    Groups may return lists containing single PortfolioFragments. This
    normalizes all items to be direct PortfolioFragments.

    Bare string symbols (from ``(asset ...)`` nodes) are wrapped in a
    single-asset PortfolioFragment so that mixed ``[group, group, asset]``
    vectors are evaluated in portfolio mode rather than silently falling
    back to individual-asset mode.

    Returns empty list if normalization fails.
    """
    normalized: list[PortfolioFragment] = []
    for item in value:
        unwrapped = _unwrap_single_element_list(item)
        if isinstance(unwrapped, PortfolioFragment):
            normalized.append(unwrapped)
        elif isinstance(unwrapped, str) and unwrapped:
            # Bare symbol string from (asset ...) -- wrap in a single-asset
            # PortfolioFragment so the filter can score it alongside groups.
            logger.info(
                "DSL filter: wrapping bare asset '%s' in PortfolioFragment "
                "for mixed group/asset filter evaluation",
                unwrapped,
            )
            normalized.append(
                PortfolioFragment(
                    fragment_id=str(uuid.uuid4()),
                    source_step="asset",
                    weights={unwrapped: Decimal("1")},
                    metadata={"group_name": unwrapped},
                )
            )
        else:
            # Item is not a PortfolioFragment or symbol after unwrapping
            return []
    return normalized


def _is_portfolio_list(value: DSLValue) -> tuple[bool, list[PortfolioFragment]]:
    """Check if the value is a list of PortfolioFragments (groups).

    Returns a tuple of (is_portfolio_list, normalized_fragments).
    Handles nested lists by unwrapping single-element wrappers.
    """
    if not isinstance(value, list):
        return False, []
    if not value:
        return False, []

    normalized = _normalize_portfolio_items(value)
    if normalized:
        return True, normalized
    return False, []


def _try_cache_scoring(
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

    group_id = _derive_group_id(group_name)

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


def _evaluate_group_for_date(
    ast_body: list[ASTNode],
    eval_date: date,
    context: DslContext,
) -> Decimal | None:
    """Evaluate a group AST body for a single historical date.

    Sets ``as_of_date`` on the indicator service, re-evaluates the
    body, extracts weights, and computes the portfolio daily return.
    The caller must save/restore ``as_of_date`` around this call.
    """
    context.indicator_service.as_of_date = eval_date

    last_result: DSLValue = None
    for expr in ast_body:
        last_result = context.evaluate_node(expr, context.correlation_id, context.trace)
    last_result = _unwrap_single_element_list(last_result)

    if isinstance(last_result, PortfolioFragment):
        day_weights = dict(last_result.weights)
    else:
        day_weights = collect_weights_from_value(last_result) if last_result else {}

    if not day_weights:
        return None

    return _compute_daily_return_for_portfolio(
        selections=day_weights,
        record_date=eval_date,
        context=context,
    )


def _collect_in_process_returns(
    ast_body: list[ASTNode],
    trading_days: list[date],
    group_name: str,
    context: DslContext,
) -> list[Decimal]:
    """Collect daily returns by re-evaluating a group body for each trading day."""
    returns: list[Decimal] = []
    for eval_date in trading_days:
        try:
            daily_ret = _evaluate_group_for_date(ast_body, eval_date, context)
            if daily_ret is not None:
                returns.append(daily_ret)
        except Exception:
            logger.debug(
                "In-process scoring: failed to evaluate %s for %s",
                eval_date.isoformat(),
                group_name,
            )
    return returns


def _try_in_process_scoring(
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
    if not ast_body or not context.market_data_service:
        return None

    indicator_svc = context.indicator_service
    if not hasattr(indicator_svc, "as_of_date"):
        return None

    window = _extract_window_from_condition(condition_expr, context)
    canonical_metric = _METRIC_DISPATCH.get(op_name or "") if op_name else None
    if not window or not canonical_metric:
        return None

    group_id = _derive_group_id(group_name)
    if group_id in _BACKFILL_IN_PROGRESS:
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


def _fetch_or_backfill_returns(
    fragment: PortfolioFragment,
    group_id: str,
    group_name: str,
    window: int,
    context: DslContext,
) -> list[Decimal]:
    """Fetch historical returns from cache, triggering backfill on miss."""
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
    return _backfill_group_cache(
        group_id=group_id,
        group_name=group_name,
        ast_body=ast_body,
        window=window,
        context=context,
    )


def _score_portfolio(
    fragment: PortfolioFragment,
    condition_expr: ASTNode,
    context: DslContext,
) -> tuple[float | None, ScoringPath]:
    """Calculate a score for a portfolio fragment and report the scoring path.

    Tries scoring approaches in priority order:
    1. DynamoDB cache-based historical scoring (Composer parity)
    2. In-process historical re-evaluation (no DynamoDB, debug runs)
    3. Per-symbol weighted-average of today's indicator values (fallback)

    Returns:
        Tuple of (score, scoring_path) where scoring_path is one of:
        ``"cache_hit"``, ``"cache_miss_backfill"``,
        ``"in_process_fallback"``, ``"per_symbol_fallback"``,
        ``"cache_unavailable"``.

    Returns ``(None, scoring_path)`` if scoring fails for all symbols.

    KNOWN LIMITATION (2026-01-11):
    -----------------------------
    When a `filter` operator is applied to `group` children (portfolios with
    decision trees), this function scores each group by the metric of TODAY'S
    SELECTED ASSET(s) only. This differs from Composer's behavior.

    Composer's approach:
        For each group in filter:
            For each day in the lookback window (e.g., 10 days for stdev-return):
                Evaluate the group's full decision tree with that day's data
                Record what asset was selected that day
                Get that day's return for that asset
            Compute the metric (e.g., stdev) over those historical returns
            Use that as the group's score

    Our current approach:
        For each group in filter:
            Evaluate with today's data to get selected asset(s)
            Look up that asset's pre-computed metric (e.g., stdev-return)
            Use that as the group's score

    Impact:
        Groups that alternate between volatile and safe assets will have
        different scores. For example, a group that picked SOXL yesterday
        and BIL today would score very differently:
        - Composer: Mixed return stream → moderate stdev
        - Us: Just BIL's stdev → very low

    Affected strategies (filters on groups, not raw assets):
        - beam_chain: (filter (stdev-return 10) (select-top 8) [(group ...)])
        - bento_collection: (filter (stdev-return 20) (select-top 1) [(group ...)])
        - fomo_nomo: (filter (stdev-return 10) (select-top 3) [(group ...)])
        - fomo_nomo_lev: (filter (stdev-return 10) (select-top 3) [(group ...)])
        - ftl_starburst: (filter (moving-average-return 10) ...) + nested filters

    Fix would require:
        1. Historical DSL evaluation - running the full decision tree for each
           day in the lookback window
        2. Point-in-time market data - data as it existed on each historical day
        3. Caching - to avoid Nx evaluation cost per group

    This is essentially embedding a mini-backtest engine inside the filter
    operator, which is a significant architectural change.

    UPDATE 2026-02-06: Group cache infrastructure is now in place.
        - DynamoDB table stores daily group evaluations
        - group_id is derived dynamically via _derive_group_id() (hash-based)
        - When cache data is available, we can use historical selections
          to compute accurate metrics for Composer parity

    UPDATE 2026-02-09: On-demand backfill is now implemented.
        - On cache miss, if the group's AST body is preserved on the
          PortfolioFragment metadata, the engine re-evaluates the group
          for each historical trading day, computes daily returns, and
          writes the results to DynamoDB before scoring
        - This eliminates the need for manual extraction; any named
          group is automatically backfilled on first encounter

    See also: scripts/diagnose_cumret_methods.py for debugging tools.

    """
    weights = fragment.weights
    if not weights:
        return None, "per_symbol_fallback"

    # Determine the metric name from the condition expression
    is_list = condition_expr.is_list() and bool(condition_expr.children)
    op_name = condition_expr.children[0].get_symbol_name() if is_list else None
    has_explicit_symbol_arg = bool(is_list and len(condition_expr.children) >= 3)
    should_invert_for_portfolio = bool(op_name in {"max-drawdown"} and not has_explicit_symbol_arg)

    # ── Bare-asset short-circuit ────────────────────────────────────
    # Single-symbol fragments with no AST body (bare assets wrapped by
    # _normalize_portfolio_items) need no group-level cache scoring.
    # Their historical return stream IS the symbol's return stream.
    group_name = fragment.metadata.get("group_name")
    if _is_bare_asset_fragment(fragment, group_name):
        logger.debug(
            "DSL filter: bare-asset group '%s' -- skipping cache/in-process "
            "scoring (per-symbol metric is already correct)",
            group_name,
            extra={
                "group_name": group_name,
                "source_step": fragment.source_step,
                "correlation_id": context.correlation_id,
            },
        )
        # Fall through directly to per-symbol scoring (no warning needed).
        return _per_symbol_score(
            fragment, condition_expr, context, should_invert=should_invert_for_portfolio
        ), "per_symbol_direct"

    # ── Cache-based scoring ────────────────────────────────────────
    cache_result = _try_cache_scoring(
        fragment,
        condition_expr,
        context,
        group_name=group_name,
        op_name=op_name,
        should_invert=should_invert_for_portfolio,
    )
    if cache_result is not None:
        return cache_result, "cache_hit"

    # ── In-process historical scoring (no DynamoDB) ────────────────
    # When cache is unavailable (e.g. local debug) but we have the AST
    # body, re-evaluate the group for historical dates in-memory.
    if isinstance(group_name, str) and group_name:
        in_process_result = _try_in_process_scoring(
            fragment,
            condition_expr,
            context,
            group_name=group_name,
            op_name=op_name,
            should_invert=should_invert_for_portfolio,
        )
        if in_process_result is not None:
            return in_process_result, "in_process_fallback"

    # ── Fallback: per-symbol weighted-average scoring ──────────────
    # Used when the group has no name, cache is unavailable, or the
    # metric is not a return-based one.
    if group_name and not _is_bare_asset_fragment(fragment, group_name):
        group_id = (
            _derive_group_id(str(group_name))
            if isinstance(group_name, str) and group_name
            else None
        )
        logger.warning(
            "DSL filter: FALLBACK -- scoring group '%s' with today-only "
            "per-symbol weighted-average (NOT DynamoDB-backed historical "
            "returns). Portfolio-level metrics (stdev-return, "
            "moving-average-return, etc.) will reflect only today's "
            "selected asset(s), not the historical composite return stream.",
            group_name,
            extra={
                "group_name": group_name,
                "group_id": group_id,
                "op_name": op_name,
                "correlation_id": context.correlation_id,
            },
        )

    return _per_symbol_score(
        fragment, condition_expr, context, should_invert=should_invert_for_portfolio
    ), "per_symbol_fallback"


def _per_symbol_score(
    fragment: PortfolioFragment,
    condition_expr: ASTNode,
    context: DslContext,
    *,
    should_invert: bool,
) -> float | None:
    """Score a portfolio fragment by weighted-average of per-symbol metrics.

    Evaluates the condition metric for each symbol in the fragment's weights
    and computes a weighted average. This is the correct approach for
    single-symbol fragments and serves as the final fallback for multi-asset
    groups when cache and in-process scoring are unavailable.

    Args:
        fragment: Portfolio fragment to score.
        condition_expr: AST node for the metric expression.
        context: DSL evaluation context.
        should_invert: Whether to negate the metric (e.g. max-drawdown).

    Returns:
        Weighted-average score, or None if scoring fails for all symbols.

    """
    weights = fragment.weights
    total_weight = Decimal("0")
    weighted_sum = Decimal("0")

    for sym, weight in weights.items():
        try:
            metric_expr = create_indicator_with_symbol(condition_expr, sym)
            metric_val = context.evaluate_node(metric_expr, context.correlation_id, context.trace)
            metric_val = (
                float(metric_val)
                if isinstance(metric_val, int | float)
                else float(context.as_decimal(metric_val))
            )
            if should_invert:
                metric_val = -metric_val
            weighted_sum += weight * Decimal(str(metric_val))
            total_weight += weight
        except (ValueError, TypeError, DslEvaluationError) as exc:
            logger.warning(
                "DSL filter: portfolio scoring failed for symbol %s: %s",
                sym,
                exc,
            )

    if total_weight > Decimal("0"):
        return float(weighted_sum / total_weight)
    return None


def _select_portfolios(
    portfolios: list[PortfolioFragment],
    condition_expr: ASTNode,
    order: Literal["top", "bottom"],
    limit: int | None,
    context: DslContext,
) -> PortfolioFragment:
    """Score, sort, and select portfolios as units.

    Treats each PortfolioFragment as a single entity to score, using the
    weighted-average of the condition metric across its holdings.

    order: "top" sorts descending (highest first); "bottom" ascending.
    limit: optional number of portfolios to select.

    Returns the merged weights of all selected portfolios.

    NOTE: See _score_portfolio docstring for known limitation when filtering
    groups with decision trees (Composer parity issue).
    """
    context.portfolio_filter_depth += 1
    try:
        return _select_portfolios_inner(portfolios, condition_expr, order, limit, context)
    finally:
        context.portfolio_filter_depth -= 1


def _select_portfolios_inner(
    portfolios: list[PortfolioFragment],
    condition_expr: ASTNode,
    order: Literal["top", "bottom"],
    limit: int | None,
    context: DslContext,
) -> PortfolioFragment:
    """Inner implementation of portfolio selection (see _select_portfolios)."""
    # Log group details at debug level -- per-group cache vs fallback
    # warnings are now emitted by _score_portfolio itself.
    groups_with_names = [
        p for p in portfolios if p.metadata.get("group_name") and len(p.weights) == 1
    ]
    if groups_with_names:
        group_details = []
        for p in groups_with_names[:10]:
            name = p.metadata.get("group_name")
            symbols = list(p.weights.keys())
            group_details.append({"name": name, "selected_today": symbols})

        logger.debug(
            "DSL filter: filtering %d groups with decision trees. Group details (first 10): %s",
            len(groups_with_names),
            group_details,
            extra={"correlation_id": context.correlation_id},
        )

    # Score each portfolio as a unit
    scored: list[tuple[PortfolioFragment, float, ScoringPath]] = []
    for idx, portfolio in enumerate(portfolios):
        score, scoring_path = _score_portfolio(portfolio, condition_expr, context)
        if score is not None:
            scored.append((portfolio, score, scoring_path))
            logger.debug(
                "DSL filter: portfolio %d scored %.4f via %s with %d symbols",
                idx,
                score,
                scoring_path,
                len(portfolio.weights),
            )

    if not scored:
        logger.warning("DSL filter: no portfolios could be scored")
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )

    # Sort portfolios by score with deterministic tiebreaker
    # Primary: score (descending for top, ascending for bottom)
    # Secondary: first symbol alphabetically for deterministic ordering
    def _portfolio_sort_key(
        item: tuple[PortfolioFragment, float, ScoringPath],
    ) -> tuple[float, str]:
        pf, score, _path = item
        first_sym = sorted(pf.weights.keys())[0] if pf.weights else ""
        return (score, first_sym)

    if order == "top":
        scored.sort(key=lambda x: (-_portfolio_sort_key(x)[0], _portfolio_sort_key(x)[1]))
    else:
        scored.sort(key=lambda x: (_portfolio_sort_key(x)[0], _portfolio_sort_key(x)[1]))

    # Trace ranking/selection for parity debugging (capture full sorted list)
    scored_candidates: list[FilterCandidate] = []
    for rank, (pf, score, scoring_path) in enumerate(scored):
        meta_name = pf.metadata.get("group_name")
        candidate_name = meta_name if isinstance(meta_name, str) else None
        symbols = list(pf.weights.keys())
        scored_candidates.append(
            FilterCandidate(
                candidate_id=pf.fragment_id,
                candidate_type="portfolio",
                candidate_name=candidate_name,
                score=float(score),
                symbol_count=len(symbols),
                symbols_sample=symbols[:10],
                rank=rank,
                scoring_path=scoring_path,
            )
        )

    logger.info(
        "DSL filter: scored %d portfolios, order=%s, limit=%s",
        len(scored),
        order,
        limit,
    )
    for idx, (pf, score, scoring_path) in enumerate(scored[:5]):
        logger.info(
            "DSL filter: portfolio %d: score=%.4f via %s, symbols=%s, symbol_count=%d",
            idx,
            score,
            scoring_path,
            list(pf.weights.keys())[:5],
            len(pf.weights),
        )

    # Log score proximity warning for portfolio mode
    _log_portfolio_score_proximity(scored, limit, context)

    # Select top/bottom N portfolios
    if limit is not None and limit >= 0:
        scored = scored[:limit]
        logger.info("DSL filter: after limit=%d, have %d portfolios", limit, len(scored))

    portfolio_trace: FilterTrace = {
        "mode": "portfolio",
        "order": order,
        "limit": limit,
        "condition": _describe_filter_condition(condition_expr, context),
        "scored_candidates": scored_candidates,
        "selected_candidate_ids": [pf.fragment_id for pf, _score, _path in scored],
        "filter_depth": context.portfolio_filter_depth,
    }
    context.add_filter_trace(portfolio_trace)

    # Merge the selected portfolios with equal weight
    if len(scored) == 1:
        # Single portfolio: return its weights directly
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights=dict(scored[0][0].weights),
        )

    # Multiple portfolios: merge with equal weight per portfolio
    merged: dict[str, Decimal] = {}
    portfolio_weight = Decimal("1") / Decimal(str(len(scored)))

    for portfolio, _score, _path in scored:
        for sym, sym_weight in portfolio.weights.items():
            contribution = portfolio_weight * sym_weight
            merged[sym] = merged.get(sym, Decimal("0")) + contribution

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="filter",
        weights=merged,
    )


def filter_assets(args: list[ASTNode], context: DslContext) -> PortfolioFragment:
    """Filter assets based on condition and optional selection.

    Supports two modes:
    1. Individual assets: scores each symbol, selects top/bottom N symbols
    2. Portfolios (groups): scores each portfolio as a unit using weighted
       average of the condition, selects top/bottom N portfolios

    Returns a PortfolioFragment with the selected holdings.
    """
    if len(args) not in (2, 3):
        raise DslEvaluationError(
            "filter requires 2 or 3 arguments: condition, [selection], portfolio"
        )

    condition_expr = args[0]
    selection_expr = args[1] if len(args) == 3 else None
    portfolio_expr = args[2] if len(args) == 3 else args[1]

    portfolio_val = context.evaluate_node(portfolio_expr, context.correlation_id, context.trace)

    take_top, take_n = parse_selection(selection_expr, context)
    order: Literal["top", "bottom"] = "top" if take_top else "bottom"

    # Debug: log what we received
    logger.info(
        "DSL filter: portfolio_val type=%s, is_list=%s",
        type(portfolio_val).__name__,
        isinstance(portfolio_val, list),
    )
    if isinstance(portfolio_val, list):
        logger.info(
            "DSL filter: list has %d items, types: %s, first item: %s",
            len(portfolio_val),
            [type(item).__name__ for item in portfolio_val[:5]],  # First 5 types
            repr(portfolio_val[0])[:100] if portfolio_val else "N/A",  # First item
        )

    # Check if we're filtering portfolios (groups) or individual assets
    is_portfolio, normalized_portfolios = _is_portfolio_list(portfolio_val)
    if is_portfolio:
        # Portfolio mode: treat each PortfolioFragment as a unit to score/select
        logger.info("DSL filter: PORTFOLIO MODE with %d portfolios", len(normalized_portfolios))
        return _select_portfolios(normalized_portfolios, condition_expr, order, take_n, context)

    logger.info("DSL filter: INDIVIDUAL ASSET MODE")
    # Individual asset mode: extract symbols and filter them
    candidates = collect_assets_from_value(portfolio_val)
    if not candidates:
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )

    return select_symbols(condition_expr, candidates, order, take_n, context)


def register_portfolio_operators(dispatcher: DslDispatcher) -> None:
    """Register all portfolio operators with the dispatcher."""
    dispatcher.register("weight-equal", weight_equal)
    dispatcher.register("weight-specified", weight_specified)
    dispatcher.register("weight-inverse-volatility", weight_inverse_volatility)
    dispatcher.register("group", group)
    dispatcher.register("asset", asset)
    dispatcher.register("filter", filter_assets)
