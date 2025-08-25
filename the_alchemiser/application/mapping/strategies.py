"""Pure mapping functions for strategy signals to display/DTO dictionaries.

This module consolidates strategy signal mapping in a dedicated mapping module and
removes ad-hoc legacy dict shapes from runtime paths. It provides pure mapping
functions from typed signals to DTO-like dictionaries while reusing existing typed
strategy engines, value objects, and shared CLI display helpers.

Allocation Scaling Contract (IMPORTANT):
---------------------------------------
All allocation figures exposed by this module are FRACTIONS (0.0–1.0) representing
portfolio weights. Formatting to human-readable percentages (e.g. 30.0%) is performed
only at the presentation layer (e.g. CLI renderers) using standard percentage
format specifiers ("{value:.1%}").

Backward Compatibility:
-----------------------
Historically, callers sometimes supplied ``allocation_percentage`` already scaled
to 0–100 while the renderer also applied percentage formatting, producing 100x
inflated numbers. To migrate safely:

* New canonical field: ``allocation_weight`` (fraction 0–1)
* Legacy field still emitted: ``allocation_percentage`` (alias, same fractional value)
    – Downstream code expecting the old key continues to work
    – Renderers should prefer ``allocation_weight`` when present

Key Functions:
* ``typed_signals_to_legacy_signals_dict`` – Convert AggregatedSignals to display dict
* ``compute_consolidated_portfolio`` – Build consolidated portfolio (fractions 0–1)
* ``format_strategy_signal_for_display`` – Individual signal formatting (fractional)
* ``handle_portfolio_symbol_alias`` – PORT → NUCLEAR_PORTFOLIO conversion

Design Principles:
* Pure functions with no side effects
* Reuse existing domain value objects (Confidence, StrategySignal, Percentage)
* No duplication of allocation or confidence logic
* Mapping only at boundaries; core flow remains typed
* Thin and declarative mapping layer
"""

from __future__ import annotations

from typing import TypedDict

from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.domain.strategies.typed_strategy_manager import AggregatedSignals
from the_alchemiser.domain.strategies.value_objects.strategy_signal import (
    StrategySignal as TypedStrategySignal,
)


class StrategySignalDisplayDTO(TypedDict):
    """Display-oriented strategy signal dictionary (fractional allocation).

    Fields:
        symbol: Display symbol or portfolio label
        action: BUY | SELL | HOLD (string literal from domain Action)
        confidence: Float in [0,1]
        reasoning: Human-readable explanation
        allocation_weight: Fractional target weight (0–1) of portfolio
        allocation_percentage: Backward-compatible alias (same value as allocation_weight)
    """

    symbol: str
    action: str
    confidence: float
    reasoning: str
    allocation_weight: float
    allocation_percentage: float  # legacy alias (fraction, not 0-100)


def handle_portfolio_symbol_alias(symbol_value: str) -> str:
    """Handle PORT -> NUCLEAR_PORTFOLIO symbol aliasing for display.

    Args:
        symbol_value: The raw symbol value from the signal

    Returns:
        Display-friendly symbol string
    """
    return "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value


def format_strategy_signal_for_display(signal: TypedStrategySignal) -> StrategySignalDisplayDTO:
    """Format a typed strategy signal for legacy display format.

    Args:
        signal: Typed domain strategy signal

    Returns:
        Legacy dict format for display compatibility
    """
    symbol_value = signal.symbol.value
    symbol_str = handle_portfolio_symbol_alias(symbol_value)

    allocation_fraction = float(signal.target_allocation.value)
    return StrategySignalDisplayDTO(
        symbol=symbol_str,
        action=signal.action,
        confidence=float(signal.confidence.value),
        reasoning=signal.reasoning,
        allocation_weight=allocation_fraction,
        allocation_percentage=allocation_fraction,  # legacy alias
    )


def create_empty_signal_dict() -> StrategySignalDisplayDTO:
    """Create a standardized empty signal dict for strategies with no signals.

    Returns:
        Empty signal dict with default values
    """
    return StrategySignalDisplayDTO(
        symbol="N/A",
        action="HOLD",
        confidence=0.0,
        reasoning="No signal produced",
        allocation_weight=0.0,
        allocation_percentage=0.0,
    )


def typed_signals_to_legacy_signals_dict(
    aggregated: AggregatedSignals,
) -> dict[StrategyType, StrategySignalDisplayDTO]:
    """Convert AggregatedSignals to legacy signals dict format.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager

    Returns:
        Legacy signals dict keyed by StrategyType for CLI compatibility
    """
    legacy_signals: dict[StrategyType, StrategySignalDisplayDTO] = {}

    for strategy_type, signals in aggregated.get_signals_by_strategy().items():
        if not signals:
            # Handle empty strategies case
            legacy_signals[strategy_type] = create_empty_signal_dict()
        else:
            # Use first signal as representative (existing behavior)
            legacy_signals[strategy_type] = format_strategy_signal_for_display(signals[0])

    return legacy_signals


def compute_consolidated_portfolio(
    aggregated: AggregatedSignals,
    strategy_allocations: dict[StrategyType, float],
) -> dict[str, float]:
    """Build consolidated portfolio from all strategy signals.

    This function consolidates portfolio allocation computation that was previously
    scattered in StrategyManagerAdapter. It reuses existing allocation logic from
    domain value objects.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager
        strategy_allocations: Portfolio allocation between strategies

    Returns:
        Consolidated portfolio dict mapping symbols to allocation weights
    """
    consolidated_portfolio: dict[str, float] = {}

    # Build consolidated portfolio from all signals
    for strategy_type, signals in aggregated.get_signals_by_strategy().items():
        strategy_allocation = strategy_allocations.get(strategy_type, 0.0)

        for signal in signals:
            if signal.action in ["BUY", "LONG"]:
                symbol_str = signal.symbol.value

                # Use the actual signal allocation for individual symbols
                if symbol_str != "PORT":
                    # Calculate individual allocation as signal proportion * strategy allocation
                    individual_allocation = (
                        float(signal.target_allocation.value) * strategy_allocation
                    )
                    # If symbol already exists, add to allocation (multiple strategies can recommend same symbol)
                    if symbol_str in consolidated_portfolio:
                        consolidated_portfolio[symbol_str] += individual_allocation
                    else:
                        consolidated_portfolio[symbol_str] = individual_allocation

    return consolidated_portfolio


def run_all_strategies_mapping(
    aggregated: AggregatedSignals,
    strategy_allocations: dict[StrategyType, float],
) -> tuple[
    dict[StrategyType, StrategySignalDisplayDTO],
    dict[str, float],
    dict[str, list[StrategyType]],
]:
    """Main mapping function to convert typed signals to legacy format.

    This function replaces the complex logic in StrategyManagerAdapter.run_all_strategies()
    with a pure mapping approach that reuses domain value objects and avoids duplication.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager
        strategy_allocations: Portfolio allocation between strategies

    Returns:
        Tuple containing:
        - Legacy signals dict for CLI compatibility
        - Consolidated portfolio allocation dict
        - Strategy attribution dict (empty for now, preserved for interface compatibility)
    """
    # Convert typed signals to legacy format
    legacy_signals = typed_signals_to_legacy_signals_dict(aggregated)

    # Compute consolidated portfolio allocations
    consolidated_portfolio = compute_consolidated_portfolio(aggregated, strategy_allocations)

    # Strategy attribution placeholder (preserved for interface compatibility)
    strategy_attribution: dict[str, list[StrategyType]] = {}

    return legacy_signals, consolidated_portfolio, strategy_attribution
