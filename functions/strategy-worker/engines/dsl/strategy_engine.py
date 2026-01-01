#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine Wrapper.

Adapts the DSL engine to work with the existing StrategyEngine protocol
for integration with the multi-strategy orchestrator.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from importlib import resources as importlib_resources
from importlib.abc import Traversable
from pathlib import Path
from typing import Any

from engines.dsl.engine import DslEngine
from errors import ConfigurationError, StrategyExecutionError

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.strategy_signal import StrategySignal
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

# Module-level constants for maintainability
DEFAULT_STRATEGY_FILE = "KLM.clj"
# Accounts for '... [N decisions]' truncation suffix when reasoning exceeds max length
REASONING_TRUNCATION_SUFFIX_LENGTH = 20


def _get_strategies_path() -> Traversable | Path:
    """Get strategies directory path (Lambda layer or local).

    Returns:
        Traversable for Lambda layer, or Path for local development

    """
    try:
        # Try Lambda layer first (returns Traversable, don't convert to Path)
        return importlib_resources.files("the_alchemiser.shared.strategies")
    except (ModuleNotFoundError, AttributeError):
        # Fallback for local development - navigate from function to project root
        # __file__ = functions/strategy-worker/engines/dsl/strategy_engine.py
        # Project root is 5 levels up
        project_root = Path(__file__).parent.parent.parent.parent.parent
        strategies_path = (
            project_root / "layers" / "shared" / "the_alchemiser" / "shared" / "strategies"
        )
        if not strategies_path.exists():
            raise RuntimeError(
                f"Cannot find strategies directory at {strategies_path}. "
                "Ensure the shared layer structure exists."
            )
        return strategies_path


class DslStrategyEngine:
    """DSL Strategy Engine wrapper implementing StrategyEngine protocol.

    This wrapper adapts the DSL engine to work with the existing multi-strategy
    orchestration system by implementing the StrategyEngine protocol.
    """

    def __init__(self, market_data_port: MarketDataPort, strategy_file: str | None = None) -> None:
        """Initialize DSL strategy engine.

        Args:
            market_data_port: Market data provider (required by protocol, not used in DSL)
            strategy_file: Optional path to .clj strategy file (defaults to klm original.clj)

        """
        self.market_data_port = market_data_port  # Required by protocol
        self.logger = get_logger(__name__)

        # Default strategy file if not provided (single-file fallback)
        self.strategy_file = strategy_file or DEFAULT_STRATEGY_FILE

        # Load settings with proper error handling
        try:
            self.settings = Settings()
        except (ConfigurationError, ValueError, TypeError) as e:
            self.logger.warning(
                f"Settings load failed, using defaults: {e}",
                extra={"error_type": type(e).__name__},
            )
            # Provide safe fallback with minimal default settings
            from the_alchemiser.shared.config.config import StrategySettings

            class MinimalSettings:
                """Minimal fallback settings for DSL engine."""

                def __init__(self) -> None:
                    self.strategy = StrategySettings(
                        dsl_files=[DEFAULT_STRATEGY_FILE],
                        dsl_allocations={DEFAULT_STRATEGY_FILE: 1.0},
                    )

            self.settings = MinimalSettings()  # type: ignore[assignment]

        # Initialize DSL engine with strategies directory as config path
        # Use importlib.resources to locate strategies in Lambda layer or local
        strategies_path = _get_strategies_path()
        # Pass Traversable or Path directly (don't convert to string)
        self.dsl_engine = DslEngine(
            strategy_config_path=strategies_path,
        )

        configured_dsl_files = self.settings.strategy.dsl_files or [self.strategy_file]
        self.logger.info(
            f"DSL Strategy Engine initialized with files: {', '.join(configured_dsl_files)}"
        )

    def generate_signals(
        self,
        timestamp: datetime,
    ) -> list[StrategySignal]:
        """Generate strategy signals using DSL engine."""
        try:
            correlation_id = str(uuid.uuid4())
            dsl_files, normalized_file_weights = self._resolve_dsl_files_and_weights()

            self.logger.info(f"Generating DSL signals from {len(dsl_files)} files")

            file_results = self._evaluate_files_sequential(
                dsl_files, correlation_id, normalized_file_weights
            )

            consolidated, decision_path = self._accumulate_results(dsl_files, file_results)
            if not consolidated:
                return self._create_fallback_signals(timestamp)

            # Create per-file signals showing each strategy's allocations
            signals = self._create_per_file_signals(
                dsl_files,
                file_results,
                timestamp,
                correlation_id,
            )

            self.logger.info(
                f"Generated {len(signals)} DSL strategy signals from {len(dsl_files)} files",
                extra={
                    "correlation_id": correlation_id,
                    "strategies": [Path(f).stem for f in dsl_files],
                },
            )

            return signals

        except (StrategyExecutionError, ValueError, RuntimeError) as e:
            self.logger.error(
                f"DSL strategy error: {e}",
                extra={
                    "correlation_id": (correlation_id if "correlation_id" in locals() else None),
                    "error_type": type(e).__name__,
                },
            )
            return self._create_fallback_signals(timestamp)

    def _accumulate_results(
        self,
        dsl_files: list[str],
        file_results: list[
            tuple[dict[str, Decimal] | None, str, Decimal, Decimal, list[dict[str, Any]] | None]
        ],
    ) -> tuple[dict[str, Decimal], list[dict[str, Any]] | None]:
        """Accumulate per-symbol weights from DSL file evaluation results using Decimal.

        Args:
            dsl_files: List of DSL files that were evaluated
            file_results: Results from file evaluations

        Returns:
            Tuple of (consolidated weights, first valid decision_path)

        """
        consolidated: dict[str, Decimal] = {}
        decision_path: list[dict[str, Any]] | None = None

        for _f, (per_file_weights, _trace_id, _, _, file_decision_path) in zip(
            dsl_files, file_results, strict=True
        ):
            if per_file_weights is None:  # Evaluation failed
                continue
            for symbol, weight in per_file_weights.items():
                consolidated[symbol] = consolidated.get(symbol, Decimal("0")) + weight

            # Use first valid decision path (for single-strategy cases)
            if decision_path is None and file_decision_path:
                decision_path = file_decision_path

        return consolidated, decision_path

    def _create_per_file_signals(
        self,
        dsl_files: list[str],
        file_results: list[
            tuple[dict[str, Decimal] | None, str, Decimal, Decimal, list[dict[str, Any]] | None]
        ],
        timestamp: datetime,
        correlation_id: str,
    ) -> list[StrategySignal]:
        """Create one signal per symbol with positive allocation across all DSL files.

        Args:
            dsl_files: List of DSL files that were evaluated
            file_results: Results from file evaluations
            timestamp: Timestamp for signal generation
            correlation_id: Correlation ID for tracing

        Returns:
            List of StrategySignal objects, one per symbol with positive allocation

        """
        signals: list[StrategySignal] = []

        for filename, (per_file_weights, _trace_id, _file_weight, _file_sum, _decision_path) in zip(
            dsl_files, file_results, strict=True
        ):
            if per_file_weights is None or not per_file_weights:
                continue

            # Extract strategy name from filename
            strategy_name = Path(filename).stem

            # Create one signal per symbol with positive weight
            for symbol, weight in per_file_weights.items():
                if weight <= 0:
                    continue

                # Build contextual reasoning from decision path if available
                # Falls back to simple allocation string if no decision path
                weight_float = float(weight)
                if _decision_path:
                    # Use decision path reasoning for contextual explanation
                    # Pass full allocation (converted to float) and strategy name for better context
                    per_file_weights_float = {s: float(w) for s, w in per_file_weights.items()}
                    reasoning = self._build_decision_reasoning(
                        _decision_path, weight_float, per_file_weights_float, strategy_name
                    )
                else:
                    # Fallback: show symbol allocation
                    reasoning = f"{strategy_name} allocation: {weight_float:.1%}"

                # Create signal for this symbol
                signal = StrategySignal(
                    symbol=Symbol(symbol),
                    action="BUY",
                    target_allocation=Decimal(str(weight)),
                    reasoning=reasoning,
                    timestamp=timestamp,
                    strategy_name=strategy_name,
                    data_source=f"dsl_engine:{filename}",
                    correlation_id=correlation_id,
                    causation_id=correlation_id,
                )
                signals.append(signal)

        return signals

    def _convert_to_signals(
        self,
        consolidated: dict[str, float],
        timestamp: datetime,
        correlation_id: str,
        dsl_files: list[str] | None = None,
        decision_path: list[dict[str, Any]] | None = None,
    ) -> list[StrategySignal]:
        """Convert consolidated weights to StrategySignal objects.

        This method is being refactored to create per-file signals.
        Currently creates consolidated signals only for backward compatibility.

        Args:
            consolidated: Dictionary mapping symbols to weights
            timestamp: Timestamp for signal generation
            correlation_id: Correlation ID for tracing
            dsl_files: Optional list of DSL files for attribution
            decision_path: Optional decision path from DSL evaluation

        Returns:
            List of StrategySignal objects for positive weights

        """
        signals: list[StrategySignal] = []

        # Extract strategy names from CLJ filenames (remove extension and path)
        strategy_names = []
        if dsl_files:
            for filename in dsl_files:
                # Use pathlib for robust cross-platform handling
                strategy_name = Path(filename).stem
                strategy_names.append(strategy_name)

        # Use first strategy name or fallback to "DSL" if no files provided
        primary_strategy = strategy_names[0] if strategy_names else "DSL"

        for symbol, weight in consolidated.items():
            if weight > 0:
                # For multiple strategies, show which ones contributed
                if len(strategy_names) > 1:
                    strategy_display = f"{primary_strategy} (+{len(strategy_names) - 1} others)"
                    reasoning = (
                        f"Multi-strategy allocation from {', '.join(strategy_names)}: {weight:.1%}"
                    )
                else:
                    strategy_display = primary_strategy
                    # Build reasoning from decision path if available
                    # Convert consolidated to float for legacy reasoning generation
                    consolidated_float = {s: float(w) for s, w in consolidated.items()}
                    reasoning = self._build_decision_reasoning(
                        decision_path, weight, consolidated_float, primary_strategy
                    )

                signals.append(
                    StrategySignal(
                        symbol=Symbol(symbol),
                        action="BUY",
                        target_allocation=Decimal(str(weight)),
                        reasoning=reasoning,
                        timestamp=timestamp,
                        strategy=strategy_display,
                        data_source="dsl_engine:multi",
                        correlation_id=correlation_id,
                        causation_id=correlation_id,  # Using correlation_id as causation for DSL signals
                    )
                )
        return signals

    def _create_fallback_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Create fallback signals when DSL evaluation fails.

        Args:
            timestamp: Timestamp for signal generation

        Returns:
            List containing a single CASH signal

        """
        # Extract strategy name from CLJ filename (remove extension and path) using pathlib
        strategy_name = Path(self.strategy_file).stem

        # Generate correlation IDs for fallback signal
        import uuid

        fallback_correlation_id = f"fallback-{uuid.uuid4().hex[:8]}"

        fallback_signal = StrategySignal(
            symbol=Symbol("CASH"),
            action="BUY",
            reasoning=f"{strategy_name} evaluation failed, fallback to cash position",
            timestamp=timestamp,
            strategy=strategy_name,
            data_source="dsl_fallback",
            fallback=True,
            dsl_file=self.strategy_file,
            correlation_id=fallback_correlation_id,
            causation_id=fallback_correlation_id,
        )
        return [fallback_signal]

    def _resolve_dsl_files_and_weights(self) -> tuple[list[str], dict[str, Decimal]]:
        """Resolve DSL files and normalize their weights to sum to 1.0 using Decimal.

        Returns:
            A tuple of (dsl_files, normalized_file_weights)

        Raises:
            ConfigurationError: If DSL files don't exist or weights are invalid

        """
        dsl_files = self.settings.strategy.dsl_files or [self.strategy_file]
        dsl_allocs = self.settings.strategy.dsl_allocations or {self.strategy_file: 1.0}

        # Validate files exist
        strategies_path = _get_strategies_path()
        for f in dsl_files:
            file_path = strategies_path / f
            # Handle both Path (.exists()) and Traversable (.is_file())
            if hasattr(file_path, "exists"):
                file_exists = file_path.exists()
            else:
                # Traversable uses is_file()
                file_exists = file_path.is_file()
            if not file_exists:
                raise ConfigurationError(f"DSL file not found: {f}", file_path=str(file_path))

        # Validate and normalize weights using Decimal for precision
        for f, w in dsl_allocs.items():
            if not isinstance(w, int | float | Decimal):
                raise ConfigurationError(
                    f"Invalid weight type for {f}: {type(w).__name__} (must be numeric)"
                )
            if w < 0:
                raise ConfigurationError(f"Invalid weight for {f}: {w} (must be non-negative)")

        total_alloc = sum(Decimal(str(w)) for w in dsl_allocs.values())
        if total_alloc == 0:
            total_alloc = Decimal("1.0")

        # Normalize to Decimal for precise arithmetic throughout
        normalized_file_weights = {
            f: Decimal(str(dsl_allocs.get(f, 0.0))) / total_alloc for f in dsl_files
        }
        return dsl_files, normalized_file_weights

    def _evaluate_file(
        self,
        filename: str,
        correlation_id: str,
        normalized_file_weights: dict[str, Decimal],
    ) -> tuple[dict[str, Decimal], str, Decimal, Decimal, list[dict[str, Any]] | None]:
        """Evaluate a single DSL file and return scaled per-symbol weights using Decimal.

        Args:
            filename: DSL file to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights (as Decimal)

        Returns:
            Tuple of (per_file_scaled_weights, trace_id, file_weight, file_sum, decision_path)

        """
        allocation, trace = self.dsl_engine.evaluate_strategy(filename, correlation_id)
        file_weight = normalized_file_weights.get(filename, Decimal("0"))
        file_sum = (
            sum(allocation.target_weights.values(), Decimal("0"))
            if allocation.target_weights
            else Decimal("0")
        )

        per_file_weights: dict[str, Decimal] = {}
        for symbol, weight in allocation.target_weights.items():
            # weight is already Decimal from allocation (PortfolioFragment)
            if weight <= Decimal("0"):
                continue
            per_file_weights[symbol] = file_weight * weight  # Decimal multiplication!

        # Format and log DSL evaluation results
        formatted_allocation = self._format_dsl_allocation(filename, allocation.target_weights)
        self.logger.debug(formatted_allocation)

        # Log diagnostic information about allocation scaling
        self.logger.info(
            f"DSL file evaluation: {Path(filename).stem}",
            extra={
                "filename": filename,
                "file_weight": str(file_weight),
                "file_sum": str(file_sum),
                "scaled_total": str(
                    sum(per_file_weights.values()) if per_file_weights else Decimal("0")
                ),
                "symbols": list(per_file_weights.keys()),
            },
        )

        # Extract decision path from trace metadata
        decision_path = trace.metadata.get("decision_path") if trace.metadata else None

        return per_file_weights, trace.trace_id, file_weight, file_sum, decision_path

    def _evaluate_files_sequential(
        self,
        dsl_files: list[str],
        correlation_id: str,
        normalized_file_weights: dict[str, Decimal],
    ) -> list[tuple[dict[str, Decimal] | None, str, Decimal, Decimal, list[dict[str, Any]] | None]]:
        """Evaluate DSL files sequentially.

        Args:
            dsl_files: List of DSL files to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            List of evaluation results for each file (preserves order)

        Raises:
            StrategyExecutionError: If all files fail to evaluate.

        """
        results: list[
            tuple[dict[str, Decimal] | None, str, Decimal, Decimal, list[dict[str, Any]] | None]
        ] = []
        failed_files: list[tuple[str, str]] = []  # (filename, error_message)

        for f in dsl_files:
            try:
                result = self._evaluate_file(f, correlation_id, normalized_file_weights)
                results.append(result)
            except (StrategyExecutionError, ValueError, RuntimeError) as e:
                self.logger.error(
                    f"DSL evaluation failed for {f}: {e}",
                    extra={
                        "correlation_id": correlation_id,
                        "filename": f,
                        "error_type": type(e).__name__,
                    },
                )
                failed_files.append((f, str(e)))
                results.append((None, "", Decimal("0"), Decimal("0"), None))

        # Log summary of partial failures if any occurred
        if failed_files:
            success_count = len(dsl_files) - len(failed_files)
            self.logger.warning(
                f"Partial strategy evaluation: {success_count}/{len(dsl_files)} files succeeded",
                extra={
                    "correlation_id": correlation_id,
                    "success_count": success_count,
                    "failure_count": len(failed_files),
                    "failed_files": [f for f, _ in failed_files],
                    "errors": dict(failed_files),
                },
            )

            # If ALL files failed, raise an error - partial results are invalid
            if success_count == 0:
                raise StrategyExecutionError(
                    f"All {len(dsl_files)} DSL files failed to evaluate: "
                    + ", ".join(f"{f}: {e}" for f, e in failed_files)
                )

        return results

    def _build_decision_reasoning(
        self,
        decision_path: list[dict[str, Any]] | None,
        weight: float | Decimal,
        allocation: dict[str, float] | None = None,
        strategy_name: str | None = None,
    ) -> str:
        """Build human-readable reasoning from decision path.

        Args:
            decision_path: List of decision nodes captured during evaluation
            weight: Allocation weight
            allocation: Optional full allocation dict for context
            strategy_name: Optional strategy name for context

        Returns:
            Human-readable reasoning string (max 1000 chars)

        """
        # Fallback if no decision path
        weight_float = float(weight)
        if not decision_path:
            return f"{weight_float:.1%} allocation"

        # Try natural language generation
        try:
            from the_alchemiser.shared.reasoning import NaturalLanguageGenerator

            nl_generator = NaturalLanguageGenerator()

            # Build allocation dict if not provided (single symbol case)
            if allocation is None:
                allocation = {}  # Will be handled by generator

            narrative = nl_generator.generate_reasoning(
                decision_path=decision_path,
                allocation=allocation,
                strategy_name=strategy_name or "Strategy",
            )

            # Use narrative if it looks good (no technical symbols)
            if narrative and "✓" not in narrative and "→" not in narrative:
                return narrative[:1000]  # Truncate to max length

        except (ImportError, Exception) as e:
            self.logger.warning(
                f"Natural language generation failed, using legacy format: {e}",
                extra={"error_type": type(e).__name__},
            )

        # Fallback to legacy format
        return self._build_legacy_reasoning(decision_path, weight_float)

    def _build_legacy_reasoning(
        self,
        decision_path: list[dict[str, Any]],
        weight: float,
    ) -> str:
        """Build reasoning using legacy format (backward compatibility).

        Args:
            decision_path: List of decision nodes
            weight: Allocation weight

        Returns:
            Legacy format reasoning string

        """
        reasoning_parts = []

        # Add key decisions (limit to most important ones to stay under 1000 chars)
        important_decisions = [d for d in decision_path if d.get("result", False)][:3]

        for decision in important_decisions:
            condition = decision.get("condition", "")
            if condition:
                reasoning_parts.append(f"✓ {condition}")

        # Combine with allocation info
        if reasoning_parts:
            decision_summary = " → ".join(reasoning_parts)
            reasoning = f"{decision_summary} → {weight:.1%} allocation"
        else:
            reasoning = f"{weight:.1%} allocation"

        # Truncate to max length (1000 chars for StrategySignal.reasoning field)
        max_length = 1000
        if len(reasoning) > max_length:
            reasoning = (
                reasoning[: max_length - REASONING_TRUNCATION_SUFFIX_LENGTH]
                + f"... [{len(decision_path)} decisions]"
            )

        return reasoning

    def _format_dsl_allocation(self, filename: str, target_weights: dict[str, Decimal]) -> str:
        """Format DSL allocation results for human-readable logging.

        Args:
            filename: Name of the DSL file
            target_weights: Target allocation weights for each symbol

        Returns:
            Formatted string for logging

        """
        if not target_weights:
            return f"📊 {filename}: No allocations"

        # Format each allocation as percentage
        allocations = []
        for symbol, weight in target_weights.items():
            percentage = float(weight) * 100
            allocations.append(f"{symbol}: {percentage:.1f}%")

        allocation_str = ", ".join(allocations)
        return f"📊 {filename}: {allocation_str}"

    def validate_signals(self, signals: list[StrategySignal]) -> None:
        """Validate generated signals.

        Args:
            signals: List of signals to validate

        Raises:
            ValueError: If signals are invalid

        """
        if not signals:
            raise ValueError("DSL strategy must generate at least one signal")

        for signal in signals:
            if not signal.symbol:
                raise ValueError("Signal symbol cannot be empty")
            if signal.action not in ["BUY", "SELL", "HOLD"]:
                raise ValueError(f"Invalid signal action: {signal.action}")

    def get_required_symbols(self) -> list[str]:
        """Get symbols required by the DSL strategy.

        Returns:
            List of required symbols (empty for DSL as it's dynamic)

        """
        # DSL strategies can reference any symbols dynamically
        # Return empty list as we can't predict them statically
        return []

    def get_strategy_summary(self) -> str:
        """Get a summary description of the DSL strategy.

        Returns:
            Strategy summary string

        """
        return f"""
        DSL Strategy Summary:

        File: {self.strategy_file}
        Type: Clojure S-expression strategy

        The DSL strategy evaluates Clojure-style expressions to produce
        portfolio allocations. The strategy file contains nested conditional
        logic using technical indicators (RSI, moving averages) to determine
        optimal asset allocation.

        Features:
        • Dynamic asset allocation based on market conditions
        • Technical indicator integration (RSI, MA, volatility)
        • Conditional logic with if/then/else expressions
        • Equal-weight and custom allocation strategies
        • Fallback to cash on evaluation errors
        """
