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
from typing import Literal

from engines.dsl.context import DslContext, FilterCandidate, FilterTrace
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
    full_sorted = list(scored)
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
    """Calculate inverse volatility weights for groups (Composer behavior).

    COMPOSER BEHAVIOR: Each group is treated as a single unit. We calculate
    the weighted-average volatility for each group, then apply inverse-vol
    weights to the groups themselves. Internal weights within each group
    are preserved and scaled by the group's share.

    Args:
        groups: List of PortfolioFragment groups
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Dictionary of normalized weights (as Decimal)

    """
    DAMPENING_EXPONENT = Decimal("0.25")

    # Calculate inverse volatility weight for each group
    group_weights: list[tuple[PortfolioFragment, Decimal]] = []
    total_inverse = Decimal("0")

    for group in groups:
        group_vol = _calculate_group_volatility(group, window, context)
        if group_vol is not None and group_vol > 0:
            vol_decimal = Decimal(str(group_vol))
            inverse_vol = Decimal("1") / vol_decimal
            dampened_inverse = inverse_vol**DAMPENING_EXPONENT
            group_weights.append((group, dampened_inverse))
            total_inverse += dampened_inverse
            logger.debug(
                "DSL weight-inverse-volatility grouped: group vol=%.6f, dampened_inverse=%.6f",
                group_vol,
                float(dampened_inverse),
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
    # Dampening exponent for "soft" inverse volatility:
    # - 1.0  → true inverse volatility (very concentrated in low-vol assets)
    # - 0.0  → equal weight (no volatility sensitivity)
    # - 0.25 → empirically calibrated fourth-root dampening that best matches
    #           Composer.trade's observed behavior across a regression suite of
    #           representative portfolios. Exponents around 0.2 skewed too close
    #           to equal-weight, while 0.3+ produced weights that were
    #           measurably more concentrated than Composer's outputs. 0.25 was
    #           chosen as the smallest exponent that consistently kept the
    #           volatility ranking intact while minimizing mean absolute error to
    #           Composer's weights.
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
            dampened_inverse = inverse_vol**DAMPENING_EXPONENT

            inverse_weights[asset] = dampened_inverse
            total_inverse += dampened_inverse

    # Handle case where no valid volatilities were obtained
    if not inverse_weights or total_inverse < Decimal("1e-10"):
        logger.warning(
            "DSL weight-inverse-volatility: No valid volatilities obtained for any assets"
        )
        return {}

    # Normalize weights to sum to 1 using Decimal division
    normalized = {
        asset: inv_weight / total_inverse for asset, inv_weight in inverse_weights.items()
    }

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

    if isinstance(last_result, PortfolioFragment):
        merged_metadata = {**last_result.metadata, "group_name": group_name}
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

    See also: scripts/diagnose_cumret_methods.py for debugging tools.
    """
    weights = fragment.weights
    if not weights:
        return None

    # Composer parity: max-drawdown is a "lower is better" metric, but Composer
    # uses select-top to mean "pick the best" (i.e., lowest drawdown).
    # We negate max-drawdown scores so select-top picks the portfolio with the
    # LOWEST drawdown (safest). This only applies when the DSL form does not
    # include an explicit symbol argument.
    # NOTE: stdev-return and stdev-price are NOT inverted - select-top with
    # volatility metrics picks the HIGHEST volatility, which is valid for some
    # strategies (e.g., beam_chain uses stdev-return to pick most volatile portfolios).
    is_list = condition_expr.is_list() and bool(condition_expr.children)
    op_name = condition_expr.children[0].get_symbol_name() if is_list else None
    has_explicit_symbol_arg = bool(is_list and len(condition_expr.children) >= 3)
    should_invert_for_portfolio = bool(op_name in {"max-drawdown"} and not has_explicit_symbol_arg)

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
            if should_invert_for_portfolio:
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
    # Warn about known Composer parity limitation when filtering groups
    groups_with_names = [
        p for p in portfolios if p.metadata.get("group_name") and len(p.weights) == 1
    ]
    if groups_with_names:
        logger.warning(
            "DSL filter: filtering %d groups with decision trees. "
            "KNOWN LIMITATION: scoring uses today's selected asset only, "
            "not historical return stream. May diverge from Composer. "
            "Affected groups: %s",
            len(groups_with_names),
            [p.metadata.get("group_name") for p in groups_with_names[:5]],
        )

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
    # "top" = sort descending (highest first), "bottom" = sort ascending (lowest first)
    scored.sort(key=lambda x: x[1], reverse=(order == "top"))

    # Trace ranking/selection for parity debugging (capture full sorted list)
    scored_candidates: list[FilterCandidate] = []
    for rank, (pf, score) in enumerate(scored):
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
            )
        )

    logger.info(
        "DSL filter: scored %d portfolios, order=%s, limit=%s",
        len(scored),
        order,
        limit,
    )
    for idx, (pf, score) in enumerate(scored[:5]):
        logger.info(
            "DSL filter: portfolio %d: score=%.4f, symbols=%s, symbol_count=%d",
            idx,
            score,
            list(pf.weights.keys())[:5],
            len(pf.weights),
        )

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
        "selected_candidate_ids": [pf.fragment_id for pf, _score in scored],
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
