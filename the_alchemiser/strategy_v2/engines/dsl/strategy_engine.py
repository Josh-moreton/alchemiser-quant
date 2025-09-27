#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine Wrapper.

Adapts the DSL engine to work with the existing StrategyEngine protocol
for integration with the multi-strategy orchestrator.
"""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, cast

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.strategy_value_objects import (
    StrategySignal,
)
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine


class DslStrategyEngine:
    """DSL Strategy Engine wrapper implementing StrategyEngine protocol.

    This wrapper adapts the DSL engine to work with the existing multi-strategy
    orchestration system by implementing the StrategyEngine protocol.
    """

    def __init__(
        self, market_data_port: MarketDataPort, strategy_file: str | None = None
    ) -> None:
        """Initialize DSL strategy engine.

        Args:
            market_data_port: Market data provider (required by protocol, not used in DSL)
            strategy_file: Optional path to .clj strategy file (defaults to klm original.clj)

        """
        self.market_data_port = market_data_port  # Required by protocol
        self.logger = get_logger(__name__)

        # Default strategy file if not provided (single-file fallback)
        self.strategy_file = strategy_file or "KLM.clj"

        # Load settings to support multi-file execution
        try:
            self.settings = Settings()
        except Exception:
            # Minimal fallback settings if config load fails
            self.settings = Settings(strategy=Settings().strategy)

        # Initialize DSL engine with strategies directory as config path and real market data
        project_root = Path(__file__).parent.parent.parent.parent.parent
        strategies_path = project_root / "the_alchemiser" / "strategy_v2" / "strategies"
        self.dsl_engine = DslEngine(
            strategy_config_path=str(strategies_path),
            market_data_service=self.market_data_port,
        )

        self.logger.info(
            f"DSL Strategy Engine initialized with file: {self.strategy_file}"
        )

    def generate_signals(
        self,
        timestamp: datetime,
        *,
        parallelism: Literal["none", "threads", "processes"] = "none",
        max_workers: int | None = None,
    ) -> list[StrategySignal]:
        """Generate strategy signals using DSL engine with optional parallelism."""
        try:
            correlation_id = str(uuid.uuid4())
            dsl_files, normalized_file_weights = self._resolve_dsl_files_and_weights()
            parallelism, effective_max_workers = self._get_parallelism_and_workers(
                parallelism, max_workers, len(dsl_files)
            )

            self.logger.info(f"Generating DSL signals from {len(dsl_files)} files")
            self.logger.debug(
                f"DSL evaluation details: parallelism={parallelism}, max_workers={effective_max_workers}",
                extra={
                    "correlation_id": correlation_id,
                    "timestamp": timestamp.isoformat(),
                    "parallelism": parallelism,
                    "max_workers": effective_max_workers,
                },
            )

            if parallelism == "none" or len(dsl_files) <= 1:
                file_results = self._evaluate_files_sequential(
                    dsl_files, correlation_id, normalized_file_weights
                )
            else:
                file_results = self._evaluate_files_parallel(
                    dsl_files,
                    correlation_id,
                    normalized_file_weights,
                    parallelism,
                    effective_max_workers,
                )

            consolidated = self._accumulate_results(dsl_files, file_results)
            if not consolidated:
                return self._create_fallback_signals(timestamp)

            consolidated = self._normalize_allocations(consolidated)
            signals = self._convert_to_signals(
                consolidated, timestamp, correlation_id, dsl_files
            )

            self.logger.info(
                f"Generated {len(signals)} DSL consolidated signals",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": [s.symbol for s in signals],
                },
            )

            return signals

        except Exception as e:
            self.logger.error(f"DSL strategy error: {e}")
            return self._create_fallback_signals(timestamp)

    def _get_parallelism_and_workers(
        self,
        parallelism: Literal["none", "threads", "processes"],
        max_workers: int | None,
        num_files: int,
    ) -> tuple[Literal["none", "threads", "processes"], int]:
        """Get parallelism mode and worker count, applying environment overrides.

        Args:
            parallelism: Requested parallelism mode
            max_workers: Requested max workers
            num_files: Number of DSL files to process

        Returns:
            Tuple of (effective_parallelism, effective_max_workers)

        """
        # Check environment overrides
        env_parallelism = os.getenv("ALCHEMISER_DSL_PARALLELISM")
        allowed_parallelism: tuple[Literal["none", "threads", "processes"], ...] = (
            "none",
            "threads",
            "processes",
        )
        if env_parallelism in allowed_parallelism:
            parallelism = cast(Literal["none", "threads", "processes"], env_parallelism)

        env_max_workers = os.getenv("ALCHEMISER_DSL_MAX_WORKERS")
        if env_max_workers and env_max_workers.isdigit():
            max_workers = int(env_max_workers)

        effective_max_workers = (
            max_workers
            if max_workers is not None
            else min(num_files, os.cpu_count() or 4)
        )
        return parallelism, effective_max_workers

    def _accumulate_results(
        self,
        dsl_files: list[str],
        file_results: list[tuple[dict[str, float] | None, str, float, float]],
    ) -> dict[str, float]:
        """Accumulate per-symbol weights from DSL file evaluation results.

        Args:
            dsl_files: List of DSL files that were evaluated
            file_results: Results from file evaluations

        Returns:
            Dictionary mapping symbols to consolidated weights

        """
        consolidated: dict[str, float] = {}
        for _f, (per_file_weights, _trace_id, _, _) in zip(
            dsl_files, file_results, strict=True
        ):
            if per_file_weights is None:  # Evaluation failed
                continue
            for symbol, weight in per_file_weights.items():
                consolidated[symbol] = consolidated.get(symbol, 0.0) + weight
        return consolidated

    def _convert_to_signals(
        self,
        consolidated: dict[str, float],
        timestamp: datetime,
        correlation_id: str,
        file_results: (
            list[tuple[dict[str, float] | None, str, float, float]] | None
        ) = None,
        dsl_files: list[str] | None = None,
    ) -> list[StrategySignal]:
        """Convert consolidated weights to StrategySignal objects.

        Args:
            consolidated: Dictionary mapping symbols to weights
            timestamp: Timestamp for signal generation
            correlation_id: Correlation ID for tracing
            dsl_files: Optional list of DSL files for attribution

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
                    strategy_display = (
                        f"{primary_strategy} (+{len(strategy_names) - 1} others)"
                    )
                    reasoning = f"Multi-strategy allocation from {', '.join(strategy_names)}: {weight:.1%}"
                else:
                    strategy_display = primary_strategy
                    reasoning = f"{primary_strategy} allocation: {weight:.1%}"

                signals.append(
                    StrategySignal(
                        symbol=symbol,
                        action="BUY",
                        target_allocation=weight,
                        reasoning=reasoning,
                        timestamp=timestamp,
                        strategy=strategy_display,
                        data_source="dsl_engine:multi",
                        correlation_id=correlation_id,
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

        fallback_signal = StrategySignal(
            symbol="CASH",
            action="BUY",
            reasoning=f"{strategy_name} evaluation failed, fallback to cash position",
            timestamp=timestamp,
            strategy=strategy_name,
            data_source="dsl_fallback",
            fallback=True,
            dsl_file=self.strategy_file,
        )
        return [fallback_signal]

    def _resolve_dsl_files_and_weights(self) -> tuple[list[str], dict[str, float]]:
        """Resolve DSL files and normalize their weights to sum to 1.0.

        Returns:
            A tuple of (dsl_files, normalized_file_weights)

        """
        dsl_files = self.settings.strategy.dsl_files or [self.strategy_file]
        dsl_allocs = self.settings.strategy.dsl_allocations or {self.strategy_file: 1.0}
        total_alloc = sum(float(w) for w in dsl_allocs.values()) or 1.0
        normalized_file_weights = {
            f: (float(dsl_allocs.get(f, 0.0)) / total_alloc) for f in dsl_files
        }
        return dsl_files, normalized_file_weights

    def _evaluate_file(
        self,
        filename: str,
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> tuple[dict[str, float], str, float, float]:
        """Evaluate a single DSL file and return scaled per-symbol weights.

        Args:
            filename: DSL file to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            Tuple of (per_file_scaled_weights, trace_id, file_weight, file_sum)

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
        formatted_allocation = self._format_dsl_allocation(
            filename, allocation.target_weights
        )
        self.logger.debug(formatted_allocation)

        return per_file_weights, trace.trace_id, file_weight, file_sum

    def _evaluate_files_sequential(
        self,
        dsl_files: list[str],
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> list[tuple[dict[str, float] | None, str, float, float]]:
        """Evaluate DSL files sequentially (original behavior).

        Args:
            dsl_files: List of DSL files to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            List of evaluation results for each file (preserves order)

        """
        results: list[tuple[dict[str, float] | None, str, float, float]] = []
        for f in dsl_files:
            try:
                result = self._evaluate_file(f, correlation_id, normalized_file_weights)
                results.append(result)
            except Exception as e:  # pragma: no cover - safety net
                self.logger.error(f"DSL evaluation failed for {f}: {e}")
                results.append((None, "", 0.0, 0.0))
        return results

    def _evaluate_files_parallel(
        self,
        dsl_files: list[str],
        correlation_id: str,
        normalized_file_weights: dict[str, float],
        parallelism: Literal["threads", "processes"],
        max_workers: int,
    ) -> list[tuple[dict[str, float] | None, str, float, float]]:
        """Evaluate DSL files in parallel while preserving deterministic order.

        Args:
            dsl_files: List of DSL files to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights
            parallelism: Either "threads" or "processes"
            max_workers: Maximum number of worker threads/processes

        Returns:
            List of evaluation results for each file (preserves input order)

        """
        executor_class = (
            ThreadPoolExecutor if parallelism == "threads" else ProcessPoolExecutor
        )

        with executor_class(max_workers=max_workers) as executor:
            # Use executor.map to preserve deterministic ordering
            return list(
                executor.map(
                    self._evaluate_file_wrapper,
                    dsl_files,
                    [correlation_id] * len(dsl_files),
                    [normalized_file_weights] * len(dsl_files),
                )
            )

    def _evaluate_file_wrapper(
        self,
        filename: str,
        correlation_id: str,
        normalized_file_weights: dict[str, float],
    ) -> tuple[dict[str, float] | None, str, float, float]:
        """Wrap _evaluate_file to handle exceptions for parallel execution.

        Args:
            filename: DSL file to evaluate
            correlation_id: Correlation ID for tracing
            normalized_file_weights: Precomputed normalized file weights

        Returns:
            Tuple of (per_file_scaled_weights, trace_id, file_weight, file_sum)
            Returns (None, "", 0.0, 0.0) if evaluation fails

        """
        try:
            return self._evaluate_file(
                filename, correlation_id, normalized_file_weights
            )
        except Exception as e:  # pragma: no cover - safety net
            self.logger.error(
                f"DSL evaluation failed for {filename}: {e}",
                extra={
                    "correlation_id": correlation_id,
                },
            )
            return (None, "", 0.0, 0.0)

    def _normalize_allocations(self, weights: dict[str, float]) -> dict[str, float]:
        """Normalize a weights dict to sum to 1.0 (if possible)."""
        total = sum(weights.values()) or 1.0
        return {sym: w / total for sym, w in weights.items()}

    def _format_dsl_allocation(
        self, filename: str, target_weights: dict[str, Decimal]
    ) -> str:
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
