"""Business Unit: shared | Status: current.

Backtesting execution engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from scripts.backtest.fill_simulator import FillSimulator
from scripts.backtest.models.backtest_result import BacktestResult, TradeRecord
from scripts.backtest.models.market_data import HistoricalBar
from scripts.backtest.models.portfolio_snapshot import PortfolioSnapshot, PositionSnapshot
from scripts.backtest.storage.data_store import DataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.strategy_v2.engines.dsl.engine import DslEngine

logger = get_logger(__name__)


class BacktestRunner:
    """Backtesting execution engine that runs the full trading pipeline.
    
    Executes strategy → portfolio → execution flow using historical data:
    1. Load historical market data for each day
    2. Run DSL strategy engine to generate signals
    3. Mock portfolio to create rebalance plan
    4. Mock execution to simulate fills at Open prices
    5. Update portfolio state and track performance
    """

    def __init__(
        self,
        strategy_config_path: str,
        data_store: DataStore,
        initial_capital: Decimal = Decimal("100000"),
        commission_per_trade: Decimal = Decimal("0"),
    ) -> None:
        """Initialize backtest runner.
        
        Args:
            strategy_config_path: Path to strategy .clj file
            data_store: Data store for historical data
            initial_capital: Starting portfolio value
            commission_per_trade: Commission per trade

        """
        self.strategy_config_path = strategy_config_path
        self.data_store = data_store
        self.initial_capital = initial_capital
        self.fill_simulator = FillSimulator(commission_per_trade)
        self.logger = logger

        # Initialize DSL engine (no event bus in backtest mode)
        self.dsl_engine = DslEngine(
            strategy_config_path=str(Path(strategy_config_path).parent),
            event_bus=None,
            market_data_service=None,  # We'll provide historical data directly
        )

    def run(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: list[str],
    ) -> BacktestResult:
        """Run backtest over date range.
        
        Args:
            start_date: Start date for backtest
            end_date: End date for backtest
            symbols: List of symbols to trade
            
        Returns:
            Complete backtest results

        """
        self.logger.info(
            f"Starting backtest from {start_date.date()} to {end_date.date()}",
            extra={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "symbols": symbols,
            },
        )

        # Initialize portfolio
        portfolio = PortfolioSnapshot.empty(start_date, self.initial_capital)
        trades: list[TradeRecord] = []
        daily_values: list[tuple[datetime, Decimal]] = [(start_date, self.initial_capital)]

        # Generate trading days
        current_date = start_date
        while current_date <= end_date:
            # Load historical data for this day
            day_bars = self._load_day_data(symbols, current_date)

            if not day_bars:
                # No trading day (weekend/holiday)
                current_date += timedelta(days=1)
                continue

            self.logger.debug(
                f"Processing {current_date.date()}",
                extra={"date": current_date.isoformat(), "symbols": len(day_bars)},
            )

            # Run strategy to generate signals
            target_allocations = self._run_strategy(day_bars)

            if not target_allocations:
                # No signals generated
                current_date += timedelta(days=1)
                continue

            # Create rebalance plan (mock portfolio_v2)
            trades_to_execute = self._create_rebalance_plan(
                portfolio, target_allocations, day_bars
            )

            # Execute trades (mock execution_v2)
            if trades_to_execute:
                fills = self.fill_simulator.simulate_rebalance(trades_to_execute, day_bars)

                # Update portfolio and record trades
                portfolio = self._update_portfolio(portfolio, fills, day_bars, current_date)
                trades.extend(self._convert_fills_to_trades(fills))

            # Record daily portfolio value
            portfolio_value = self._calculate_portfolio_value(portfolio, day_bars)
            daily_values.append((current_date, portfolio_value))

            current_date += timedelta(days=1)

        # Calculate final metrics
        from scripts.backtest.analysis.performance_metrics import calculate_metrics

        metrics = calculate_metrics(daily_values, trades, self.initial_capital)

        result = BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=daily_values[-1][1] if daily_values else self.initial_capital,
            trades=trades,
            daily_values=daily_values,
            metrics=metrics,
            strategy_name=Path(self.strategy_config_path).stem,
        )

        self.logger.info(
            f"Backtest complete: {len(trades)} trades, final value: {result.final_capital}",
            extra={
                "trade_count": len(trades),
                "final_value": str(result.final_capital),
                "return": str(metrics.total_return),
            },
        )

        return result

    def _load_day_data(
        self, symbols: list[str], date: datetime
    ) -> dict[str, HistoricalBar]:
        """Load historical data for a specific day.
        
        Args:
            symbols: List of symbols
            date: Date to load
            
        Returns:
            Dictionary mapping symbols to bars

        """
        day_bars: dict[str, HistoricalBar] = {}

        for symbol in symbols:
            bars = self.data_store.load_bars(symbol, date, date)
            if bars:
                day_bars[symbol] = bars[0]

        return day_bars

    def _run_strategy(self, day_bars: dict[str, HistoricalBar]) -> dict[str, Decimal]:
        """Run strategy engine to generate target allocations.
        
        Args:
            day_bars: Historical bars for the day
            
        Returns:
            Dictionary mapping symbols to target weights

        """
        # For MVP, implement simplified strategy evaluation
        # In full implementation, this would call DSL engine with historical data
        
        # Simplified: equal weight allocation
        if not day_bars:
            return {}

        weight = Decimal("1.0") / Decimal(str(len(day_bars)))
        return dict.fromkeys(day_bars.keys(), weight)

    def _create_rebalance_plan(
        self,
        portfolio: PortfolioSnapshot,
        target_allocations: dict[str, Decimal],
        day_bars: dict[str, HistoricalBar],
    ) -> dict[str, tuple[str, Decimal]]:
        """Create rebalance plan (mock portfolio_v2).
        
        Args:
            portfolio: Current portfolio state
            target_allocations: Target weights by symbol
            day_bars: Market data for pricing
            
        Returns:
            Dictionary mapping symbol to (action, quantity)

        """
        total_value = self._calculate_portfolio_value(portfolio, day_bars)
        trades: dict[str, tuple[str, Decimal]] = {}

        for symbol, target_weight in target_allocations.items():
            if symbol not in day_bars:
                continue

            target_value = total_value * target_weight
            current_value = Decimal("0")

            # Get current position value
            if symbol in portfolio.positions:
                pos = portfolio.positions[symbol]
                current_value = pos.quantity * day_bars[symbol].open_price

            # Calculate trade needed
            value_diff = target_value - current_value
            price = day_bars[symbol].open_price

            if abs(value_diff) < Decimal("10"):  # Minimum trade threshold
                continue

            if value_diff > 0:
                # Need to buy
                quantity = value_diff / price
                trades[symbol] = ("BUY", quantity)
            else:
                # Need to sell
                quantity = abs(value_diff) / price
                trades[symbol] = ("SELL", quantity)

        return trades

    def _update_portfolio(
        self,
        portfolio: PortfolioSnapshot,
        fills: list,
        day_bars: dict[str, HistoricalBar],
        date: datetime,
    ) -> PortfolioSnapshot:
        """Update portfolio state after fills.
        
        Args:
            portfolio: Current portfolio
            fills: List of simulated fills
            day_bars: Market data for pricing
            date: Current date
            
        Returns:
            Updated portfolio snapshot

        """
        from scripts.backtest.fill_simulator import SimulatedFill

        # Start with current positions
        new_positions: dict[str, PositionSnapshot] = dict(portfolio.positions)
        new_cash = portfolio.cash

        for fill in fills:
            if not isinstance(fill, SimulatedFill):
                continue
            
            # Update cash
            if fill.action == "BUY":
                new_cash -= fill.fill_value + fill.commission
            else:
                new_cash += fill.fill_value - fill.commission

            # Update position
            if fill.symbol in new_positions:
                pos = new_positions[fill.symbol]
                if fill.action == "BUY":
                    new_qty = pos.quantity + fill.quantity
                    new_avg_price = (
                        (pos.quantity * pos.average_price + fill.fill_value) / new_qty
                    )
                    new_positions[fill.symbol] = PositionSnapshot(
                        symbol=fill.symbol,
                        quantity=new_qty,
                        average_price=new_avg_price,
                        current_price=fill.fill_price,
                        market_value=new_qty * fill.fill_price,
                    )
                else:  # SELL
                    new_qty = pos.quantity - fill.quantity
                    if new_qty <= 0:
                        del new_positions[fill.symbol]
                    else:
                        new_positions[fill.symbol] = PositionSnapshot(
                            symbol=fill.symbol,
                            quantity=new_qty,
                            average_price=pos.average_price,
                            current_price=fill.fill_price,
                            market_value=new_qty * fill.fill_price,
                        )
            else:
                # New position (BUY only)
                if fill.action == "BUY":
                    new_positions[fill.symbol] = PositionSnapshot(
                        symbol=fill.symbol,
                        quantity=fill.quantity,
                        average_price=fill.fill_price,
                        current_price=fill.fill_price,
                        market_value=fill.fill_value,
                    )

        # Calculate total value
        total_value = new_cash + sum(
            pos.market_value for pos in new_positions.values()
        )

        return PortfolioSnapshot(
            date=date,
            cash=new_cash,
            positions=new_positions,
            total_value=total_value,
        )

    def _calculate_portfolio_value(
        self, portfolio: PortfolioSnapshot, day_bars: dict[str, HistoricalBar]
    ) -> Decimal:
        """Calculate current portfolio value.
        
        Args:
            portfolio: Portfolio snapshot
            day_bars: Market data for pricing
            
        Returns:
            Total portfolio value

        """
        total = portfolio.cash

        for symbol, position in portfolio.positions.items():
            if symbol in day_bars:
                price = day_bars[symbol].open_price
                total += position.quantity * price

        return total

    def _convert_fills_to_trades(self, fills: list) -> list[TradeRecord]:
        """Convert simulated fills to trade records.
        
        Args:
            fills: List of simulated fills
            
        Returns:
            List of trade records

        """
        from scripts.backtest.fill_simulator import SimulatedFill

        trades: list[TradeRecord] = []

        for fill in fills:
            if not isinstance(fill, SimulatedFill):
                continue
            
            trade = TradeRecord(
                date=fill.timestamp,
                symbol=fill.symbol,
                action=fill.action,
                quantity=fill.quantity,
                price=fill.fill_price,
                value=fill.fill_value,
                commission=fill.commission,
            )
            trades.append(trade)

        return trades
