"""Business Unit: scripts | Status: current.

Backtesting execution engine.

Runs the full trading pipeline with historical data using real Strategy_v2 DSL engine
and mocked portfolio/execution layers.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.analysis.performance_metrics import PerformanceMetrics
from scripts.backtest.fill_simulator import FillSimulator
from scripts.backtest.historical_market_data_port import HistoricalMarketDataPort
from scripts.backtest.models.backtest_result import BacktestConfig, BacktestResult
from scripts.backtest.models.market_data import DailyBar
from scripts.backtest.models.portfolio_snapshot import (
    PortfolioSnapshot,
    PositionSnapshot,
    TradeRecord,
)
from scripts.backtest.storage.data_store import DataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine

# Constants
MIN_POSITION_SIZE = Decimal("0.01")  # Minimum trade size in shares

logger = get_logger(__name__)


class BacktestRunner:
    """Backtesting execution engine.

    Runs strategy -> portfolio -> execution pipeline with historical data.
    """

    def __init__(
        self,
        data_store: DataStore | None = None,
        fill_simulator: FillSimulator | None = None,
        strategy_files: list[str] | None = None,
    ) -> None:
        """Initialize backtest runner.

        Args:
            data_store: Optional DataStore instance
            fill_simulator: Optional FillSimulator instance
            strategy_files: Optional list of strategy files to use

        """
        self.data_store = data_store or DataStore()
        self.fill_simulator = fill_simulator or FillSimulator()
        self.strategy_files = strategy_files or ["KLM.clj"]
        logger.info(
            f"BacktestRunner initialized with strategies: {self.strategy_files}"
        )

    def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """Run a complete backtest.

        Args:
            config: Backtest configuration

        Returns:
            BacktestResult with portfolio evolution and performance metrics

        """
        logger.info(
            f"Starting backtest from {config.start_date} to {config.end_date}",
            start_date=config.start_date.isoformat(),
            end_date=config.end_date.isoformat(),
            initial_capital=str(config.initial_capital),
            strategy_files=config.strategy_files,
        )

        # Store strategy files from config
        self.strategy_files = config.strategy_files

        # Initialize result
        result = BacktestResult(
            strategy_name=", ".join(config.strategy_files),
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
        )

        # Initialize portfolio state
        current_portfolio = PortfolioSnapshot(
            timestamp=config.start_date,
            cash=config.initial_capital,
            positions={},
            total_value=config.initial_capital,
        )
        result.portfolio_snapshots.append(current_portfolio)

        logger.info(
            f"Using real Strategy_v2 DSL engine with files: {', '.join(config.strategy_files)}"
        )

        # Iterate through each trading day
        current_date = config.start_date
        trading_day = 0

        while current_date <= config.end_date:
            logger.debug(f"Processing trading day: {current_date.date()}")

            # Get all available symbols
            symbols = config.symbols or self._get_all_symbols()

            # Load market data for this day
            bars = self._load_bars_for_date(symbols, current_date)

            if not bars:
                logger.warning(f"No market data for {current_date.date()}, skipping")
                current_date += timedelta(days=1)
                continue

            # Generate signals (mocked for now)
            signals = self._generate_signals(symbols, bars, current_date)

            # Generate rebalance plan (mocked portfolio_v2)
            rebalance_plan = self._generate_rebalance_plan(
                current_portfolio, signals, bars
            )

            # Execute trades (mocked execution_v2)
            trades = self._execute_trades(rebalance_plan, bars)

            # Update portfolio state
            current_portfolio = self._update_portfolio(
                current_portfolio, trades, bars, current_date
            )

            # Store snapshot and trades
            result.portfolio_snapshots.append(current_portfolio)
            result.trades.extend(trades)

            trading_day += 1
            current_date += timedelta(days=1)

        # Calculate performance metrics
        PerformanceMetrics.calculate_metrics(result)

        logger.info(
            f"Backtest complete: {trading_day} trading days, {result.total_trades} trades",
            final_value=str(result.final_value),
            total_return=str(result.total_return),
            sharpe_ratio=str(result.sharpe_ratio),
            max_drawdown=str(result.max_drawdown),
        )

        return result

    def _get_all_symbols(self) -> list[str]:
        """Get all symbols available in data store (placeholder)."""
        # For now, return common symbols
        return ["SPY", "QQQ", "TECL", "TQQQ"]

    def _load_bars_for_date(
        self, symbols: list[str], date: datetime
    ) -> dict[str, DailyBar]:
        """Load market data bars for a specific date.

        Args:
            symbols: List of symbols
            date: Trading date

        Returns:
            Dictionary mapping symbol to DailyBar

        """
        bars: dict[str, DailyBar] = {}

        for symbol in symbols:
            try:
                # Load bars for this symbol around this date
                symbol_bars = self.data_store.load_bars(
                    symbol,
                    date - timedelta(days=1),
                    date + timedelta(days=1),
                )

                # Find bar for exact date
                for bar in symbol_bars:
                    if bar.date.date() == date.date():
                        bars[symbol] = bar
                        break

            except Exception as e:
                logger.debug(
                    f"Could not load data for {symbol} on {date.date()}",
                    symbol=symbol,
                    error=str(e),
                )

        return bars

    def _generate_signals(
        self, symbols: list[str], bars: dict[str, DailyBar], date: datetime
    ) -> dict[str, Decimal]:
        """Generate trading signals using real Strategy_v2 DSL engine.

        Args:
            symbols: List of symbols
            bars: Market data for the day
            date: Trading date

        Returns:
            Dictionary mapping symbol to target allocation weight

        """
        if not bars:
            return {}

        try:
            # Create historical market data port for this date
            market_data_port = HistoricalMarketDataPort(self.data_store, date)

            # Initialize DSL strategy engine with historical data
            strategy_engine = DslStrategyEngine(
                market_data_port=market_data_port,
                strategy_file=(
                    self.strategy_files[0] if self.strategy_files else "KLM.clj"
                ),
            )

            # Generate signals using real strategy
            strategy_signals = strategy_engine.generate_signals(timestamp=date)

            # Convert StrategySignal list to symbol -> weight dict
            signals: dict[str, Decimal] = {}
            total_allocation = Decimal("0")

            for signal in strategy_signals:
                if (
                    signal.target_allocation is not None
                    and signal.target_allocation > 0
                ):
                    symbol_str = str(signal.symbol)
                    signals[symbol_str] = signal.target_allocation
                    total_allocation += signal.target_allocation

            # Normalize allocations to sum to 1.0 if needed
            if total_allocation > Decimal("1.0"):
                for symbol in signals:
                    signals[symbol] = signals[symbol] / total_allocation

            logger.info(
                f"Generated {len(signals)} signals from Strategy_v2",
                date=date.date(),
                symbols=list(signals.keys()),
            )

            return signals

        except Exception as e:
            logger.error(
                f"Failed to generate signals from Strategy_v2: {e}",
                error=str(e),
                date=date.date(),
            )
            # Fallback to empty signals rather than mocked equal-weight
            return {}

    def _generate_rebalance_plan(
        self,
        portfolio: PortfolioSnapshot,
        signals: dict[str, Decimal],
        bars: dict[str, DailyBar],
    ) -> list[tuple[str, str, Decimal]]:
        """Generate rebalance plan (mocked portfolio_v2).

        Args:
            portfolio: Current portfolio state
            signals: Target allocation signals
            bars: Current market data

        Returns:
            List of (symbol, side, quantity) tuples

        """
        orders: list[tuple[str, str, Decimal]] = []

        # Calculate target positions
        total_value = portfolio.total_value
        target_positions: dict[str, Decimal] = {}

        for symbol, weight in signals.items():
            if symbol in bars:
                target_value = total_value * weight
                target_qty = target_value / bars[symbol].open
                target_positions[symbol] = target_qty

        # Generate orders to reach target positions
        for symbol, target_qty in target_positions.items():
            current_qty = Decimal("0")
            if symbol in portfolio.positions:
                current_qty = portfolio.positions[symbol].quantity

            delta = target_qty - current_qty

            if abs(delta) > MIN_POSITION_SIZE:
                side = "BUY" if delta > 0 else "SELL"
                orders.append((symbol, side, abs(delta)))

        # Generate SELL orders for positions not in signals
        for symbol, position in portfolio.positions.items():
            if symbol not in signals or symbol not in bars:
                orders.append((symbol, "SELL", position.quantity))

        return orders

    def _execute_trades(
        self,
        rebalance_plan: list[tuple[str, str, Decimal]],
        bars: dict[str, DailyBar],
    ) -> list[TradeRecord]:
        """Execute trades (mocked execution_v2).

        Args:
            rebalance_plan: List of orders to execute
            bars: Current market data

        Returns:
            List of TradeRecord objects

        """
        return self.fill_simulator.simulate_multiple_fills(rebalance_plan, bars)

    def _update_portfolio(
        self,
        portfolio: PortfolioSnapshot,
        trades: list[TradeRecord],
        bars: dict[str, DailyBar],
        date: datetime,
    ) -> PortfolioSnapshot:
        """Update portfolio state after trades.

        Args:
            portfolio: Current portfolio state
            trades: Executed trades
            bars: Current market data
            date: Current date

        Returns:
            New PortfolioSnapshot

        """
        # Start with current positions
        new_positions = dict(portfolio.positions)
        new_cash = portfolio.cash

        # Apply trades
        for trade in trades:
            if trade.side == "BUY":
                # Buy: decrease cash, increase position
                new_cash -= trade.total_cost

                if trade.symbol in new_positions:
                    # Update existing position
                    pos = new_positions[trade.symbol]
                    old_qty = pos.quantity
                    old_value = pos.avg_entry_price * old_qty
                    new_qty = old_qty + trade.quantity
                    new_avg_price = (
                        old_value + (trade.price * trade.quantity)
                    ) / new_qty

                    new_positions[trade.symbol] = PositionSnapshot(
                        symbol=trade.symbol,
                        quantity=new_qty,
                        avg_entry_price=new_avg_price,
                        current_price=trade.price,
                        market_value=new_qty * trade.price,
                        unrealized_pnl=(trade.price - new_avg_price) * new_qty,
                    )
                else:
                    # New position
                    new_positions[trade.symbol] = PositionSnapshot(
                        symbol=trade.symbol,
                        quantity=trade.quantity,
                        avg_entry_price=trade.price,
                        current_price=trade.price,
                        market_value=trade.quantity * trade.price,
                        unrealized_pnl=Decimal("0"),
                    )

            else:  # SELL
                # Sell: increase cash, decrease/remove position
                new_cash += trade.total_cost

                if trade.symbol in new_positions:
                    pos = new_positions[trade.symbol]
                    new_qty = pos.quantity - trade.quantity

                    if new_qty > MIN_POSITION_SIZE:
                        # Update position
                        new_positions[trade.symbol] = PositionSnapshot(
                            symbol=trade.symbol,
                            quantity=new_qty,
                            avg_entry_price=pos.avg_entry_price,
                            current_price=trade.price,
                            market_value=new_qty * trade.price,
                            unrealized_pnl=(trade.price - pos.avg_entry_price)
                            * new_qty,
                        )
                    else:
                        # Close position
                        del new_positions[trade.symbol]

        # Update positions with current prices
        for symbol, position in new_positions.items():
            if symbol in bars:
                current_price = bars[symbol].open
                new_positions[symbol] = PositionSnapshot(
                    symbol=position.symbol,
                    quantity=position.quantity,
                    avg_entry_price=position.avg_entry_price,
                    current_price=current_price,
                    market_value=position.quantity * current_price,
                    unrealized_pnl=(current_price - position.avg_entry_price)
                    * position.quantity,
                )

        # Calculate total value
        total_value = new_cash + sum(pos.market_value for pos in new_positions.values())

        # Calculate P&L
        day_pnl = total_value - portfolio.total_value
        total_pnl = total_value - portfolio.cash  # Assumes first snapshot has only cash

        return PortfolioSnapshot(
            timestamp=date,
            cash=new_cash,
            positions=new_positions,
            total_value=total_value,
            day_pnl=day_pnl,
            total_pnl=total_pnl,
        )
