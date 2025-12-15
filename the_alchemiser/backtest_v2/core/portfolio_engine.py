"""Business Unit: backtest | Status: current.

Portfolio backtest engine for multi-strategy evaluation.

Runs backtests on multiple DSL strategies with specified portfolio weights,
then aggregates the results into a single portfolio-level result. Supports
loading strategy allocations from JSON config files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from the_alchemiser.backtest_v2.core.config import BacktestConfig
from the_alchemiser.backtest_v2.core.engine import BacktestEngine
from the_alchemiser.backtest_v2.core.metrics import (
    PerformanceMetrics,
    calculate_benchmark_metrics,
    calculate_metrics,
)
from the_alchemiser.backtest_v2.core.result import BacktestResult
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

MODULE_NAME = "backtest_v2.core.portfolio_engine"


@dataclass(frozen=True)
class StrategyWeight:
    """Strategy and its portfolio weight.

    Attributes:
        strategy_path: Path to .clj strategy file
        weight: Portfolio weight (0-1)
        name: Optional display name

    """

    strategy_path: Path
    weight: Decimal
    name: str = ""

    def __post_init__(self) -> None:
        """Validate weight is in valid range."""
        if self.weight < 0 or self.weight > 1:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


@dataclass
class PortfolioBacktestConfig:
    """Configuration for portfolio-level backtesting.

    Attributes:
        strategies: List of strategy paths with weights
        start_date: Backtest start date (timezone-aware UTC)
        end_date: Backtest end date (timezone-aware UTC)
        initial_capital: Starting capital
        data_dir: Path to historical data directory
        slippage_bps: Slippage in basis points
        commission_per_share: Commission per share traded
        auto_fetch_missing: Auto-fetch missing symbol data during backtest
        auto_fetch_lookback_days: Lookback days for auto-fetch

    """

    strategies: list[StrategyWeight]
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = Decimal("100000")
    data_dir: Path = Path("data/historical")
    slippage_bps: Decimal = Decimal("5")
    commission_per_share: Decimal = Decimal("0")
    auto_fetch_missing: bool = False
    auto_fetch_lookback_days: int = 600

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.strategies:
            raise ValueError("At least one strategy is required")

        # Validate dates are timezone-aware
        if self.start_date.tzinfo is None:
            raise ValueError("start_date must be timezone-aware")
        if self.end_date.tzinfo is None:
            raise ValueError("end_date must be timezone-aware")

        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")

        # Validate weights sum close to 1
        total_weight = sum(s.weight for s in self.strategies)
        if abs(total_weight - Decimal("1")) > Decimal("0.01"):
            logger.warning(
                "Strategy weights do not sum to 1.0",
                module=MODULE_NAME,
                total_weight=str(total_weight),
            )

        # Validate data directory exists
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")

    @classmethod
    def from_config_file(
        cls,
        config_path: str | Path,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100_000,
        data_dir: str | Path = "data/historical",
        strategies_base_dir: str | Path = "the_alchemiser/strategy_v2/strategies",
        slippage_bps: float = 5,
        auto_fetch_missing: bool = False,
        auto_fetch_lookback_days: int = 600,
    ) -> PortfolioBacktestConfig:
        """Create config from a strategy.{env}.json file.

        Args:
            config_path: Path to JSON config file (e.g., strategy.dev.json)
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Starting capital
            data_dir: Path to historical data directory
            strategies_base_dir: Base directory for strategy files
            slippage_bps: Slippage in basis points
            auto_fetch_missing: Auto-fetch missing symbol data during backtest
            auto_fetch_lookback_days: Lookback days for auto-fetch

        Returns:
            PortfolioBacktestConfig

        Example:
            >>> config = PortfolioBacktestConfig.from_config_file(
            ...     "the_alchemiser/config/strategy.dev.json",
            ...     start_date=datetime(2024, 1, 1, tzinfo=UTC),
            ...     end_date=datetime(2024, 12, 1, tzinfo=UTC),
            ... )

        """
        config_path = Path(config_path)
        strategies_base_dir = Path(strategies_base_dir)

        with config_path.open() as f:
            config_data = json.load(f)

        strategies = []
        allocations = config_data.get("allocations", {})

        for file_path, weight in allocations.items():
            full_path = strategies_base_dir / file_path
            strategies.append(
                StrategyWeight(
                    strategy_path=full_path,
                    weight=Decimal(str(weight)),
                    name=file_path,
                )
            )

        return cls(
            strategies=strategies,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal(str(initial_capital)),
            data_dir=Path(data_dir),
            slippage_bps=Decimal(str(slippage_bps)),
            auto_fetch_missing=auto_fetch_missing,
            auto_fetch_lookback_days=auto_fetch_lookback_days,
        )


@dataclass
class StrategyBacktestResult:
    """Result for a single strategy in the portfolio.

    Attributes:
        name: Strategy name/path
        weight: Portfolio weight
        result: Full backtest result
        weighted_equity: Equity curve scaled by weight

    """

    name: str
    weight: Decimal
    result: BacktestResult
    weighted_equity: pd.DataFrame


@dataclass
class PortfolioBacktestResult:
    """Complete results from a portfolio backtest.

    Attributes:
        config_summary: Summary of portfolio configuration
        strategy_results: Individual results for each strategy
        equity_curve: Combined portfolio equity curve
        benchmark_curve: SPY benchmark curve
        metrics: Portfolio-level performance metrics
        benchmark_metrics: Benchmark metrics for comparison
        errors: Aggregated errors from all strategies

    """

    config_summary: dict[str, object]
    strategy_results: list[StrategyBacktestResult]
    equity_curve: pd.DataFrame
    benchmark_curve: pd.DataFrame
    metrics: PerformanceMetrics
    benchmark_metrics: PerformanceMetrics
    errors: list[dict[str, object]] = field(default_factory=list)

    @property
    def total_return(self) -> Decimal:
        """Total portfolio return."""
        return self.metrics.total_return

    @property
    def sharpe_ratio(self) -> float:
        """Portfolio Sharpe ratio."""
        return self.metrics.sharpe_ratio

    @property
    def max_drawdown(self) -> Decimal:
        """Maximum portfolio drawdown."""
        return self.metrics.max_drawdown

    @property
    def alpha(self) -> float:
        """Alpha vs benchmark."""
        return float(self.total_return - self.benchmark_metrics.total_return)

    def to_dict(self) -> dict[str, object]:
        """Convert result to dictionary for serialization."""
        return {
            "config": self.config_summary,
            "portfolio_metrics": {
                "total_return": str(self.metrics.total_return),
                "cagr": str(self.metrics.cagr),
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "sortino_ratio": self.metrics.sortino_ratio,
                "max_drawdown": str(self.metrics.max_drawdown),
                "max_drawdown_duration_days": self.metrics.max_drawdown_duration_days,
                "volatility": str(self.metrics.volatility),
                "win_rate": self.metrics.win_rate,
                "profit_factor": self.metrics.profit_factor,
            },
            "benchmark_metrics": {
                "total_return": str(self.benchmark_metrics.total_return),
                "cagr": str(self.benchmark_metrics.cagr),
                "sharpe_ratio": self.benchmark_metrics.sharpe_ratio,
                "max_drawdown": str(self.benchmark_metrics.max_drawdown),
            },
            "alpha": self.alpha,
            "strategy_results": [
                {
                    "name": sr.name,
                    "weight": str(sr.weight),
                    "total_return": str(sr.result.total_return),
                    "sharpe": sr.result.sharpe_ratio,
                    "max_drawdown": str(sr.result.max_drawdown),
                    "error_count": len(sr.result.errors),
                }
                for sr in self.strategy_results
            ],
            "error_count": len(self.errors),
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "PORTFOLIO BACKTEST RESULTS",
            "=" * 70,
            f"Strategies: {len(self.strategy_results)}",
            f"Period: {self.config_summary.get('start_date', 'N/A')} to {self.config_summary.get('end_date', 'N/A')}",
            f"Initial Capital: ${self.config_summary.get('initial_capital', 'N/A'):,.2f}",
            "",
            "PORTFOLIO PERFORMANCE",
            "-" * 50,
            f"Total Return: {float(self.metrics.total_return) * 100:.2f}%",
            f"CAGR: {float(self.metrics.cagr) * 100:.2f}%",
            f"Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}",
            f"Sortino Ratio: {self.metrics.sortino_ratio:.2f}",
            f"Max Drawdown: {float(self.metrics.max_drawdown) * 100:.2f}%",
            f"Max DD Duration: {self.metrics.max_drawdown_duration_days} days",
            f"Volatility (Ann.): {float(self.metrics.volatility) * 100:.2f}%",
            "",
            "BENCHMARK COMPARISON (SPY)",
            "-" * 50,
            f"Benchmark Return: {float(self.benchmark_metrics.total_return) * 100:.2f}%",
            f"Alpha: {self.alpha * 100:.2f}%",
            f"Benchmark Sharpe: {self.benchmark_metrics.sharpe_ratio:.2f}",
            "",
            "STRATEGY BREAKDOWN",
            "-" * 50,
            f"{'Strategy':<30} {'Weight':>8} {'Return':>10} {'Sharpe':>8} {'Errors':>8}",
            "-" * 50,
        ]

        for sr in self.strategy_results:
            name = sr.name[:28] + ".." if len(sr.name) > 30 else sr.name
            lines.append(
                f"{name:<30} {float(sr.weight) * 100:>7.1f}% "
                f"{float(sr.result.total_return) * 100:>9.2f}% "
                f"{sr.result.sharpe_ratio:>7.2f} "
                f"{len(sr.result.errors):>8}"
            )

        lines.extend(
            [
                "",
                f"Total Errors: {len(self.errors)}",
                "=" * 70,
            ]
        )
        return "\n".join(lines)


class PortfolioBacktestEngine:
    """Engine for backtesting a portfolio of DSL strategies.

    Runs individual backtests for each strategy, then combines the
    equity curves using the specified weights to produce portfolio-level
    results.

    Example:
        >>> config = PortfolioBacktestConfig.from_config_file(
        ...     "the_alchemiser/config/strategy.dev.json",
        ...     start_date=datetime(2024, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 12, 1, tzinfo=UTC),
        ... )
        >>> engine = PortfolioBacktestEngine(config)
        >>> result = engine.run()
        >>> print(result.summary())

    """

    def __init__(self, config: PortfolioBacktestConfig) -> None:
        """Initialize portfolio backtest engine.

        Args:
            config: Portfolio backtest configuration

        """
        self.config = config

        logger.info(
            "PortfolioBacktestEngine initialized",
            module=MODULE_NAME,
            strategy_count=len(config.strategies),
            start=config.start_date.isoformat(),
            end=config.end_date.isoformat(),
            initial_capital=str(config.initial_capital),
        )

    def _run_single_strategy(
        self,
        strategy: StrategyWeight,
    ) -> BacktestResult | None:
        """Run backtest for a single strategy.

        Args:
            strategy: Strategy path and weight

        Returns:
            BacktestResult or None if failed

        """
        logger.info(
            "Running strategy backtest",
            module=MODULE_NAME,
            strategy=str(strategy.strategy_path),
            weight=str(strategy.weight),
        )

        try:
            strategy_config = BacktestConfig(
                strategy_path=strategy.strategy_path,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                initial_capital=self.config.initial_capital,
                data_dir=self.config.data_dir,
                slippage_bps=self.config.slippage_bps,
                commission_per_share=self.config.commission_per_share,
                auto_fetch_missing=self.config.auto_fetch_missing,
                auto_fetch_lookback_days=self.config.auto_fetch_lookback_days,
            )

            engine = BacktestEngine(strategy_config)
            result = engine.run()

            logger.info(
                "Strategy backtest completed",
                module=MODULE_NAME,
                strategy=str(strategy.strategy_path),
                total_return=str(result.total_return),
                sharpe=result.sharpe_ratio,
            )

            return result

        except Exception as e:
            logger.error(
                "Strategy backtest failed",
                module=MODULE_NAME,
                strategy=str(strategy.strategy_path),
                error=str(e),
            )
            return None

    def _aggregate_equity_curves(
        self,
        strategy_results: list[StrategyBacktestResult],
    ) -> pd.DataFrame:
        """Aggregate strategy equity curves by weight.

        Each strategy's equity curve is scaled by its weight, then
        summed to produce the portfolio equity curve.

        Args:
            strategy_results: List of strategy results with weights

        Returns:
            DataFrame with combined 'portfolio_value' column

        """
        if not strategy_results:
            return pd.DataFrame(columns=["portfolio_value", "close"])

        # Get all unique dates from all strategies
        all_dates: set[datetime] = set()
        for sr in strategy_results:
            if not sr.result.equity_curve.empty:
                all_dates.update(sr.result.equity_curve.index.tolist())

        if not all_dates:
            return pd.DataFrame(columns=["portfolio_value", "close"])

        sorted_dates = sorted(all_dates)
        initial_capital = float(self.config.initial_capital)

        # Build portfolio equity curve
        portfolio_values = []

        for date in sorted_dates:
            portfolio_value = Decimal("0")

            for sr in strategy_results:
                ec = sr.result.equity_curve
                if ec.empty:
                    # Use initial capital portion if no data
                    strategy_capital = initial_capital * float(sr.weight)
                    portfolio_value += Decimal(str(strategy_capital))
                elif date in ec.index:
                    strategy_value = Decimal(str(ec.loc[date, "portfolio_value"]))
                    # Scale by weight (already applied in weighted_equity)
                    portfolio_value += strategy_value * sr.weight
                else:
                    # Forward fill: find last available value
                    prior_dates = [d for d in ec.index if d <= date]
                    if prior_dates:
                        last_value = Decimal(str(ec.loc[max(prior_dates), "portfolio_value"]))
                        portfolio_value += last_value * sr.weight
                    else:
                        strategy_capital = initial_capital * float(sr.weight)
                        portfolio_value += Decimal(str(strategy_capital))

            portfolio_values.append(float(portfolio_value))

        df = pd.DataFrame(
            {"portfolio_value": portfolio_values, "close": portfolio_values},
            index=pd.DatetimeIndex(sorted_dates),
        )
        df.index.name = "date"
        return df

    def run(self) -> PortfolioBacktestResult:
        """Run portfolio backtest.

        Executes backtest for each strategy, combines results using
        portfolio weights, and computes aggregate metrics.

        Returns:
            PortfolioBacktestResult with complete portfolio analysis

        """
        logger.info(
            "Starting portfolio backtest",
            module=MODULE_NAME,
            strategy_count=len(self.config.strategies),
        )

        strategy_results: list[StrategyBacktestResult] = []
        all_errors: list[dict[str, object]] = []
        benchmark_curve: pd.DataFrame | None = None

        # Run each strategy
        for i, strategy in enumerate(self.config.strategies):
            logger.info(
                "Processing strategy",
                module=MODULE_NAME,
                index=i + 1,
                total=len(self.config.strategies),
                strategy=strategy.name or str(strategy.strategy_path),
            )

            strategy_result = self._run_single_strategy(strategy)

            if strategy_result is not None:
                # Store first benchmark curve (they should all be the same)
                if benchmark_curve is None and not strategy_result.benchmark_curve.empty:
                    benchmark_curve = strategy_result.benchmark_curve

                # Add errors with strategy context
                for error in strategy_result.errors:
                    error_with_context = {
                        **error,
                        "strategy": strategy.name or str(strategy.strategy_path),
                    }
                    all_errors.append(error_with_context)

                # Create weighted equity curve
                weighted_equity = strategy_result.equity_curve.copy()
                if not weighted_equity.empty:
                    weighted_equity["portfolio_value"] = weighted_equity["portfolio_value"] * float(
                        strategy.weight
                    )

                strategy_results.append(
                    StrategyBacktestResult(
                        name=strategy.name or str(strategy.strategy_path),
                        weight=strategy.weight,
                        result=strategy_result,
                        weighted_equity=weighted_equity,
                    )
                )

        # Aggregate equity curves
        portfolio_equity = self._aggregate_equity_curves(strategy_results)

        # Calculate portfolio metrics
        portfolio_metrics = calculate_metrics(portfolio_equity, [])

        # Use stored benchmark or create empty
        if benchmark_curve is None:
            benchmark_curve = pd.DataFrame(columns=["close"])

        benchmark_metrics = calculate_benchmark_metrics(benchmark_curve)

        # Build config summary
        config_summary = {
            "start_date": self.config.start_date.isoformat(),
            "end_date": self.config.end_date.isoformat(),
            "initial_capital": float(self.config.initial_capital),
            "slippage_bps": float(self.config.slippage_bps),
            "strategy_count": len(self.config.strategies),
            "strategies": [
                {
                    "path": str(s.strategy_path),
                    "weight": float(s.weight),
                    "name": s.name,
                }
                for s in self.config.strategies
            ],
        }

        portfolio_result = PortfolioBacktestResult(
            config_summary=config_summary,
            strategy_results=strategy_results,
            equity_curve=portfolio_equity,
            benchmark_curve=benchmark_curve,
            metrics=portfolio_metrics,
            benchmark_metrics=benchmark_metrics,
            errors=all_errors,
        )

        logger.info(
            "Portfolio backtest completed",
            module=MODULE_NAME,
            total_return=str(portfolio_result.total_return),
            sharpe=portfolio_result.sharpe_ratio,
            max_dd=str(portfolio_result.max_drawdown),
            strategies_completed=len(strategy_results),
            total_errors=len(all_errors),
        )

        return portfolio_result


def run_portfolio_backtest(
    config_path: str | Path,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100_000,
    data_dir: str | Path = "data/historical",
    strategies_base_dir: str | Path = "the_alchemiser/strategy_v2/strategies",
    slippage_bps: float = 5,
) -> PortfolioBacktestResult:
    """Run a portfolio backtest from a config file.

    Args:
        config_path: Path to strategy config JSON file
        start_date: Backtest start date (timezone-aware)
        end_date: Backtest end date (timezone-aware)
        initial_capital: Starting capital
        data_dir: Path to historical data directory
        strategies_base_dir: Base directory for strategy files
        slippage_bps: Slippage in basis points

    Returns:
        PortfolioBacktestResult with complete portfolio analysis

    Example:
        >>> from datetime import datetime, UTC
        >>> result = run_portfolio_backtest(
        ...     "the_alchemiser/config/strategy.dev.json",
        ...     start_date=datetime(2024, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 12, 1, tzinfo=UTC),
        ... )
        >>> print(result.summary())

    """
    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=UTC)

    config = PortfolioBacktestConfig.from_config_file(
        config_path=config_path,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        data_dir=data_dir,
        strategies_base_dir=strategies_base_dir,
        slippage_bps=slippage_bps,
    )

    engine = PortfolioBacktestEngine(config)
    return engine.run()
