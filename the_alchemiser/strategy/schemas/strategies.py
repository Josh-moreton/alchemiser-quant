"""Business Unit: strategy | Status: current..

    Args:
        symbol_value: The raw symbol value from the signal

    Returns:
        Display-friendly symbol string

    """
    return "NUCLEAR_PORTFOLIO" if symbol_value == "PORT" else symbol_value


def format_strategy_signal_for_display(
    signal: TypedStrategySignal,
    strategy_allocation_fraction: float,
    multi_signal_context: dict[str, float] | None = None,
) -> StrategySignalDisplayDTO:
    """Format a typed strategy signal for display.

    Args:
        signal: Typed domain strategy signal
        strategy_allocation_fraction: Strategy-level allocation fraction (0-1)
        multi_signal_context: Optional mapping of constituent symbol -> fraction of total
            strategy allocation (already multiplied by *intra* weight) used to build a
            breakdown for portfolio strategies.

    Returns:
        Display dict with restored legacy allocation semantics.

    """
    symbol_value = signal.symbol.value
    symbol_str = handle_portfolio_symbol_alias(symbol_value)

    intra_fraction = float(signal.target_allocation.value)

    reasoning = signal.reasoning
    breakdown_text = ""
    if multi_signal_context and len(multi_signal_context) > 1:
        # Build breakdown similar to legacy implementation: weights as % of total portfolio
        lines: list[str] = ["Nuclear Portfolio Breakdown:"]
        for sym, weight in sorted(multi_signal_context.items()):
            lines.append(f"• {sym}: {weight * 100:.1f}%")
        breakdown_text = "\n\n" + "\n".join(lines)
        reasoning = reasoning.split(" | Nuclear portfolio constituent")[0] + breakdown_text
        symbol_str = f"NUCLEAR_PORTFOLIO ({', '.join(sorted(multi_signal_context.keys()))})"

    display: StrategySignalDisplayDTO = StrategySignalDisplayDTO(
        symbol=symbol_str,
        action=signal.action,
        confidence=float(signal.confidence.value),
        reasoning=reasoning,
        allocation_weight=strategy_allocation_fraction,
        allocation_percentage=strategy_allocation_fraction,  # alias
        intra_strategy_weight=intra_fraction,
    )
    if breakdown_text:
        display["constituents_breakdown"] = breakdown_text.strip()
    return display


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


def typed_signals_to_display_signals_dict(
    aggregated: AggregatedSignals,
    strategy_allocations: dict[StrategyType, float],
) -> dict[StrategyType, StrategySignalDisplayDTO]:
    """Convert AggregatedSignals to display signals dict format.

    Restores legacy semantics for allocation_weight while enriching multi-signal strategies.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager
        strategy_allocations: Strategy -> allocation fraction

    Returns:
        Display signals dict keyed by StrategyType.

    """
    display_signals: dict[StrategyType, StrategySignalDisplayDTO] = {}

    for strategy_type, signals in aggregated.get_signals_by_strategy().items():
        if not signals:
            display_signals[strategy_type] = create_empty_signal_dict()
            continue

        strategy_alloc_fraction = float(strategy_allocations.get(strategy_type, 0.0))

        if len(signals) == 1:
            display_signals[strategy_type] = format_strategy_signal_for_display(
                signals[0], strategy_alloc_fraction
            )
        else:
            # Build multi-signal constituent mapping: symbol -> total portfolio fraction
            constituents: dict[str, float] = {}
            for sig in signals:
                sym = sig.symbol.value
                if sym == "PORT":
                    continue
                constituents[sym] = float(sig.target_allocation.value) * strategy_alloc_fraction
            # Use first signal for base reasoning/action
            display_signals[strategy_type] = format_strategy_signal_for_display(
                signals[0], strategy_alloc_fraction, constituents
            )

    return display_signals


def compute_consolidated_portfolio(
    aggregated: AggregatedSignals,
    strategy_allocations: dict[StrategyType, float],
) -> tuple[dict[str, float], dict[str, list[StrategyType]]]:
    """Build consolidated portfolio and symbol strategy attribution.

    Business Rules:
    * Only BUY/LONG signals contribute positive weight.
    * SELL signals imply zero desired allocation (they do NOT add weight). If a symbol
      receives only SELL signals it is omitted (target = 0). Mixed BUY/SELL across
      strategies results in the net positive BUY contributions (no subtraction logic yet).
    * Portfolio (aggregate) placeholder symbol 'PORT' is ignored for direct allocation.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager
        strategy_allocations: Portfolio allocation between strategies (fractions 0-1)

    Returns:
        (consolidated_portfolio, strategy_attribution)
        * consolidated_portfolio: symbol -> fractional target weight (0-1)
        * strategy_attribution: symbol -> list of strategies contributing a BUY/LONG weight

    """
    consolidated_portfolio: dict[str, float] = {}
    attribution: dict[str, list[StrategyType]] = defaultdict(list)

    for strategy_type, signals in aggregated.get_signals_by_strategy().items():
        strategy_allocation = strategy_allocations.get(strategy_type, 0.0)
        if strategy_allocation <= 0:
            continue
        for signal in signals:
            action = str(signal.action)
            symbol_str = signal.symbol.value
            if symbol_str == "PORT":  # Skip synthetic portfolio container symbol
                continue
            if action in BUY_ACTIONS:
                individual_allocation = float(signal.target_allocation.value) * strategy_allocation
                if individual_allocation <= 0:
                    continue
                if symbol_str in consolidated_portfolio:
                    consolidated_portfolio[symbol_str] += individual_allocation
                else:
                    consolidated_portfolio[symbol_str] = individual_allocation
                if strategy_type not in attribution[symbol_str]:  # Avoid duplicates
                    attribution[symbol_str].append(strategy_type)
            # SELL actions intentionally ignored for now (no netting). Future enhancement:
            # subtract SELL contributions or mark symbol for full exit.

    return consolidated_portfolio, dict(attribution)


def run_all_strategies_mapping(
    aggregated: AggregatedSignals,
    strategy_allocations: dict[StrategyType, float],
) -> tuple[
    dict[StrategyType, StrategySignalDisplayDTO],
    dict[str, float],
    dict[str, list[StrategyType]],
]:
    """Main mapping function to convert typed signals to display format.

    This function replaces the complex logic in StrategyManagerAdapter.run_all_strategies()
    with a pure mapping approach that reuses domain value objects and avoids duplication.

    Args:
        aggregated: Aggregated signals from TypedStrategyManager
        strategy_allocations: Portfolio allocation between strategies

    Returns:
        Tuple containing:
        - Display signals dict for CLI compatibility
        - Consolidated portfolio allocation dict
        - Strategy attribution dict (empty for now, preserved for interface compatibility)

    """
    # Convert typed signals to display format (with restored semantics)
    display_signals = typed_signals_to_display_signals_dict(aggregated, strategy_allocations)

    # Compute consolidated portfolio allocations + attribution
    consolidated_portfolio, strategy_attribution = compute_consolidated_portfolio(
        aggregated, strategy_allocations
    )

    # Return strongly-typed display signals; callers expecting loose dicts should adapt upstream.
    return display_signals, consolidated_portfolio, strategy_attribution
