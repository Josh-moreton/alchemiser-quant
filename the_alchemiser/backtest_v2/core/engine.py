"""Business Unit: backtest | Status: current.

Backtest engine for DSL strategy evaluation.

Orchestrates the complete backtest workflow: loads strategy, iterates over
trading days, evaluates DSL at each point-in-time, and simulates portfolio
rebalancing.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

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

if TYPE_CHECKING:
    from the_alchemiser.backtest_v2.adapters.data_fetcher import BacktestDataFetcher

logger = get_logger(__name__)

# Module constant
MODULE_NAME = "backtest_v2.core.engine"

# Benchmark symbol
BENCHMARK_SYMBOL: Final[str] = "SPY"

# Regex pattern to extract missing symbol from error messages
MISSING_SYMBOL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"No historical data found for symbol: (\w+)"
)


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
        self._fetched_symbols: set[str] = set()  # Track auto-fetched symbols
        self._data_fetcher: BacktestDataFetcher | None = None

        # Initialize market data adapter (start with end date, will update per day)
        self.market_data = BacktestMarketDataAdapter(
            data_dir=config.data_dir,
            as_of=config.end_date,
        )

        # Initialize data fetcher if auto-fetch is enabled
        if config.auto_fetch_missing:
            from the_alchemiser.backtest_v2.adapters.data_fetcher import (
                BacktestDataFetcher,
            )
            self._data_fetcher = BacktestDataFetcher(data_dir=config.data_dir)

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
            auto_fetch_enabled=config.auto_fetch_missing,
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

        If auto_fetch_missing is enabled, will attempt to fetch missing symbol
        data and retry evaluation once.

        Args:
            date: Evaluation date (point-in-time)
            ast: Parsed AST from strategy file
            correlation_id: Correlation ID for tracing

        Returns:
            Target weights dict or None if evaluation failed

        """
        return self._evaluate_with_retry(date, ast, correlation_id, retry_count=0)

    def _evaluate_with_retry(
        self,
        date: datetime,
        ast: object,
        correlation_id: str,
        retry_count: int,
    ) -> dict[str, Decimal] | None:
        """Internal evaluation method with retry logic for auto-fetch.

        Args:
            date: Evaluation date
            ast: Parsed AST
            correlation_id: Correlation ID
            retry_count: Current retry attempt (max 3)

        Returns:
            Target weights dict or None if evaluation failed

        """
        max_retries = 3  # Limit retries to prevent infinite loops
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
            error_str = str(e)

            # Check if this is a missing symbol error and auto-fetch is enabled
            if (
                self.config.auto_fetch_missing
                and self._data_fetcher is not None
                and retry_count < max_retries
            ):
                missing_symbol = self._extract_missing_symbol(error_str)
                if missing_symbol and missing_symbol not in self._fetched_symbols:
                    # Attempt to fetch the missing symbol
                    if self._auto_fetch_symbol(missing_symbol):
                        # Clear the market data cache for this symbol and retry
                        if missing_symbol in self.market_data._data_cache:
                            del self.market_data._data_cache[missing_symbol]

                        logger.info(
                            "Retrying evaluation after auto-fetch",
                            module=MODULE_NAME,
                            symbol=missing_symbol,
                            date=date.isoformat(),
                            retry_count=retry_count + 1,
                        )
                        return self._evaluate_with_retry(
                            date, ast, correlation_id, retry_count + 1
                        )

            # Record the error
            error_record: dict[str, object] = {
                "date": date.isoformat(),
                "error": error_str,
                "error_type": type(e).__name__,
                "correlation_id": correlation_id,
            }
            self.errors.append(error_record)

            logger.warning(
                "Strategy evaluation failed",
                module=MODULE_NAME,
                date=date.isoformat(),
                error=error_str,
                correlation_id=correlation_id,
            )

            return None

    def _extract_missing_symbol(self, error_str: str) -> str | None:
        """Extract missing symbol from error message.

        Args:
            error_str: Error message string

        Returns:
            Symbol string if found, None otherwise

        """
        match = MISSING_SYMBOL_PATTERN.search(error_str)
        if match:
            return match.group(1).upper()
        return None

    def _auto_fetch_symbol(self, symbol: str) -> bool:
        """Attempt to auto-fetch data for a missing symbol.

        Args:
            symbol: Symbol to fetch

        Returns:
            True if fetch was successful, False otherwise

        """
        if self._data_fetcher is None:
            return False

        logger.info(
            "Auto-fetching missing symbol data",
            module=MODULE_NAME,
            symbol=symbol,
            lookback_days=self.config.auto_fetch_lookback_days,
        )

        try:
            result = self._data_fetcher.fetch_symbol(
                symbol=symbol,
                lookback_days=self.config.auto_fetch_lookback_days,
            )

            if result.get("status") == "success":
                self._fetched_symbols.add(symbol)
                logger.info(
                    "Auto-fetch successful",
                    module=MODULE_NAME,
                    symbol=symbol,
                    bars_fetched=result.get("bars_fetched", 0),
                )
                return True

            logger.warning(
                "Auto-fetch returned non-success status",
                module=MODULE_NAME,
                symbol=symbol,
                status=result.get("status"),
                error=result.get("error"),
            )
            return False

        except Exception as e:
            logger.warning(
                "Auto-fetch failed with exception",
                module=MODULE_NAME,
                symbol=symbol,
                error=str(e),
            )
            self._fetched_symbols.add(symbol)  # Mark as attempted to avoid retrying
            return False

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
    auto_fetch_missing: bool = False,
    auto_fetch_lookback_days: int = 600,
) -> BacktestResult:
    """Run a backtest on a DSL strategy file.

    Args:
        strategy_path: Path to .clj strategy file
        start_date: Backtest start date (timezone-aware)
        end_date: Backtest end date (timezone-aware)
        initial_capital: Starting capital
        data_dir: Path to historical data directory
        slippage_bps: Slippage in basis points
        auto_fetch_missing: Auto-fetch missing symbol data from Alpaca API
        auto_fetch_lookback_days: Lookback days for auto-fetch (default 600)

    Returns:
        BacktestResult with complete results

    Example:
        >>> from datetime import datetime, UTC
        >>> result = run_backtest(
        ...     strategy_path="strategies/core/main.clj",
        ...     start_date=datetime(2023, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 1, 1, tzinfo=UTC),
        ...     auto_fetch_missing=True,
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
        auto_fetch_missing=auto_fetch_missing,
        auto_fetch_lookback_days=auto_fetch_lookback_days,
    )

    engine = BacktestEngine(config)
    return engine.run()
