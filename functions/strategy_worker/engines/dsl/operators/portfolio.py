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
) -> list[DSLValue]:
    """Score, sort, and select symbols based on selection parameters.

    order: "top" sorts descending (highest first); "bottom" ascending.
    limit: optional number of items to return.
    """
    scored = score_candidates(symbols, condition_expr, context)
    if not scored:
        return []
    scored.sort(key=lambda x: x[1], reverse=(order == "top"))
    if limit is not None and limit >= 0:
        scored = scored[:limit]
    return cast(list[DSLValue], [sym for sym, _ in scored])


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


# ---------- Operators ----------


def weight_equal(args: list[ASTNode], context: DslContext) -> PortfolioFragment:
    """Evaluate weight-equal - allocate equal weight to all assets using Decimal arithmetic."""
    if not args:
        raise DslEvaluationError(
            "weight-equal requires at least one asset argument. "
            "DSL strategies must always produce a non-empty allocation."
        )

    # Collect all assets from all arguments
    all_assets: list[str] = []
    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)
        all_assets.extend(collect_assets_from_value(result))

    if not all_assets:
        raise DslEvaluationError(
            "DSL weight-equal received no assets after evaluation. "
            "Strategies must always produce a non-empty allocation."
        )

    # Deduplicate while preserving order
    unique_assets: list[str] = []
    seen: set[str] = set()
    for asset in all_assets:
        if asset not in seen:
            unique_assets.append(asset)
            seen.add(asset)

    # Use Decimal division instead of float division (CRITICAL FIX)
    weight_per_asset = Decimal("1") / Decimal(str(len(unique_assets)))
    weights = dict.fromkeys(unique_assets, weight_per_asset)

    return PortfolioFragment(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_equal",
        weights=weights,
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

    Args:
        assets: List of asset symbols
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Dictionary of normalized weights (as Decimal)

    """
    inverse_weights: dict[str, Decimal] = {}
    total_inverse = Decimal("0")

    # Calculate inverse volatility weights
    for asset in assets:
        volatility = _get_volatility_for_asset(asset, window, context)
        if volatility is not None:
            # Convert float volatility to Decimal before division
            vol_decimal = Decimal(str(volatility))
            inverse_vol = Decimal("1") / vol_decimal
            inverse_weights[asset] = inverse_vol
            total_inverse += inverse_vol

    # Handle case where no valid volatilities were obtained
    if not inverse_weights or total_inverse < Decimal("1e-10"):
        logger.warning(
            "DSL weight-inverse-volatility: No valid volatilities obtained for any assets"
        )
        return {}

    # Normalize weights to sum to 1 using Decimal division
    return {asset: inv_weight / total_inverse for asset, inv_weight in inverse_weights.items()}


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
    """Evaluate group - aggregate results from body expressions using Decimal arithmetic.

    Groups act as composition blocks in the DSL. We evaluate each body
    expression and combine any resulting portfolio fragments by summing
    weights. If no weights are produced by the body, we fall back to the
    result of the last expression to preserve compatibility.
    """
    if len(args) < 2:
        raise DslEvaluationError("group requires at least 2 arguments")

    _name = args[0]  # Group name (unused in evaluation)
    body = args[1:]

    combined: dict[str, Decimal] = {}
    last_result: DSLValue = None

    def _merge_weights_from(value: DSLValue) -> None:
        if isinstance(value, PortfolioFragment):
            for sym, w in value.weights.items():
                combined[sym] = combined.get(sym, Decimal("0")) + w
        elif isinstance(value, list):
            for item in value:
                _merge_weights_from(item)
        elif isinstance(value, str):
            combined[value] = combined.get(value, Decimal("0")) + Decimal("1.0")

    # Evaluate each expression and merge any weights found
    for expr in body:
        res = context.evaluate_node(expr, context.correlation_id, context.trace)
        last_result = res
        _merge_weights_from(res)

    # If we gathered any weights, return as a fragment; else, return last result
    if combined:
        return PortfolioFragment(
            fragment_id=str(uuid.uuid4()),
            source_step="group",
            weights=combined,
        )

    # No combined weights produced: if single body item, return its result; otherwise last
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


def filter_assets(args: list[ASTNode], context: DslContext) -> DSLValue:
    """Filter assets based on condition and optional selection."""
    if len(args) not in (2, 3):
        raise DslEvaluationError(
            "filter requires 2 or 3 arguments: condition, [selection], portfolio"
        )

    condition_expr = args[0]
    selection_expr = args[1] if len(args) == 3 else None
    portfolio_expr = args[2] if len(args) == 3 else args[1]

    portfolio_val = context.evaluate_node(portfolio_expr, context.correlation_id, context.trace)
    candidates = collect_assets_from_value(portfolio_val)
    if not candidates:
        return []

    take_top, take_n = parse_selection(selection_expr, context)
    order: Literal["top", "bottom"] = "top" if take_top else "bottom"
    return select_symbols(condition_expr, candidates, order, take_n, context)


def register_portfolio_operators(dispatcher: DslDispatcher) -> None:
    """Register all portfolio operators with the dispatcher."""
    dispatcher.register("weight-equal", weight_equal)
    dispatcher.register("weight-specified", weight_specified)
    dispatcher.register("weight-inverse-volatility", weight_inverse_volatility)
    dispatcher.register("group", group)
    dispatcher.register("asset", asset)
    dispatcher.register("filter", filter_assets)
