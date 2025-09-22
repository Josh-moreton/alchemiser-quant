#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

DSL Strategy Engine Wrapper.

Adapts the DSL engine to work with the existing StrategyEngine protocol
for integration with the multi-strategy orchestrator.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.types.strategy_value_objects import (
    Confidence,
    StrategySignal,
)
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine, DslEngineError


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

        # Initialize DSL engine with project root as config path and real market data
        project_root = Path(__file__).parent.parent.parent.parent.parent
        self.dsl_engine = DslEngine(
            strategy_config_path=str(project_root),
            market_data_service=self.market_data_port,
        )

        self.logger.info(
            f"DSL Strategy Engine initialized with file: {self.strategy_file}"
        )

    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Generate strategy signals using DSL engine.

        Args:
            timestamp: Timestamp for signal generation

        Returns:
            List of StrategySignal objects

        """
        try:
            correlation_id = str(uuid.uuid4())

            self.logger.info(
                f"Generating DSL signals from {self.strategy_file}",
                extra={
                    "correlation_id": correlation_id,
                    "timestamp": timestamp.isoformat(),
                },
            )

            # Resolve configured files and normalized weights
            dsl_files, normalized_file_weights = self._resolve_dsl_files_and_weights()

            # Evaluate each file and accumulate per-symbol weights scaled by file allocation
            consolidated: dict[str, float] = {}
            traces: dict[str, str] = {}

            for f in dsl_files:
                try:
                    per_file_weights, trace_id, _, _ = self._evaluate_file(
                        f, correlation_id, normalized_file_weights
                    )
                except Exception as e:  # pragma: no cover - safety net
                    self.logger.error(f"DSL evaluation failed for {f}: {e}")
                    continue

                for symbol, weight in per_file_weights.items():
                    consolidated[symbol] = consolidated.get(symbol, 0.0) + weight
                traces[f] = trace_id

            # If nothing produced, fallback to CASH
            if not consolidated:
                return self._create_fallback_signals(timestamp)

            # Normalize final consolidated weights to sum to 1.0 to avoid drift
            consolidated = self._normalize_allocations(consolidated)

            # Convert to StrategySignals
            signals: list[StrategySignal] = []
            for symbol, weight in consolidated.items():
                if weight > 0:
                    signal = StrategySignal(
                        symbol=symbol,
                        action="BUY",
                        confidence=Confidence(weight),
                        target_allocation=weight,
                        reasoning=f"DSL consolidated allocation: {weight:.1%}",
                        timestamp=timestamp,
                        strategy="DSL",
                        data_source="dsl_engine:multi",
                        metadata={
                            "correlation_id": correlation_id,
                            "dsl_files": dsl_files,
                            "file_weights": normalized_file_weights,
                            "trace_ids": traces,
                        },
                    )
                    signals.append(signal)

            self.logger.info(
                f"Generated {len(signals)} DSL consolidated signals",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": [s.symbol for s in signals],
                },
            )

            return signals

        except DslEngineError as e:
            self.logger.error(f"DSL engine error: {e}")
            return self._create_fallback_signals(timestamp)
        except Exception as e:
            self.logger.error(f"Unexpected error in DSL strategy: {e}")
            return self._create_fallback_signals(timestamp)

    def _create_fallback_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Create fallback signals when DSL evaluation fails.

        Args:
            timestamp: Timestamp for signal generation

        Returns:
            List containing a single CASH signal

        """
        fallback_signal = StrategySignal(
            symbol="CASH",
            action="BUY",
            confidence=Confidence(1.0),
            reasoning="DSL evaluation failed, fallback to cash position",
            timestamp=timestamp,
            strategy="DSL",
            data_source="dsl_fallback",
            metadata={"fallback": True, "dsl_file": self.strategy_file},
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

        self.logger.info(
            f"DSL evaluation for {filename}: {dict(allocation.target_weights)}",
            extra={
                "correlation_id": correlation_id,
                "success": trace.success,
                "file_weight": file_weight,
                "file_sum": file_sum,
            },
        )

        return per_file_weights, trace.trace_id, file_weight, file_sum

    def _normalize_allocations(self, weights: dict[str, float]) -> dict[str, float]:
        """Normalize a weights dict to sum to 1.0 (if possible)."""
        total = sum(weights.values()) or 1.0
        return {sym: w / total for sym, w in weights.items()}

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
            if signal.confidence.value <= 0:
                raise ValueError(
                    f"Signal confidence must be positive, got {signal.confidence.value}"
                )
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
