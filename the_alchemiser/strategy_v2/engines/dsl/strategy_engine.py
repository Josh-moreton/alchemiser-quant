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

        # Default strategy file if not provided
        self.strategy_file = strategy_file or "KLM.clj"

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

            # Evaluate DSL strategy
            allocation, trace = self.dsl_engine.evaluate_strategy(
                self.strategy_file, correlation_id
            )

            # Debug: Log what allocation we got
            self.logger.info(
                f"DSL evaluation result: {dict(allocation.target_weights)}",
                extra={
                    "correlation_id": correlation_id,
                    "success": trace.success,
                    "total_weight": sum(allocation.target_weights.values()),
                },
            )

            # Convert StrategyAllocationDTO to StrategySignal objects
            signals = []

            for symbol, weight in allocation.target_weights.items():
                if weight > 0:  # Only create signals for positive allocations
                    signal = StrategySignal(
                        symbol=symbol,
                        action="BUY",  # DSL allocations are buy signals
                        confidence=Confidence(weight),  # Use weight as confidence
                        target_allocation=weight,
                        reasoning=f"DSL allocation: {float(weight):.1%} from {self.strategy_file}",
                        timestamp=timestamp,
                        strategy="DSL",
                        data_source=f"dsl_engine:{self.strategy_file}",
                        metadata={
                            "correlation_id": correlation_id,
                            "trace_id": trace.trace_id,
                            "dsl_file": self.strategy_file,
                            "evaluation_success": trace.success,
                            "trace_entries": len(trace.entries),
                        },
                    )
                    signals.append(signal)

            self.logger.info(
                f"Generated {len(signals)} DSL signals",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": [s.symbol for s in signals],
                    "success": trace.success,
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
            confidence=1.0,
            reasoning="DSL evaluation failed, fallback to cash position",
            timestamp=timestamp,
            strategy="DSL",
            data_source="dsl_fallback",
            metadata={"fallback": True, "dsl_file": self.strategy_file},
        )
        return [fallback_signal]

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
