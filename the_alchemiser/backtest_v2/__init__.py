"""Business Unit: backtest | Status: current.

Backtesting module for Alchemiser DSL strategies.

Provides a complete backtesting framework that evaluates existing .clj strategy
files against historical market data without requiring strategy rewrites. The
engine uses the production DSL evaluator with a historical market data adapter
for point-in-time correctness.

Key Components:
    - BacktestMarketDataAdapter: MarketDataPort implementation using Parquet files
    - BacktestEngine: Orchestrates daily strategy evaluation over date range
    - PortfolioSimulator: Tracks positions, cash, and applies slippage/commission
    - PerformanceMetrics: Calculates Sharpe, drawdown, CAGR, etc.

Example Usage:
    >>> from the_alchemiser.backtest_v2 import BacktestEngine, BacktestConfig
    >>> config = BacktestConfig(
    ...     strategy_path="strategies/core/main.clj",
    ...     start_date=datetime(2023, 1, 1),
    ...     end_date=datetime(2024, 1, 1),
    ...     initial_capital=100_000,
    ... )
    >>> engine = BacktestEngine(config)
    >>> result = engine.run()
    >>> print(result.metrics.total_return)
"""

from the_alchemiser.backtest_v2.adapters.historical_market_data import (
    BacktestMarketDataAdapter,
)
from the_alchemiser.backtest_v2.core.config import BacktestConfig
from the_alchemiser.backtest_v2.core.engine import BacktestEngine
from the_alchemiser.backtest_v2.core.metrics import PerformanceMetrics
from the_alchemiser.backtest_v2.core.portfolio_engine import (
    PortfolioBacktestConfig,
    PortfolioBacktestEngine,
    PortfolioBacktestResult,
    run_portfolio_backtest,
)
from the_alchemiser.backtest_v2.core.result import BacktestResult
from the_alchemiser.backtest_v2.core.simulator import PortfolioSimulator

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestMarketDataAdapter",
    "BacktestResult",
    "PerformanceMetrics",
    "PortfolioBacktestConfig",
    "PortfolioBacktestEngine",
    "PortfolioBacktestResult",
    "PortfolioSimulator",
    "run_portfolio_backtest",
]
