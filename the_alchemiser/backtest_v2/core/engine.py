"""Business Unit: backtest | Status: current.

Backtest engine for DSL strategy evaluation.

Orchestrates the complete backtest workflow: loads strategy, iterates over
trading days, evaluates DSL at each point-in-time, and simulates portfolio
rebalancing.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

import pandas as pd

from the_alchemiser.backtest_v2.adapters.historical_market_data import (
    BacktestMarketDataAdapter,
)
from the_alchemiser.backtest_v2.core.config import BacktestConfig
from the_alchemiser.backtest_v2.core.metrics import (
    calculate_benchmark_metrics,
    calculate_metrics,
)
from the_alchemiser.backtest_v2.core.result import BacktestResult
from the_alchemiser.backtest_v2.core.simulator import PortfolioSimulator
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.strategy_v2.engines.dsl.dsl_evaluator import DslEvaluator
from the_alchemiser.strategy_v2.engines.dsl.sexpr_parser import SexprParser
from the_alchemiser.strategy_v2.indicators.indicator_service import IndicatorService

logger = get_logger(__name__)

# Module constant
MODULE_NAME = "backtest_v2.core.engine"

# Benchmark symbol
BENCHMARK_SYMBOL: Final[str] = "SPY"


class BacktestEngine:
    """Engine for backtesting DSL strategies against historical data.

    Evaluates existing .clj strategy files at each trading day in the
    backtest period, simulates portfolio rebalancing with transaction
    costs, and computes performance metrics.

    Attributes:
        config: Backtest configuration
        parser: S-expression parser for DSL files
        market_data: Historical market data adapter
        simulator: Portfolio simulator
        errors: List of errors encountered during backtest

    Example:
        >>> config = BacktestConfig(
        ...     strategy_path=Path("strategies/core/main.clj"),
        ...     start_date=datetime(2023, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 1, 1, tzinfo=UTC),
        ... )
        >>> engine = BacktestEngine(config)
        >>> result = engine.run()
        >>> print(result.summary())

    """

    def __init__(self, config: BacktestConfig) -> None:
        """Initialize backtest engine.

        Args:
            config: Backtest configuration

        """
        self.config = config
        self.parser = SexprParser()
        self.errors: list[dict[str, object]] = []

        # Initialize market data adapter (start with end date, will update per day)
        self.market_data = BacktestMarketDataAdapter(
            data_dir=config.data_dir,
            as_of=config.end_date,
        )

        # Initialize simulator
        self.simulator = PortfolioSimulator(
            market_data=self.market_data,
            slippage_bps=config.slippage_bps,
            commission_per_share=config.commission_per_share,
        )

        logger.info(
            "BacktestEngine initialized",
            module=MODULE_NAME,
            strategy=str(config.strategy_path),
            start=config.start_date.isoformat(),
            end=config.end_date.isoformat(),
            initial_capital=str(config.initial_capital),
        )

    def _get_trading_days(self) -> list[datetime]:
        """Get list of trading days in the backtest period.

        Uses SPY trading days as the reference calendar.

        Returns:
            List of trading dates (timezone-aware UTC)

        """
        # Load SPY data to get trading calendar
        try:
            spy_df = self.market_data._load_symbol_data(BENCHMARK_SYMBOL)

            # Filter to date range
            mask = (spy_df.index >= self.config.start_date) & (spy_df.index <= self.config.end_date)
            trading_days = spy_df[mask].index.tolist()

            logger.info(
                "Trading days determined",
                module=MODULE_NAME,
                count=len(trading_days),
                first=str(trading_days[0]) if trading_days else "N/A",
                last=str(trading_days[-1]) if trading_days else "N/A",
            )

            return list(trading_days)
        except Exception as e:
            logger.error(
                "Failed to get trading days from SPY",
                module=MODULE_NAME,
                error=str(e),
            )
            raise ValueError(f"Cannot determine trading days: {e}") from e

    def _evaluate_strategy(
        self,
        date: datetime,
        ast: object,
        correlation_id: str,
    ) -> dict[str, Decimal] | None:
        """Evaluate strategy DSL at a specific date.

        Args:
            date: Evaluation date (point-in-time)
            ast: Parsed AST from strategy file
            correlation_id: Correlation ID for tracing

        Returns:
            Target weights dict or None if evaluation failed

        """
        try:
            # Update market data adapter to this date
            self.market_data.set_as_of(date)

            # Create indicator service with historical data
            indicator_service = IndicatorService(self.market_data)

            # Create evaluator
            evaluator = DslEvaluator(indicator_service=indicator_service, event_bus=None)

            # Evaluate AST
            allocation, _trace = evaluator.evaluate(ast, correlation_id)  # type: ignore[arg-type]

            logger.debug(
                "Strategy evaluated",
                module=MODULE_NAME,
                date=date.isoformat(),
                symbols=list(allocation.target_weights.keys()),
                correlation_id=correlation_id,
            )

            return allocation.target_weights

        except Exception as e:
            error_record: dict[str, object] = {
                "date": date.isoformat(),
                "error": str(e),
                "error_type": type(e).__name__,
                "correlation_id": correlation_id,
            }
            self.errors.append(error_record)

            logger.warning(
                "Strategy evaluation failed",
                module=MODULE_NAME,
                date=date.isoformat(),
                error=str(e),
                correlation_id=correlation_id,
            )

            return None

    def _generate_benchmark_curve(
        self,
        trading_days: list[datetime],
    ) -> pd.DataFrame:
        """Generate SPY benchmark equity curve.

        Args:
            trading_days: List of trading dates

        Returns:
            DataFrame with 'close' column indexed by date

        """
        closes = []
        dates = []

        for day in trading_days:
            price = self.market_data.get_close_price_on_date(BENCHMARK_SYMBOL, day)
            if price is not None:
                closes.append(price)
                dates.append(day)

        if not closes:
            return pd.DataFrame(columns=["close"])

        # Normalize to start at same value as portfolio
        initial_capital = float(self.config.initial_capital)
        initial_price = closes[0]
        normalized = [(c / initial_price) * initial_capital for c in closes]

        df = pd.DataFrame(
            {"close": normalized},
            index=pd.DatetimeIndex(dates),
        )
        df.index.name = "date"
        return df

    def run(self) -> BacktestResult:
        """Run the backtest.

        Iterates over each trading day, evaluates the strategy,
        and simulates portfolio rebalancing.

        Returns:
            BacktestResult with complete results and metrics

        """
        logger.info(
            "Starting backtest",
            module=MODULE_NAME,
            strategy=str(self.config.strategy_path),
        )

        # Parse strategy file
        try:
            ast = self.parser.parse_file(
                str(self.config.strategy_path),
                correlation_id=f"backtest-{uuid.uuid4().hex[:8]}",
            )
        except Exception as e:
            logger.error(
                "Failed to parse strategy file",
                module=MODULE_NAME,
                error=str(e),
            )
            raise ValueError(f"Failed to parse strategy: {e}") from e

        # Get trading days
        trading_days = self._get_trading_days()
        if not trading_days:
            raise ValueError("No trading days in specified date range")

        # Initialize simulator
        self.simulator.initialize(self.config.initial_capital)

        # Track allocations
        allocation_history: dict[datetime, dict[str, Decimal]] = {}

        # Main backtest loop
        total_days = len(trading_days)
        for i, date in enumerate(trading_days):
            correlation_id = f"bt-{date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"

            # Log progress every 20 days
            if i % 20 == 0:
                logger.info(
                    "Backtest progress",
                    module=MODULE_NAME,
                    day=i + 1,
                    total=total_days,
                    date=date.isoformat(),
                    pct=f"{(i / total_days) * 100:.1f}%",
                )

            # Evaluate strategy
            target_weights = self._evaluate_strategy(date, ast, correlation_id)

            if target_weights:
                # Record allocation
                allocation_history[date] = target_weights

                # Rebalance portfolio
                self.simulator.rebalance(date, target_weights)
            else:
                # Mark to market without trading (strategy evaluation failed)
                self.simulator.mark_to_market(date)

        # Generate results
        equity_curve = self.simulator.get_equity_curve()
        trades = self.simulator.get_trades()

        # Generate benchmark curve
        benchmark_curve = self._generate_benchmark_curve(trading_days)

        # Calculate metrics
        strategy_metrics = calculate_metrics(equity_curve, trades)
        benchmark_metrics = calculate_benchmark_metrics(benchmark_curve)

        # Create config summary
        config_summary = {
            "strategy_path": str(self.config.strategy_path),
            "start_date": self.config.start_date.isoformat(),
            "end_date": self.config.end_date.isoformat(),
            "initial_capital": float(self.config.initial_capital),
            "slippage_bps": float(self.config.slippage_bps),
            "commission_per_share": float(self.config.commission_per_share),
            "trading_days": len(trading_days),
            "total_trades": len(trades),
        }

        result = BacktestResult(
            config_summary=config_summary,
            equity_curve=equity_curve,
            benchmark_curve=benchmark_curve,
            allocation_history=allocation_history,
            trades=trades,
            metrics=strategy_metrics,
            strategy_metrics=strategy_metrics,
            benchmark_metrics=benchmark_metrics,
            errors=self.errors,
        )

        logger.info(
            "Backtest completed",
            module=MODULE_NAME,
            total_return=str(result.total_return),
            sharpe=result.sharpe_ratio,
            max_dd=str(result.max_drawdown),
            total_trades=len(trades),
            errors=len(self.errors),
        )

        return result


def run_backtest(
    strategy_path: str | Path,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100_000,
    data_dir: str | Path = "data/historical",
    slippage_bps: float = 5,
) -> BacktestResult:
    """Run a backtest on a DSL strategy file.

    Args:
        strategy_path: Path to .clj strategy file
        start_date: Backtest start date (timezone-aware)
        end_date: Backtest end date (timezone-aware)
        initial_capital: Starting capital
        data_dir: Path to historical data directory
        slippage_bps: Slippage in basis points

    Returns:
        BacktestResult with complete results

    Example:
        >>> from datetime import datetime, UTC
        >>> result = run_backtest(
        ...     strategy_path="strategies/core/main.clj",
        ...     start_date=datetime(2023, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 1, 1, tzinfo=UTC),
        ... )
        >>> print(result.summary())

    """
    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=UTC)

    config = BacktestConfig(
        strategy_path=Path(strategy_path),
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal(str(initial_capital)),
        data_dir=Path(data_dir),
        slippage_bps=Decimal(str(slippage_bps)),
    )

    engine = BacktestEngine(config)
    return engine.run()
