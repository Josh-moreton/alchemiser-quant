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

import logging
import uuid
from collections.abc import Iterable

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import (
    IndicatorRequestDTO,
    PortfolioFragmentDTO,
)

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DslEvaluationError, DSLValue
from .control_flow import create_indicator_with_symbol

logger = logging.getLogger(__name__)


def weight_equal(args: list[ASTNodeDTO], context: DslContext) -> PortfolioFragmentDTO:
    """Evaluate weight-equal - equal weight allocation."""
    if not args:
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()), source_step="weight_equal", weights={}
        )

    # Collect all assets from arguments
    all_assets: list[str] = []

    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)

        if isinstance(result, PortfolioFragmentDTO):
            # Add all assets from this fragment
            for symbol in result.weights:
                all_assets.append(symbol)
        elif isinstance(result, list):
            # Handle list of results - recursively process nested lists
            def process_list_items(items: Iterable[DSLValue]) -> list[str]:
                assets: list[str] = []
                for item in items:
                    if isinstance(item, PortfolioFragmentDTO):
                        assets.extend(item.weights.keys())
                    elif isinstance(item, str):
                        assets.append(item)
                    elif isinstance(item, list):
                        # Recursively process nested lists
                        assets.extend(process_list_items(item))
                return assets

            nested_assets = process_list_items(result)
            all_assets.extend(nested_assets)
        elif isinstance(result, str):
            # Direct symbol string
            all_assets.append(result)

    # Create equal weights for all collected assets
    if not all_assets:
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()), source_step="weight_equal", weights={}
        )

    # Remove duplicates while preserving order
    unique_assets: list[str] = []
    seen: set[str] = set()
    for asset in all_assets:
        if asset not in seen:
            unique_assets.append(asset)
            seen.add(asset)

    weight_per_asset = 1.0 / len(unique_assets)
    weights = dict.fromkeys(unique_assets, weight_per_asset)

    return PortfolioFragmentDTO(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_equal",
        weights=weights,
    )


def weight_specified(args: list[ASTNodeDTO], context: DslContext) -> PortfolioFragmentDTO:
    """Evaluate weight-specified - specified weight allocation.

    Format: (weight-specified weight1 asset1 weight2 asset2 ...)
    """
    if len(args) < 2 or len(args) % 2 != 0:
        raise DslEvaluationError("weight-specified requires pairs of weight and asset arguments")

    weights: dict[str, float] = {}

    def collect_normalized_weights(value: DSLValue) -> dict[str, float]:
        collected: dict[str, float] = {}
        if isinstance(value, str):
            collected[value] = 1.0
            return collected
        if isinstance(value, PortfolioFragmentDTO):
            frag = value.normalize_weights()
            return dict(frag.weights)
        if isinstance(value, list):
            for item in value:
                nested = collect_normalized_weights(item)
                for sym, w in nested.items():
                    collected[sym] = collected.get(sym, 0.0) + w
            total = sum(collected.values())
            if total > 0:
                collected = {sym: w / total for sym, w in collected.items()}
            return collected
        return collected

    # Process weight-asset pairs
    for i in range(0, len(args), 2):
        weight_node = args[i]
        asset_node = args[i + 1]

        # Evaluate weight (should be a number)
        weight_value = context.evaluate_node(weight_node, context.correlation_id, context.trace)
        if not isinstance(weight_value, (int, float)):
            weight_value = context.as_decimal(weight_value)
            weight_value = float(weight_value)

        weight = float(weight_value)

        # Evaluate asset (should be a symbol or asset result)
        asset_result = context.evaluate_node(asset_node, context.correlation_id, context.trace)

        normalized = collect_normalized_weights(asset_result)
        if not normalized:
            raise DslEvaluationError(f"Expected asset symbol or fragment, got {type(asset_result)}")
        for symbol, base_w in normalized.items():
            scaled = base_w * weight
            weights[symbol] = weights.get(symbol, 0.0) + scaled

    return PortfolioFragmentDTO(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_specified",
        weights=weights,
    )


def _extract_window(args: list[ASTNodeDTO], context: DslContext) -> float:
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

    if not isinstance(window, (int, float)):
        window = context.as_decimal(window)
        window = float(window)

    return float(window)


def _collect_assets_from_args(args: list[ASTNodeDTO], context: DslContext) -> list[str]:
    """Collect assets from DSL arguments.

    Args:
        args: List of AST nodes (excluding window parameter)
        context: DSL evaluation context

    Returns:
        List of asset symbols

    """
    all_assets: list[str] = []

    for arg in args:
        result = context.evaluate_node(arg, context.correlation_id, context.trace)

        if isinstance(result, PortfolioFragmentDTO):
            all_assets.extend(result.weights.keys())
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, PortfolioFragmentDTO):
                    all_assets.extend(item.weights.keys())
                elif isinstance(item, str):
                    all_assets.append(item)
        elif isinstance(result, str):
            all_assets.append(result)

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
        request = IndicatorRequestDTO(
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
        if int(window) == 6 and indicator.stdev_return_6 is not None:
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

    except Exception as exc:
        logger.warning(
            "DSL weight-inverse-volatility: Failed to get volatility for %s: %s",
            asset,
            exc,
        )
        return None


def _calculate_inverse_weights(
    assets: list[str], window: float, context: DslContext
) -> dict[str, float]:
    """Calculate and normalize inverse volatility weights.

    Args:
        assets: List of asset symbols
        window: Window parameter for volatility calculation
        context: DSL evaluation context

    Returns:
        Dictionary of normalized weights

    """
    inverse_weights = {}
    total_inverse = 0.0

    # Calculate inverse volatility weights
    for asset in assets:
        volatility = _get_volatility_for_asset(asset, window, context)
        if volatility is not None:
            inverse_vol = 1.0 / volatility
            inverse_weights[asset] = inverse_vol
            total_inverse += inverse_vol

    # Handle case where no valid volatilities were obtained
    if not inverse_weights or total_inverse <= 0:
        logger.warning(
            "DSL weight-inverse-volatility: No valid volatilities obtained for any assets"
        )
        return {}

    # Normalize weights to sum to 1
    return {asset: inv_weight / total_inverse for asset, inv_weight in inverse_weights.items()}


def weight_inverse_volatility(args: list[ASTNodeDTO], context: DslContext) -> PortfolioFragmentDTO:
    """Evaluate weight-inverse-volatility - inverse volatility weighting.

    Format: (weight-inverse-volatility window [assets...])
    """
    # Extract and validate window parameter
    window = _extract_window(args, context)

    # Collect assets from remaining arguments
    all_assets = _collect_assets_from_args(args[1:], context)

    if not all_assets:
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_inverse_volatility",
            weights={},
        )

    # Calculate and normalize inverse volatility weights
    normalized_weights = _calculate_inverse_weights(all_assets, window, context)

    return PortfolioFragmentDTO(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_inverse_volatility",
        weights=normalized_weights,
    )


def group(args: list[ASTNodeDTO], context: DslContext) -> DSLValue:
    """Evaluate group - aggregate results from body expressions.

    Groups act as composition blocks in the DSL. We evaluate each body
    expression and combine any resulting portfolio fragments by summing
    weights. If no weights are produced by the body, we fall back to the
    result of the last expression to preserve compatibility.
    """
    if len(args) < 2:
        raise DslEvaluationError("group requires at least 2 arguments")

    _name = args[0]  # Group name (unused in evaluation)
    body = args[1:]

    combined: dict[str, float] = {}
    last_result: DSLValue = None

    def _merge_weights_from(value: DSLValue) -> None:
        if isinstance(value, PortfolioFragmentDTO):
            for sym, w in value.weights.items():
                combined[sym] = combined.get(sym, 0.0) + float(w)
        elif isinstance(value, list):
            for item in value:
                _merge_weights_from(item)
        elif isinstance(value, str):
            combined[value] = combined.get(value, 0.0) + 1.0

    # Evaluate each expression and merge any weights found
    for expr in body:
        res = context.evaluate_node(expr, context.correlation_id, context.trace)
        last_result = res
        _merge_weights_from(res)

    # If we gathered any weights, return as a fragment; else, return last result
    if combined:
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="group",
            weights=combined,
        )

    # No combined weights produced: if single body item, return its result; otherwise last
    return (
        last_result
        if last_result is not None
        else PortfolioFragmentDTO(fragment_id=str(uuid.uuid4()), source_step="group", weights={})
    )


def asset(args: list[ASTNodeDTO], context: DslContext) -> str:
    """Evaluate asset - single asset allocation."""
    if not args:
        raise DslEvaluationError("asset requires at least 1 argument")

    symbol_node = args[0]
    symbol = context.evaluate_node(symbol_node, context.correlation_id, context.trace)

    if not isinstance(symbol, str):
        raise DslEvaluationError(f"Asset symbol must be string, got {type(symbol)}")

    # Return just the symbol string - weight-equal will handle creating the fragment
    return symbol


def filter_assets(args: list[ASTNodeDTO], context: DslContext) -> DSLValue:
    """Evaluate filter - filter assets based on condition.

    Supported forms:
    - (filter condition_expr portfolio_expr)
    - (filter condition_expr selection_expr portfolio_expr)

    Where selection_expr can be a selector like (select-top N) or (select-bottom N).
    Returns a list of selected asset symbols.
    """
    if len(args) not in (2, 3):
        raise DslEvaluationError(
            "filter requires 2 or 3 arguments: condition, [selection], portfolio"
        )

    condition_expr = args[0]
    selection_expr = args[1] if len(args) == 3 else None
    portfolio_expr = args[2] if len(args) == 3 else args[1]

    # Evaluate the portfolio expression and collect candidate symbols
    portfolio_val = context.evaluate_node(portfolio_expr, context.correlation_id, context.trace)

    def collect_assets(value: DSLValue) -> list[str]:
        symbols: list[str] = []
        if isinstance(value, PortfolioFragmentDTO):
            symbols.extend(list(value.weights.keys()))
        elif isinstance(value, str):
            symbols.append(value)
        elif isinstance(value, list):
            for item in value:
                symbols.extend(collect_assets(item))
        return symbols

    candidates = collect_assets(portfolio_val)
    if not candidates:
        return []

    # Determine selection parameters
    take_top = True
    take_n: int | None = None

    if selection_expr is not None:
        # Determine direction from the selection node symbol if available
        sel_node = selection_expr
        sel_name = (
            sel_node.children[0].get_symbol_name()
            if sel_node.is_list() and sel_node.children
            else None
        )
        if sel_name == "select-bottom":
            take_top = False
        # Evaluate to get N
        n_val = context.evaluate_node(selection_expr, context.correlation_id, context.trace)
        if isinstance(n_val, (int, float)):
            take_n = int(n_val)
        else:
            # Coerce via Decimal helper if needed
            try:
                take_n = int(context.as_decimal(n_val))
            except Exception:
                take_n = None

    # Score each candidate using the condition expression applied to the symbol
    scored: list[tuple[str, float]] = []
    for sym in candidates:
        try:
            metric_expr = create_indicator_with_symbol(condition_expr, sym)
            metric_val = context.evaluate_node(metric_expr, context.correlation_id, context.trace)
            if not isinstance(metric_val, (int, float)):
                metric_val = float(context.as_decimal(metric_val))
            scored.append((sym, float(metric_val)))
        except Exception:
            # Log and skip symbols that fail metric evaluation
            logger.exception("DSL filter: condition evaluation failed for symbol %s", sym)
            continue

    if not scored:
        return []

    # Sort based on selection direction
    scored.sort(key=lambda x: x[1], reverse=take_top)

    # Apply N if provided
    if take_n is not None and take_n >= 0:
        scored = scored[:take_n]

    # Return only symbols
    return [sym for sym, _ in scored]


def register_portfolio_operators(dispatcher: DslDispatcher) -> None:
    """Register all portfolio operators with the dispatcher."""
    dispatcher.register("weight-equal", weight_equal)
    dispatcher.register("weight-specified", weight_specified)
    dispatcher.register("weight-inverse-volatility", weight_inverse_volatility)
    dispatcher.register("group", group)
    dispatcher.register("asset", asset)
    dispatcher.register("filter", filter_assets)
