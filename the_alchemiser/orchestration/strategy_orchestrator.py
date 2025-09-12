"""Business Unit: orchestration | Status: current

Multi-strategy coordination orchestration.

Coordinates strategy allocation and signal aggregation across multiple strategies.
Extracted from deprecated /strategy/managers/typed_strategy_manager.py.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config.confidence_config import ConfidenceConfig
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.strategy_types import StrategyType
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.shared.types import StrategyEngine, StrategySignal, Confidence
from the_alchemiser.shared.types.exceptions import StrategyExecutionError


class AggregatedSignals:
    """Aggregated strategy signals with conflict resolution."""

    def __init__(self) -> None:
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


class StrategyOrchestrator:
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
            raise ValueError(f"Strategy allocations must sum to 1.0, got {total_allocation}")

        # Initialize typed strategy engines
        self.strategy_engines: dict[StrategyType, StrategyEngine] = {}
        self._initialize_typed_engines()

        self.logger.info(
            f"StrategyOrchestrator initialized with allocations: {self.strategy_allocations}"
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
                self.logger.error(f"Failed to initialize {strategy_type.value} typed engine: {e}")
                # Collect failed strategies for removal after iteration
                failed_strategies.append(strategy_type)
        
        # Remove failed strategies from allocations
        for strategy_type in failed_strategies:
            del self.strategy_allocations[strategy_type]

    def _create_typed_engine(self, strategy_type: StrategyType) -> StrategyEngine:
        """Create typed strategy engine instance."""
        if strategy_type == StrategyType.NUCLEAR:
            # Direct import to avoid circular dependency during migration
            from the_alchemiser.strategy_v2.engines.nuclear.engine import NuclearEngine
            return NuclearEngine(self.market_data_port)
        if strategy_type == StrategyType.KLM:
            # Direct import to avoid circular dependency during migration
            from the_alchemiser.strategy_v2.engines.klm.engine import KLMEngine
            return KLMEngine(self.market_data_port)
        if strategy_type == StrategyType.TECL:
            # Direct import to avoid circular dependency during migration
            from the_alchemiser.strategy_v2.engines.tecl.engine import TECLEngine
            return TECLEngine(self.market_data_port)
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    def generate_all_signals(self, timestamp: datetime | None = None) -> AggregatedSignals:
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
                self.logger.info(f"Generating signals from {strategy_type.value} strategy")

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
                self.logger.info(f"{strategy_type.value} generated {len(signals)} signals")

            except Exception as e:
                # Log error and determine if this is a critical failure
                self.logger.error(f"Error generating signals for {strategy_type.value}: {e}")

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
        signals_by_symbol: dict[str, list[tuple[StrategyType, StrategySignal]]] = {}

        for strategy_type, signals in aggregated.signals_by_strategy.items():
            for signal in signals:
                symbol_str = signal.symbol.value
                if symbol_str not in signals_by_symbol:
                    signals_by_symbol[symbol_str] = []
                signals_by_symbol[symbol_str].append((strategy_type, signal))

        # Process each symbol
        for symbol_str, strategy_signals in signals_by_symbol.items():
            if len(strategy_signals) == 1:
                # No conflict - use the single signal
                _, signal = strategy_signals[0]
                aggregated.consolidated_signals.append(signal)
            else:
                # Multiple strategies have opinions on this symbol - resolve conflict
                resolved_signal = self._resolve_signal_conflict(symbol_str, strategy_signals)
                if resolved_signal:
                    aggregated.consolidated_signals.append(resolved_signal)

                # Record the conflict for analysis
                conflict = {
                    "symbol": symbol_str,
                    "strategies": [strategy.value for strategy, _ in strategy_signals],
                    "actions": [signal.action for _, signal in strategy_signals],
                    "confidences": [
                        float(signal.confidence.value) for _, signal in strategy_signals
                    ],
                    "resolution": resolved_signal.action if resolved_signal else "NO_ACTION",
                }
                aggregated.conflicts.append(conflict)

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
        self.logger.info(f"Resolving conflict for {symbol} with {len(strategy_signals)} signals")

        # Filter signals that meet minimum confidence thresholds
        valid_signals = self._filter_by_confidence_thresholds(strategy_signals)

        if not valid_signals:
            self.logger.warning(f"No signals for {symbol} meet minimum confidence thresholds")
            return None

        if len(valid_signals) == 1:
            # Only one signal meets thresholds
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

    def _filter_by_confidence_thresholds(
        self, strategy_signals: list[tuple[StrategyType, StrategySignal]]
    ) -> list[tuple[StrategyType, StrategySignal]]:
        """Filter signals that meet minimum confidence thresholds for their action."""
        thresholds = self.confidence_config.aggregation.thresholds
        valid_signals = []

        for strategy_type, signal in strategy_signals:
            min_threshold = thresholds.get_threshold(signal.action)
            if signal.confidence.value >= min_threshold:
                valid_signals.append((strategy_type, signal))
            else:
                self.logger.debug(
                    f"Signal {strategy_type.value}:{signal.symbol.value}:{signal.action} "
                    f"confidence {signal.confidence.value:.2f} below threshold {min_threshold:.2f}"
                )

        return valid_signals

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
            total_weighted_confidence / total_weight if total_weight > 0 else Decimal("0.5")
        )

        combined_reasoning += f"• Final confidence: {final_confidence:.2f} (weighted average)"

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
        """
        best_score = Decimal("-1")
        best_signals: list[tuple[StrategyType, StrategySignal]] = []

        reasoning = f"Conflict resolution for {symbol}:\n"

        # Calculate weighted scores for all signals
        for strategy_type, signal in strategy_signals:
            weight = Decimal(str(self.strategy_allocations[strategy_type]))
            confidence_value = signal.confidence.value
            weighted_score = confidence_value * weight

            reasoning += (
                f"• {strategy_type.value}: {signal.action} "
                f"(confidence: {confidence_value:.2f}, weight: {weight:.1%}, "
                f"score: {weighted_score:.3f})\n"
            )

            if weighted_score > best_score:
                best_score = weighted_score
                best_signals = [(strategy_type, signal)]
            elif weighted_score == best_score:
                best_signals.append((strategy_type, signal))

        # Handle ties with explicit tie-breaking rules
        if len(best_signals) > 1:
            reasoning += (
                f"• Tie detected with {len(best_signals)} signals at score {best_score:.3f}\n"
            )
            best_strategy, best_signal = self._break_tie(best_signals)
            reasoning += f"• Tie-breaker: {best_strategy.value} (priority order + allocation)\n"
        else:
            best_strategy, best_signal = best_signals[0]

        reasoning += f"• Winner: {best_strategy.value} with weighted score {best_score:.3f}"

        # Create new signal with combined reasoning
        return StrategySignal(
            symbol=best_signal.symbol,
            action=best_signal.action,
            confidence=best_signal.confidence,
            target_allocation=best_signal.target_allocation,
            reasoning=reasoning,
            timestamp=best_signal.timestamp,
        )

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
        def tie_break_key(item: tuple[StrategyType, StrategySignal]) -> tuple[float, int]:
            strategy_type, _ = item
            allocation = self.strategy_allocations[strategy_type]

            # Get priority index (lower = higher priority)
            priority_order = self.confidence_config.aggregation.strategy_priority
            try:
                priority_index = priority_order.index(strategy_type.value)
            except ValueError:
                priority_index = len(priority_order)  # Unknown strategies get lowest priority

            return (-allocation, priority_index)  # Negative allocation for descending sort

        tied_signals.sort(key=tie_break_key)
        return tied_signals[0]

    def get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Get current strategy allocations."""
        return self.strategy_allocations.copy()

    def get_enabled_strategies(self) -> list[StrategyType]:
        """Get list of enabled strategy types."""
        return list(self.strategy_engines.keys())