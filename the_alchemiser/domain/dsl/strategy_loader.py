"""Business Unit: strategy & signal generation; Status: current.

Strategy loader for DSL files.

Loads, parses, and evaluates strategy files written in the S-expression DSL.
Provides integration with the existing trading system infrastructure.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from the_alchemiser.strategy.dsl.errors import DSLError
from the_alchemiser.domain.dsl.evaluator import DSLEvaluator, Portfolio
from the_alchemiser.domain.dsl.optimization_config import (
    DSLOptimizationConfig,
    configure_from_environment,
)
from the_alchemiser.domain.dsl.parser import DSLParser
from the_alchemiser.shared.types.market_data_port import MarketDataPort


class StrategyLoader:
    """Loads and evaluates DSL strategy files."""

    def __init__(
        self,
        market_data_port: MarketDataPort,
        optimization_config: DSLOptimizationConfig | None = None,
        use_environment: bool = True,
    ) -> None:
        """Initialize strategy loader.

        Args:
            market_data_port: Market data access interface
            optimization_config: Explicit optimization config (overrides env if provided)
            use_environment: When True and no explicit config supplied, load from environment

        """
        self.market_data_port = market_data_port

        if optimization_config is not None:
            self._config = optimization_config
        elif use_environment:
            # Load and set global default (idempotent)
            self._config = configure_from_environment()
        else:
            self._config = DSLOptimizationConfig()

        # Parser with optional interning
        self.parser = DSLParser(enable_interning=self._config.enable_interning)
        # Evaluator with memoisation / parallel flags
        self.evaluator = DSLEvaluator(
            market_data_port,
            enable_memoisation=self._config.enable_memoisation,
            cache_maxsize=self._config.memo_cache_maxsize,
            enable_parallel=self._config.enable_parallel,
            parallel_mode=self._config.parallel_mode,
            max_workers=self._config.parallel_max_workers,
        )

    def load_strategy_file(self, file_path: str | Path) -> str:
        """Load strategy source code from file.

        Args:
            file_path: Path to strategy file

        Returns:
            Strategy source code

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read

        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Strategy file not found: {file_path}")

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise OSError(f"Failed to read strategy file {file_path}: {e}") from e

    def evaluate_strategy(self, source_code: str) -> tuple[Portfolio, list[dict[str, Any]]]:
        """Parse and evaluate strategy source code.

        Args:
            source_code: Strategy source code in DSL format

        Returns:
            Tuple of (portfolio weights, evaluation trace)

        Raises:
            DSLError: If parsing or evaluation fails

        """
        # Parse the strategy
        ast_node = self.parser.parse(source_code)

        # Evaluate to get portfolio weights
        result = self.evaluator.evaluate(ast_node)

        # Ensure result is a portfolio
        if not isinstance(result, dict):
            raise DSLError(f"Strategy must evaluate to portfolio, got {type(result)}")

        # Validate portfolio weights automatically
        self.validate_portfolio(result)

        # Get evaluation trace
        trace = self.evaluator.get_trace()

        return result, trace

    def evaluate_strategy_file(
        self, file_path: str | Path
    ) -> tuple[Portfolio, list[dict[str, Any]]]:
        """Load and evaluate strategy from file.

        Args:
            file_path: Path to strategy file

        Returns:
            Tuple of (portfolio weights, evaluation trace)

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
            DSLError: If parsing or evaluation fails

        """
        source_code = self.load_strategy_file(file_path)
        return self.evaluate_strategy(source_code)

    def save_trace(self, trace: list[dict[str, Any]], output_path: str | Path) -> None:
        """Save evaluation trace to JSON file.

        Args:
            trace: Evaluation trace from evaluator
            output_path: Path to save trace file

        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2, default=str)

    def validate_portfolio(
        self, portfolio: Portfolio, tolerance: Decimal = Decimal("1e-9")
    ) -> None:
        """Validate portfolio weights.

        Args:
            portfolio: Portfolio weights dict
            tolerance: Tolerance for weight sum validation

        Raises:
            ValueError: If portfolio is invalid

        """
        if not portfolio:
            raise ValueError("Portfolio cannot be empty")

        # Check for negative weights
        negative_weights = {
            symbol: weight for symbol, weight in portfolio.items() if weight < Decimal("0")
        }
        if negative_weights:
            raise ValueError(f"Portfolio contains negative weights: {negative_weights}")

        # Check weight sum
        total_weight = sum(portfolio.values())
        if abs(total_weight - Decimal("1.0")) > tolerance:
            raise ValueError(
                f"Portfolio weights sum to {total_weight}, expected 1.0 (tolerance {tolerance})"
            )

        # Check for invalid weights (NaN is not possible with Decimal)


class StrategyResult:
    """Container for strategy evaluation results."""

    def __init__(
        self,
        portfolio: Portfolio,
        trace: list[dict[str, Any]],
        strategy_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialize strategy result.

        Args:
            portfolio: Final portfolio weights
            trace: Evaluation trace
            strategy_name: Optional strategy name
            metadata: Optional strategy metadata

        """
        self.portfolio = portfolio
        self.trace = trace
        self.strategy_name = strategy_name
        self.metadata = metadata or {}

        # Compute summary statistics
        self.num_positions = len(portfolio)
        self.max_weight = max(portfolio.values()) if portfolio else 0.0
        self.min_weight = min(portfolio.values()) if portfolio else 0.0
        self.weight_concentration = self.max_weight if portfolio else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy_name": self.strategy_name,
            "metadata": self.metadata,
            "portfolio": self.portfolio,
            "summary": {
                "num_positions": self.num_positions,
                "max_weight": self.max_weight,
                "min_weight": self.min_weight,
                "weight_concentration": self.weight_concentration,
            },
            "trace": self.trace,
        }

    def get_top_positions(self, n: int = 5) -> list[tuple[str, Decimal]]:
        """Get top N positions by weight.

        Args:
            n: Number of top positions to return

        Returns:
            List of (symbol, weight) tuples sorted by weight descending

        """
        sorted_positions = sorted(self.portfolio.items(), key=lambda x: x[1], reverse=True)
        return sorted_positions[:n]
