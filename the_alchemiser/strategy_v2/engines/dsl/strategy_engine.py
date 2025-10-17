#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine Wrapper.

Adapts the DSL engine to work with the existing StrategyEngine protocol
for integration with the multi-strategy orchestrator.
"""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.strategy_value_objects import (
    StrategySignal,
)
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine
from the_alchemiser.strategy_v2.errors import ConfigurationError, StrategyExecutionError

# Module-level constants for maintainability
DEFAULT_STRATEGY_FILE = "KLM.clj"
DEFAULT_MAX_WORKERS = 4
DEFAULT_DSL_TIMEOUT_SECONDS = 300  # 5 minutes
# Accounts for '... [N decisions]' truncation suffix when reasoning exceeds max length
REASONING_TRUNCATION_SUFFIX_LENGTH = 20


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

        # Initialize DSL engine with strategies directory as config path and real market data
        # Resolve strategies directory relative to this module to avoid depending on repo root
        strategies_path = Path(__file__).parent.parent.parent / "strategies"
        self.dsl_engine = DslEngine(
            strategy_config_path=str(strategies_path),
            market_data_service=self.market_data_port,
        )

        configured_dsl_files = self.settings.strategy.dsl_files or [self.strategy_file]
        self.logger.info(
            f"DSL Strategy Engine initialized with files: {', '.join(configured_dsl_files)}"
        )

    def generate_signals(
        self,
        timestamp: datetime,
        *,
        max_workers: int | None = None,
    ) -> list[StrategySignal]:
        """Generate strategy signals using DSL engine with thread-based parallelism."""
        try:
            correlation_id = str(uuid.uuid4())
            dsl_files, normalized_file_weights = self._resolve_dsl_files_and_weights()
            effective_max_workers = self._get_max_workers(max_workers, len(dsl_files))

            self.logger.info(f"Generating DSL signals from {len(dsl_files)} files")
            self.logger.debug(
                f"DSL evaluation details: parallelism=threads, max_workers={effective_max_workers}",
                extra={
                    "correlation_id": correlation_id,
                    "timestamp": timestamp.isoformat(),
                    "parallelism": "threads",
                    "max_workers": effective_max_workers,
                },
            )

            if len(dsl_files) <= 1:
                file_results = self._evaluate_files_sequential(
                    dsl_files, correlation_id, normalized_file_weights
                )
            else:
                file_results = self._evaluate_files_parallel(
                    dsl_files,
                    correlation_id,
                    normalized_file_weights,
                    effective_max_workers,
                )

            consolidated, decision_path = self._accumulate_results(dsl_files, file_results)
            if not consolidated:
                return self._create_fallback_signals(timestamp)

            consolidated = self._normalize_allocations(consolidated)
            signals = self._convert_to_signals(
                consolidated,
                timestamp,
                correlation_id,
                dsl_files=dsl_files,
                decision_path=decision_path,
            )

            self.logger.info(
                f"Generated {len(signals)} DSL consolidated signals",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": [s.symbol for s in signals],
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

    def _get_max_workers(
        self,
        max_workers: int | None,
        num_files: int,
    ) -> int:
        """Get worker count, applying environment overrides.

        Args:
            max_workers: Requested max workers
            num_files: Number of DSL files to process

        Returns:
            Effective max workers count

        """
        env_max_workers = os.getenv("ALCHEMISER_DSL_MAX_WORKERS")
        if env_max_workers and env_max_workers.isdigit():
            max_workers = int(env_max_workers)

        return (
            max_workers
            if max_workers is not None
            else min(num_files, os.cpu_count() or DEFAULT_MAX_WORKERS)
        )

    def _accumulate_results(
        self,
        dsl_files: list[str],
        file_results: list[
            tuple[dict[str, float] | None, str, float, float, list[dict[str, Any]] | None]
        ],
    ) -> tuple[dict[str, float], list[dict[str, Any]] | None]:
        """Accumulate per-symbol weights from DSL file evaluation results.

        Args:
            dsl_files: List of DSL files that were evaluated
            file_results: Results from file evaluations

        Returns:
            Tuple of (consolidated weights, first valid decision_path)

        """
        consolidated: dict[str, float] = {}
        decision_path: list[dict[str, Any]] | None = None

        for _f, (per_file_weights, _trace_id, _, _, file_decision_path) in zip(
            dsl_files, file_results, strict=True
        ):
            if per_file_weights is None:  # Evaluation failed
                continue
            for symbol, weight in per_file_weights.items():
                consolidated[symbol] = consolidated.get(symbol, 0.0) + weight

            # Use first valid decision path (for single-strategy cases)
            if decision_path is None and file_decision_path:
                decision_path = file_decision_path

        return consolidated, decision_path

    def _convert_to_signals(
        self,
        consolidated: dict[str, float],
        timestamp: datetime,
        correlation_id: str,
        dsl_files: list[str] | None = None,
        decision_path: list[dict[str, Any]] | None = None,
    ) -> list[StrategySignal]:
        """Convert consolidated weights to StrategySignal objects.

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
                    reasoning = self._build_decision_reasoning(
                        decision_path, primary_strategy, weight
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

    def _resolve_dsl_files_and_weights(self) -> tuple[list[str], dict[str, float]]:
        """Resolve DSL files and normalize their weights to sum to 1.0.

        Returns:
            A tuple of (dsl_files, normalized_file_weights)

        Raises:
            ConfigurationError: If DSL files don't exist or weights are invalid

        """
        dsl_files = self.settings.strategy.dsl_files or [self.strategy_file]
        dsl_allocs = self.settings.strategy.dsl_allocations or {self.strategy_file: 1.0}

        # Validate files exist
        strategies_path = Path(__file__).parent.parent.parent / "strategies"
        for f in dsl_files:
            file_path = strategies_path / f
            if not file_path.exists():
                raise ConfigurationError(f"DSL file not found: {f}", file_path=str(file_path))

        # Validate and normalize weights using Decimal for precision
        for f, w in dsl_allocs.items():
            if not isinstance(w, (int, float, Decimal)):
                raise ConfigurationError(
                    f"Invalid weight type for {f}: {type(w).__name__} (must be numeric)"
                )
            if w < 0:
                raise ConfigurationError(f"Invalid weight for {f}: {w} (must be non-negative)")

        total_alloc = sum(Decimal(str(w)) for w in dsl_allocs.values())
        if total_alloc == 0:
            total_alloc = Decimal("1.0")

        # Normalize to floats for downstream compatibility (precision maintained in calculation)
        normalized_file_weights = {
            f: float(Decimal(str(dsl_allocs.get(f, 0.0))) / total_alloc) for f in dsl_files
        }
        return dsl_files, normalized_file_weights

    def _evaluate_file(
        self,
        filename: str,
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> tuple[dict[str, float], str, float, float, list[dict[str, Any]] | None]:
        """Evaluate a single DSL file and return scaled per-symbol weights.

        Args:
            filename: DSL file to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            Tuple of (per_file_scaled_weights, trace_id, file_weight, file_sum, decision_path)

        """
        allocation, trace = self.dsl_engine.evaluate_strategy(filename, correlation_id)
        file_weight = float(normalized_file_weights.get(filename, 0.0))
        file_sum = float(sum(allocation.target_weights.values())) or 0.0

        per_file_weights: dict[str, float] = {}
        for symbol, weight in allocation.target_weights.items():
            w = float(weight)
            if w <= 0:
                continue
            per_file_weights[symbol] = file_weight * w

        # Format and log DSL evaluation results
        formatted_allocation = self._format_dsl_allocation(filename, allocation.target_weights)
        self.logger.debug(formatted_allocation)

        # Extract decision path from trace metadata
        decision_path = trace.metadata.get("decision_path") if trace.metadata else None

        return per_file_weights, trace.trace_id, file_weight, file_sum, decision_path

    def _evaluate_files_sequential(
        self,
        dsl_files: list[str],
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> list[tuple[dict[str, float] | None, str, float, float, list[dict[str, Any]] | None]]:
        """Evaluate DSL files sequentially (original behavior).

        Args:
            dsl_files: List of DSL files to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            List of evaluation results for each file (preserves order)

        """
        results: list[
            tuple[dict[str, float] | None, str, float, float, list[dict[str, Any]] | None]
        ] = []
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
                results.append((None, "", 0.0, 0.0, None))
        return results

    def _evaluate_files_parallel(
        self,
        dsl_files: list[str],
        correlation_id: str,
        normalized_file_weights: dict[str, float],
        max_workers: int,
    ) -> list[tuple[dict[str, float] | None, str, float, float, list[dict[str, Any]] | None]]:
        """Evaluate DSL files in parallel using threads while preserving deterministic order.

        Args:
            dsl_files: List of DSL files to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights
            max_workers: Maximum number of worker threads

        Returns:
            List of evaluation results for each file (preserves input order)

        """
        from concurrent.futures import TimeoutError as FuturesTimeoutError

        # Get timeout from environment or use default
        timeout_seconds = int(os.getenv("ALCHEMISER_DSL_TIMEOUT", str(DEFAULT_DSL_TIMEOUT_SECONDS)))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            try:
                # Use executor.map to preserve deterministic ordering
                return list(
                    executor.map(
                        self._evaluate_file_wrapper,
                        dsl_files,
                        [correlation_id] * len(dsl_files),
                        [normalized_file_weights] * len(dsl_files),
                        timeout=timeout_seconds,
                    )
                )
            except FuturesTimeoutError:
                self.logger.error(
                    f"DSL evaluation timeout after {timeout_seconds}s",
                    extra={
                        "correlation_id": correlation_id,
                        "file_count": len(dsl_files),
                        "timeout_seconds": timeout_seconds,
                    },
                )
                # Return None results for all files as fallback
                return [(None, "", 0.0, 0.0, None) for _ in dsl_files]

    def _evaluate_file_wrapper(
        self,
        filename: str,
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> tuple[dict[str, float] | None, str, float, float, list[dict[str, Any]] | None]:
        """Wrap _evaluate_file to handle exceptions for parallel execution.

        Args:
            filename: DSL file to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            Tuple of (per_file_scaled_weights, trace_id, file_weight, file_sum, decision_path)
            Returns (None, "", 0.0, 0.0, None) if evaluation fails

        """
        try:
            return self._evaluate_file(filename, correlation_id, normalized_file_weights)
        except (StrategyExecutionError, ValueError, RuntimeError) as e:
            self.logger.error(
                f"DSL evaluation failed for {filename}: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "filename": filename,
                    "error_type": type(e).__name__,
                },
            )
            return (None, "", 0.0, 0.0, None)

    def _normalize_allocations(self, weights: dict[str, float]) -> dict[str, float]:
        """Normalize a weights dict to sum to 1.0 using Decimal for precision.

        Args:
            weights: Dictionary of symbol weights

        Returns:
            Normalized weights dictionary summing to 1.0

        """
        total_decimal = Decimal(str(sum(weights.values())))
        if total_decimal == 0:
            total_decimal = Decimal("1.0")

        return {sym: float(Decimal(str(w)) / total_decimal) for sym, w in weights.items()}

    def _build_decision_reasoning(
        self,
        decision_path: list[dict[str, Any]] | None,
        strategy_name: str,
        weight: float,
    ) -> str:
        """Build human-readable reasoning from decision path.

        Args:
            decision_path: List of decision nodes captured during evaluation
            strategy_name: Name of the strategy
            weight: Allocation weight

        Returns:
            Human-readable reasoning string (max 1000 chars)

        """
        # Fallback if no decision path
        if not decision_path:
            return f"{strategy_name} allocation: {weight:.1%}"

        # Build reasoning from decision path
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
            reasoning = f"{strategy_name}: {decision_summary} → {weight:.1%} allocation"
        else:
            reasoning = f"{strategy_name} allocation: {weight:.1%}"

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
