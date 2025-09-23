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
from collections.abc import Iterable

from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
from the_alchemiser.shared.dto.indicator_request_dto import PortfolioFragmentDTO

from ..context import DslContext
from ..dispatcher import DslDispatcher
from ..types import DslEvaluationError, DSLValue


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


def weight_specified(
    args: list[ASTNodeDTO], context: DslContext
) -> PortfolioFragmentDTO:
    """Evaluate weight-specified - specified weight allocation.

    Format: (weight-specified weight1 asset1 weight2 asset2 ...)
    """
    if len(args) < 2 or len(args) % 2 != 0:
        raise DslEvaluationError(
            "weight-specified requires pairs of weight and asset arguments"
        )

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
        weight_value = context.evaluate_node(
            weight_node, context.correlation_id, context.trace
        )
        if not isinstance(weight_value, (int, float)):
            weight_value = context.as_decimal(weight_value)
            weight_value = float(weight_value)

        weight = float(weight_value)

        # Evaluate asset (should be a symbol or asset result)
        asset_result = context.evaluate_node(
            asset_node, context.correlation_id, context.trace
        )

        normalized = collect_normalized_weights(asset_result)
        if not normalized:
            raise DslEvaluationError(
                f"Expected asset symbol or fragment, got {type(asset_result)}"
            )
        for symbol, base_w in normalized.items():
            scaled = base_w * weight
            weights[symbol] = weights.get(symbol, 0.0) + scaled

    return PortfolioFragmentDTO(
        fragment_id=str(uuid.uuid4()),
        source_step="weight_specified",
        weights=weights,
    )


def weight_inverse_volatility(
    args: list[ASTNodeDTO], context: DslContext
) -> PortfolioFragmentDTO:
    """Evaluate weight-inverse-volatility - inverse volatility weighting.

    Format: (weight-inverse-volatility window [assets...])
    """
    if not args:
        raise DslEvaluationError("weight-inverse-volatility requires window and assets")

    # First argument is the window
    window_node = args[0]
    window = context.evaluate_node(window_node, context.correlation_id, context.trace)

    if not isinstance(window, (int, float)):
        window = context.as_decimal(window)
        window = float(window)

    # Collect assets from remaining arguments
    all_assets: list[str] = []
    for arg in args[1:]:
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

    if not all_assets:
        return PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()),
            source_step="weight_inverse_volatility",
            weights={},
        )

    # Calculate inverse volatility weights
    # For now, use mock volatilities - in real implementation would calculate from price history
    mock_volatilities = {
        "UVXY": 0.8,  # High volatility
        "BTAL": 0.2,  # Low volatility
        "TLT": 0.15,
        "QQQ": 0.25,
        "SPY": 0.20,
        "TQQQ": 0.6,
        "SQQQ": 0.6,
    }

    # Calculate inverse weights
    inverse_weights = {}
    total_inverse = 0.0

    for asset in all_assets:
        volatility = mock_volatilities.get(asset, 0.25)  # Default volatility
        inverse_vol = 1.0 / volatility
        inverse_weights[asset] = inverse_vol
        total_inverse += inverse_vol

    # Normalize to sum to 1
    normalized_weights = {}
    for asset, inv_weight in inverse_weights.items():
        normalized_weights[asset] = inv_weight / total_inverse

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
        else PortfolioFragmentDTO(
            fragment_id=str(uuid.uuid4()), source_step="group", weights={}
        )
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
    """
    if len(args) not in (2, 3):
        raise DslEvaluationError(
            "filter requires 2 or 3 arguments: condition, [selection], portfolio"
        )

    _condition_expr = args[0]
    _selection_expr = args[1] if len(args) == 3 else None
    portfolio_expr = args[2] if len(args) == 3 else args[1]

    # Placeholder implementation: return the portfolio as-is until per-asset
    # condition evaluation and selection ranking is implemented.
    return context.evaluate_node(portfolio_expr, context.correlation_id, context.trace)


def register_portfolio_operators(dispatcher: DslDispatcher) -> None:
    """Register all portfolio operators with the dispatcher."""
    dispatcher.register("weight-equal", weight_equal)
    dispatcher.register("weight-specified", weight_specified)
    dispatcher.register("weight-inverse-volatility", weight_inverse_volatility)
    dispatcher.register("group", group)
    dispatcher.register("asset", asset)
    dispatcher.register("filter", filter_assets)
