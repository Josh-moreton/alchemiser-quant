"""Business Unit: orchestration | Status: current.

Multi-strategy coordination orchestration.

Coordinates strategy allocation and signal aggregation across multiple strategies.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config.confidence_config import ConfidenceConfig
from the_alchemiser.shared.types import Confidence, StrategyEngine, StrategySignal
from the_alchemiser.shared.types.exceptions import StrategyExecutionError
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.strategy_types import StrategyType
from the_alchemiser.shared.value_objects.symbol import Symbol


class AggregatedSignals:
    """Aggregated strategy signals with conflict resolution."""

    def __init__(self) -> None:
        """Initialize containers for per-strategy and consolidated signals."""
        self.signals_by_strategy: dict[StrategyType, list[StrategySignal]] = {}
        self.consolidated_signals: list[StrategySignal] = []
        self.conflicts: list[dict[str, Any]] = []

    def add_strategy_signals(
        self, strategy_type: StrategyType, signals: list[StrategySignal]
    ) -> None:
        """Add signals from a specific strategy."""
        self.signals_by_strategy[strategy_type] = signals

    def get_all_signals(self) -> list[StrategySignal]:
        """Get all signals from all strategies."""
        all_signals = []
        for signals in self.signals_by_strategy.values():
            all_signals.extend(signals)
        return all_signals

    def get_signals_by_strategy(self) -> dict[StrategyType, list[StrategySignal]]:
        """Get signals grouped by strategy."""
        return self.signals_by_strategy.copy()


class MultiStrategyOrchestrator:
    """Orchestrates multiple strategies and handles signal aggregation.

    This orchestrator coordinates typed strategy engines and aggregates their signals
    with proper conflict resolution and allocation management.
    """

    def __init__(
        self,
        market_data_port: MarketDataPort,
        strategy_allocations: dict[StrategyType, float] | None = None,
    ) -> None:
        """Initialize strategy orchestrator.

        Args:
            market_data_port: Market data access interface
            strategy_allocations: Optional strategy allocations (defaults from registry)

        """
        self.market_data_port = market_data_port
        self.logger = logging.getLogger(__name__)
        self.confidence_config = ConfidenceConfig.default()

        # Use provided allocations or defaults from registry
        if strategy_allocations is None:
            from the_alchemiser.shared.types.strategy_registry import StrategyRegistry

            self.strategy_allocations = StrategyRegistry.get_default_allocations()
        else:
            # Filter to only enabled strategies
            from the_alchemiser.shared.types.strategy_registry import StrategyRegistry

            self.strategy_allocations = {
                strategy_type: allocation
                for strategy_type, allocation in strategy_allocations.items()
                if StrategyRegistry.is_strategy_enabled(strategy_type)
            }

        # Validate allocations sum to 1.0
        total_allocation = sum(self.strategy_allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(
                f"Strategy allocations must sum to 1.0, got {total_allocation}"
            )

        # Initialize typed strategy engines
        self.strategy_engines: dict[StrategyType, StrategyEngine] = {}
        self._initialize_typed_engines()

        self.logger.info(
            f"MultiStrategyOrchestrator initialized with allocations: {self.strategy_allocations}"
        )

    def _initialize_typed_engines(self) -> None:
        """Initialize typed strategy engines that implement StrategyEngine protocol."""
        failed_strategies = []

        for strategy_type in self.strategy_allocations:
            try:
                engine = self._create_typed_engine(strategy_type)
                self.strategy_engines[strategy_type] = engine
                self.logger.info(
                    f"Initialized {strategy_type.value} typed engine with "
                    f"{self.strategy_allocations[strategy_type]:.1%} allocation"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize {strategy_type.value} typed engine: {e}"
                )
                # Collect failed strategies for removal after iteration
                failed_strategies.append(strategy_type)

        # Remove failed strategies from allocations
        for strategy_type in failed_strategies:
            del self.strategy_allocations[strategy_type]

    def _create_typed_engine(self, strategy_type: StrategyType) -> StrategyEngine:
        """Create typed strategy engine instance."""
        if strategy_type == StrategyType.DSL:
            # Direct import to avoid circular dependency during migration
            from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import (
                DslStrategyEngine,
            )

            return DslStrategyEngine(self.market_data_port)

        # For this PR, we only support DSL engine to test the integration
        raise ValueError(
            f"Strategy type {strategy_type} not supported in this DSL-focused PR"
        )

    def generate_all_signals(
        self, timestamp: datetime | None = None
    ) -> AggregatedSignals:
        """Generate signals from all enabled strategies.

        Args:
            timestamp: Optional timestamp for signal generation (defaults to now)

        Returns:
            AggregatedSignals containing all strategy signals and aggregation results

        Raises:
            StrategyExecutionError: If signal generation fails

        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        aggregated = AggregatedSignals()

        # Generate signals from each strategy
        for strategy_type, engine in self.strategy_engines.items():
            try:
                self.logger.info(
                    f"Generating signals from {strategy_type.value} strategy"
                )

                if hasattr(engine, "generate_signals"):
                    # All engines now use new constructor injection interface
                    signals = engine.generate_signals(timestamp)
                else:
                    self.logger.warning(
                        f"{strategy_type.value} engine doesn't have generate_signals method"
                    )
                    signals = []

                # Validate signals
                if signals and hasattr(engine, "validate_signals"):
                    engine.validate_signals(signals)

                aggregated.add_strategy_signals(strategy_type, signals)
                self.logger.info(
                    f"{strategy_type.value} generated {len(signals)} signals"
                )

            except Exception as e:
                # Log error and determine if this is a critical failure
                self.logger.error(
                    f"Error generating signals for {strategy_type.value}: {e}"
                )

                # Critical errors that should fail the entire operation
                error_message = str(e)
                error_type = type(e).__name__

                # System errors that indicate fundamental configuration or code issues
                critical_patterns = [
                    "No module named",
                    "ImportError",
                    "ModuleNotFoundError",
                    "cannot import name",
                    "object has no attribute",  # AttributeError missing attributes
                    "not defined",
                    "is not callable",
                ]

                critical_error_types = [
                    "AttributeError",  # Missing attributes on strategy engines
                    "NameError",  # Undefined variables/functions
                    "TypeError",  # Incorrect type usage in core functionality
                ]

                if (
                    any(pattern in error_message for pattern in critical_patterns)
                    or error_type in critical_error_types
                ):
                    # System errors indicate fundamental configuration/code issues
                    # that should cause the entire signal generation to fail
                    raise StrategyExecutionError(
                        f"Critical system error in {strategy_type.value} strategy: {e}. "
                        f"This indicates a fundamental code or configuration issue "
                        f"(error type: {error_type}) that prevents strategy execution "
                        f"and should be resolved before proceeding."
                    )

                # Non-critical errors: continue with other strategies
                aggregated.add_strategy_signals(strategy_type, [])
                continue

        # Perform aggregation and conflict resolution
        self._aggregate_signals(aggregated)

        return aggregated

    def _aggregate_signals(self, aggregated: AggregatedSignals) -> None:
        """Aggregate signals from multiple strategies and resolve conflicts.

        Args:
            aggregated: AggregatedSignals object to populate with consolidated results

        """
        # Group signals by symbol
        signals_by_symbol = self._group_signals_by_symbol(
            aggregated.signals_by_strategy
        )

        # Process each symbol
        for symbol_str, strategy_signals in signals_by_symbol.items():
            if len(strategy_signals) == 1:
                # No conflict - use the single signal
                _, signal = strategy_signals[0]
                aggregated.consolidated_signals.append(signal)
            else:
                # Multiple strategies have opinions on this symbol - resolve conflict
                resolved_signal = self._resolve_signal_conflict(
                    symbol_str, strategy_signals
                )
                if resolved_signal:
                    aggregated.consolidated_signals.append(resolved_signal)

                # Record the conflict for analysis
                conflict = self._create_conflict_record(
                    symbol_str, strategy_signals, resolved_signal
                )
                aggregated.conflicts.append(conflict)

    def _group_signals_by_symbol(
        self, signals_by_strategy: dict[StrategyType, list[StrategySignal]]
    ) -> dict[str, list[tuple[StrategyType, StrategySignal]]]:
        """Group signals by symbol across all strategies.

        Args:
            signals_by_strategy: Signals grouped by strategy type

        Returns:
            Dictionary mapping symbol strings to lists of (strategy_type, signal) tuples

        """
        signals_by_symbol: dict[str, list[tuple[StrategyType, StrategySignal]]] = {}

        for strategy_type, signals in signals_by_strategy.items():
            for signal in signals:
                symbol_str = signal.symbol.value
                if symbol_str not in signals_by_symbol:
                    signals_by_symbol[symbol_str] = []
                signals_by_symbol[symbol_str].append((strategy_type, signal))

        return signals_by_symbol

    def _create_conflict_record(
        self,
        symbol_str: str,
        strategy_signals: list[tuple[StrategyType, StrategySignal]],
        resolved_signal: StrategySignal | None,
    ) -> dict[str, Any]:
        """Create a conflict record for analysis.

        Args:
            symbol_str: Symbol with conflicting signals
            strategy_signals: List of conflicting signals from different strategies
            resolved_signal: The resolved signal (if any)

        Returns:
            Dictionary containing conflict analysis data

        """
        return {
            "symbol": symbol_str,
            "strategies": [strategy.value for strategy, _ in strategy_signals],
            "actions": [signal.action for _, signal in strategy_signals],
            "confidences": [
                float(signal.confidence.value) for _, signal in strategy_signals
            ],
            "resolution": resolved_signal.action if resolved_signal else "NO_ACTION",
        }

    def _resolve_signal_conflict(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal | None:
        """Resolve conflicts when multiple strategies have different opinions on the same symbol.

        Args:
            symbol: The symbol with conflicting signals
            strategy_signals: List of (strategy_type, signal) tuples

        Returns:
            Resolved StrategySignal or None if no resolution possible

        """
        self.logger.info(
            f"Resolving conflict for {symbol} with {len(strategy_signals)} signals"
        )

        # Use ALL signals - no confidence threshold filtering
        # Strategy signals are concrete and should not be filtered by confidence
        valid_signals = strategy_signals

        if not valid_signals:
            self.logger.warning(f"No signals provided for {symbol}")
            return None

        if len(valid_signals) == 1:
            # Only one signal - use it directly
            _, signal = valid_signals[0]
            return signal

        # Conflict resolution strategy:
        # 1. If all actions are the same, combine with weighted confidence
        # 2. If actions differ, use highest confidence signal with explicit tie-breaking
        # 3. Weight by strategy allocation

        actions = [signal.action for _, signal in valid_signals]
        unique_actions = set(actions)

        if len(unique_actions) == 1:
            # All strategies agree on action - combine confidences
            return self._combine_agreeing_signals(symbol, valid_signals)
        # Strategies disagree - use highest weighted confidence with tie-breaking
        return self._select_highest_confidence_signal(symbol, valid_signals)

    def _combine_agreeing_signals(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal:
        """Combine signals when all strategies agree on the action."""
        # Use the first signal as template
        _, template_signal = strategy_signals[0]

        # Calculate weighted confidence
        total_weighted_confidence = Decimal("0")
        total_weight = Decimal("0")
        combined_reasoning = f"Combined signal for {symbol}:\n"

        for strategy_type, signal in strategy_signals:
            weight = Decimal(str(self.strategy_allocations[strategy_type]))
            confidence_value = signal.confidence.value
            weighted_confidence = confidence_value * weight

            total_weighted_confidence += weighted_confidence
            total_weight += weight

            combined_reasoning += (
                f"• {strategy_type.value}: {signal.action} "
                f"(confidence: {confidence_value:.2f}, weight: {weight:.1%})\n"
            )

        # Average confidence weighted by strategy allocation
        final_confidence = (
            total_weighted_confidence / total_weight
            if total_weight > 0
            else Decimal("0.5")
        )

        combined_reasoning += (
            f"• Final confidence: {final_confidence:.2f} (weighted average)"
        )

        return StrategySignal(
            symbol=Symbol(symbol),
            action=template_signal.action,
            confidence=Confidence(final_confidence),
            target_allocation=template_signal.target_allocation,
            reasoning=combined_reasoning,
            timestamp=template_signal.timestamp,
        )

    def _select_highest_confidence_signal(
        self, symbol: str, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> StrategySignal:
        """Select signal with highest weighted confidence when strategies disagree.

        Implements explicit tie-breaking rules for deterministic behavior.
        Applies confidence-based weight adjustment up to 10% boost/reduction for high/low confidence strategies.
        """
        best_score = Decimal("-1")
        best_signals: list[tuple[StrategyType, StrategySignal]] = []

        reasoning = f"Conflict resolution for {symbol}:\n"

        # Calculate weighted scores for all signals
        for strategy_type, signal in strategy_signals:
            base_weight = Decimal(str(self.strategy_allocations[strategy_type]))
            confidence_value = signal.confidence.value

            # Apply confidence-based weight adjustment (up to 10% boost/reduction)
            confidence_adjusted_weight = self._apply_confidence_weighting(
                base_weight, confidence_value, strategy_signals
            )

            weighted_score = confidence_value * confidence_adjusted_weight

            reasoning += (
                f"• {strategy_type.value}: {signal.action} "
                f"(confidence: {confidence_value:.2f}, weight: {confidence_adjusted_weight:.1%}, "
                f"score: {weighted_score:.3f})\n"
            )

            if weighted_score > best_score:
                best_score = weighted_score
                best_signals = [(strategy_type, signal)]
            elif weighted_score == best_score:
                best_signals.append((strategy_type, signal))

        # Handle ties with explicit tie-breaking rules
        if len(best_signals) > 1:
            reasoning += f"• Tie detected with {len(best_signals)} signals at score {best_score:.3f}\n"
            best_strategy, best_signal = self._break_tie(best_signals)
            reasoning += (
                f"• Tie-breaker: {best_strategy.value} (priority order + allocation)\n"
            )
        else:
            best_strategy, best_signal = best_signals[0]

        reasoning += (
            f"• Winner: {best_strategy.value} with weighted score {best_score:.3f}"
        )

        # Create new signal with combined reasoning
        return StrategySignal(
            symbol=best_signal.symbol,
            action=best_signal.action,
            confidence=best_signal.confidence,
            target_allocation=best_signal.target_allocation,
            reasoning=reasoning,
            timestamp=best_signal.timestamp,
        )

    def _apply_confidence_weighting(
        self,
        base_weight: Decimal,
        confidence: Decimal,
        all_signals: list[tuple[StrategyType, StrategySignal]],
    ) -> Decimal:
        """Apply confidence-based weight adjustment up to 10% boost/reduction.

        High confidence strategies get up to 10% additional weighting vs low confidence.
        This provides gentle weighting between strategies based on their conviction.
        """
        if len(all_signals) <= 1:
            return base_weight

        # Get confidence values from all strategies
        confidences = [signal.confidence.value for _, signal in all_signals]
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        # If all strategies have same confidence, no adjustment needed
        if max_confidence == min_confidence:
            return base_weight

        # Calculate relative confidence position (0.0 to 1.0)
        confidence_range = max_confidence - min_confidence
        relative_confidence = (confidence - min_confidence) / confidence_range

        # Apply up to 10% weight adjustment
        max_adjustment = (
            self.confidence_config.aggregation.max_confidence_weight_adjustment
        )
        weight_adjustment = (relative_confidence - Decimal("0.5")) * max_adjustment * 2

        # Apply adjustment to base weight
        adjusted_weight = base_weight * (Decimal("1.0") + weight_adjustment)

        # Ensure weight stays positive and reasonable
        return max(Decimal("0.01"), adjusted_weight)

    def _break_tie(
        self, tied_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> tuple[StrategyType, StrategySignal]:
        """Break ties using explicit priority rules.

        Tie-breaking order:
        1. Highest strategy allocation
        2. Strategy priority order (NUCLEAR > TECL > KLM)
        3. First encountered (deterministic fallback)
        """

        # Sort by allocation (descending), then by priority order
        def tie_break_key(
            item: tuple[StrategyType, StrategySignal],
        ) -> tuple[float, int]:
            strategy_type, _ = item
            allocation = self.strategy_allocations[strategy_type]

            # Get priority index (lower = higher priority)
            priority_order = self.confidence_config.aggregation.strategy_priority
            try:
                priority_index = priority_order.index(strategy_type.value)
            except ValueError:
                priority_index = len(
                    priority_order
                )  # Unknown strategies get lowest priority

            return (
                -allocation,
                priority_index,
            )  # Negative allocation for descending sort

        tied_signals.sort(key=tie_break_key)
        return tied_signals[0]

    def get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Get current strategy allocations."""
        return self.strategy_allocations.copy()

    def get_enabled_strategies(self) -> list[StrategyType]:
        """Get list of enabled strategy types."""
        return list(self.strategy_engines.keys())
