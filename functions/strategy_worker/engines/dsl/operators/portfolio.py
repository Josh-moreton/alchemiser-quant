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

import uuid
from decimal import Decimal
from typing import Literal, cast

from engines.dsl.context import DslContext
from engines.dsl.dispatcher import DslDispatcher
from engines.dsl.operators.control_flow import create_indicator_with_symbol
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


# ---------- Shared helpers ----------


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
    scored.sort(key=lambda x: x[1], reverse=(order == "top"))
    if limit is not None and limit >= 0:
        scored = scored[:limit]

    # Create equal-weighted fragment for selected symbols
    selected_symbols = [sym for sym, _ in scored]
    if not selected_symbols:
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )

    weight_per_asset = Decimal("1") / Decimal(str(len(selected_symbols)))
    weights = {sym: weight_per_asset for sym in selected_symbols}

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="filter",
        weights=weights,
    )


def _normalize_fragment_weights(value: DSLValue, context: DslContext) -> dict[str, Decimal]:
    """Convert a DSLValue into a normalized weights dict using Decimal arithmetic.

    - str → {symbol: Decimal("1.0")}
    - PortfolioFragment → normalized weights (already Decimal)
    - list → merge recursively, then normalize to sum to 1 if total > 0
    """
    if isinstance(value, str):
        return {value: Decimal("1.0")}
    if isinstance(value, PortfolioFragment):
        frag = value.normalize_weights()
        return dict(frag.weights)  # Already Decimal after Phase 1
    if isinstance(value, list):
        collected: dict[str, Decimal] = {}
        for item in value:
            nested = _normalize_fragment_weights(item, context)
            for sym, w in nested.items():
                collected[sym] = collected.get(sym, Decimal("0")) + w
        total = sum(collected.values()) if collected else Decimal("0")
        if total > Decimal("0"):
            return {sym: w / total for sym, w in collected.items()}
        return collected
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

    When weight-equal receives a single argument that evaluates to a list,
    each item in that list should be treated as a separate child for
    equal weighting purposes. This function handles the flattening.

    For a PortfolioFragment or string, returns a single-item list.
    For a list, returns each item as a separate normalized weight dict.
    """
    if isinstance(value, PortfolioFragment):
        frag = value.normalize_weights()
        return [dict(frag.weights)]
    if isinstance(value, str):
        return [{value: Decimal("1.0")}]
    if isinstance(value, list):
        result: list[dict[str, Decimal]] = []
        for item in value:
            # Recursively flatten nested lists
            result.extend(_flatten_to_weight_dicts(item))
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
    """Collect assets from DSL arguments.

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
    """Calculate and normalize inverse volatility weights using Decimal arithmetic.

    IMPORTANT: Composer.trade's inverse volatility implementation produces weights
    much closer to equal-weight than true mathematical inverse volatility would give.
    For example, with BIL (0.01% vol), DRV (1.6% vol), LABU (4.3% vol):
    - True inverse volatility: BIL ~99%, DRV ~0.8%, LABU ~0.3%
    - Composer produces:       BIL ~65%, DRV ~20%, LABU ~15%

    To match Composer's actual behavior, we apply a fourth-root dampening transformation:
    weight ∝ (1/volatility)^0.25

    This:
    - Still favors lower volatility assets (inverse relationship preserved)
    - Prevents extreme weight concentration that true 1/vol would cause
    - Matches Composer's observed outputs very closely
    - Is essentially a "soft" inverse volatility that respects the ranking
      but doesn't let extreme volatility differences dominate

    Args:
        assets: List of asset symbols
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Dictionary of normalized weights (as Decimal)

    """
    # Dampening exponent: 0.25 (fourth root) matches Composer's apparent behavior
    # True inverse volatility would use 1.0, equal weight would use 0.0
    DAMPENING_EXPONENT = Decimal("0.25")

    inverse_weights: dict[str, Decimal] = {}
    total_inverse = Decimal("0")

    # Calculate dampened inverse volatility weights
    for asset in assets:
        volatility = _get_volatility_for_asset(asset, window, context)
        if volatility is not None:
            # Convert float volatility to Decimal
            vol_decimal = Decimal(str(volatility))
            inverse_vol = Decimal("1") / vol_decimal

            # Apply fourth-root dampening: (1/vol)^0.25
            # This prevents extreme concentration while preserving volatility ranking
            # Matches Composer's observed implementation
            dampened_inverse = inverse_vol ** DAMPENING_EXPONENT

            inverse_weights[asset] = dampened_inverse
            total_inverse += dampened_inverse

    # Handle case where no valid volatilities were obtained
    if not inverse_weights or total_inverse < Decimal("1e-10"):
        logger.warning(
            "DSL weight-inverse-volatility: No valid volatilities obtained for any assets"
        )
        return {}

    # Normalize weights to sum to 1 using Decimal division
    normalized = {asset: inv_weight / total_inverse for asset, inv_weight in inverse_weights.items()}

    # Log the dampening effect for transparency
    logger.debug(
        "DSL weight-inverse-volatility: Applied fourth-root dampening to match Composer behavior",
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
    """
    # Extract and validate window parameter
    window = _extract_window(args, context)

    # Collect assets from remaining arguments
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

    _name = args[0]  # Group name (unused in evaluation, for documentation only)
    body = args[1:]

    # Evaluate each expression sequentially, return the last result
    last_result: DSLValue = None
    for expr in body:
        last_result = context.evaluate_node(expr, context.correlation_id, context.trace)

    # Pass through the last result unchanged - no weight merging
    return (
        last_result
        if last_result is not None
        else PortfolioFragment(fragment_id=str(uuid.uuid4()), source_step="group", weights={})
    )


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


def _normalize_portfolio_items(value: list) -> list[PortfolioFragment]:
    """Normalize a list of portfolio items by unwrapping nested lists.

    Groups may return lists containing single PortfolioFragments. This
    normalizes all items to be direct PortfolioFragments.

    Returns empty list if normalization fails.
    """
    normalized: list[PortfolioFragment] = []
    for item in value:
        unwrapped = _unwrap_single_element_list(item)
        if isinstance(unwrapped, PortfolioFragment):
            normalized.append(unwrapped)
        else:
            # Item is not a PortfolioFragment after unwrapping - not a portfolio list
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


def _score_portfolio(
    fragment: PortfolioFragment,
    condition_expr: ASTNode,
    context: DslContext,
) -> float | None:
    """Calculate a weighted-average score for a portfolio fragment.

    For each symbol in the portfolio, evaluates the condition and computes
    the portfolio-level metric as a weighted average of individual scores.

    Returns None if scoring fails for all symbols.
    """
    weights = fragment.weights
    if not weights:
        return None

    # Score each symbol and compute weighted average
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
    """
    # Score each portfolio as a unit
    scored: list[tuple[PortfolioFragment, float]] = []
    for idx, portfolio in enumerate(portfolios):
        score = _score_portfolio(portfolio, condition_expr, context)
        if score is not None:
            scored.append((portfolio, score))
            logger.debug(
                "DSL filter: portfolio %d scored %.4f with %d symbols",
                idx,
                score,
                len(portfolio.weights),
            )

    if not scored:
        logger.warning("DSL filter: no portfolios could be scored")
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="filter",
            weights={},
        )

    # Sort portfolios by score
    scored.sort(key=lambda x: x[1], reverse=(order == "top"))

    logger.info(
        "DSL filter: scored %d portfolios, order=%s, limit=%s",
        len(scored),
        order,
        limit,
    )
    for idx, (pf, score) in enumerate(scored[:5]):
        logger.info(
            "DSL filter: portfolio %d: score=%.4f, symbols=%s",
            idx,
            score,
            list(pf.weights.keys())[:3],
        )

    # Select top/bottom N portfolios
    if limit is not None and limit >= 0:
        scored = scored[:limit]
        logger.info("DSL filter: after limit=%d, have %d portfolios", limit, len(scored))

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

    for portfolio, _score in scored:
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
        logger.info(
            "DSL filter: PORTFOLIO MODE with %d portfolios", len(normalized_portfolios)
        )
        return _select_portfolios(
            normalized_portfolios, condition_expr, order, take_n, context
        )

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
