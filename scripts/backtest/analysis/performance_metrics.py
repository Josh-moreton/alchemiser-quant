"""Business Unit: scripts | Status: current.

Performance metrics calculation for backtesting.

Calculates Sharpe ratio, drawdown, and other performance metrics.
"""

from __future__ import annotations

import math
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.models.backtest_result import BacktestResult
from scripts.backtest.models.portfolio_snapshot import PortfolioSnapshot
from the_alchemiser.shared.logging import get_logger

# Constants
TRADING_DAYS_PER_YEAR = 252
DEFAULT_RISK_FREE_RATE = Decimal("0.02")  # 2% annual risk-free rate

logger = get_logger(__name__)


class PerformanceMetrics:
    """Calculate performance metrics from backtest results."""

    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_snapshots: list[PortfolioSnapshot],
        risk_free_rate: Decimal = DEFAULT_RISK_FREE_RATE,
    ) -> Decimal:
        """Calculate Sharpe ratio.

        Args:
            portfolio_snapshots: List of portfolio snapshots
            risk_free_rate: Annual risk-free rate (default 2%)

        Returns:
            Sharpe ratio

        """
        if len(portfolio_snapshots) < 2:
            return Decimal("0")

        # Calculate daily returns
        returns: list[Decimal] = []
        for i in range(1, len(portfolio_snapshots)):
            prev_value = portfolio_snapshots[i - 1].total_value
            curr_value = portfolio_snapshots[i].total_value
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)

        if not returns:
            return Decimal("0")

        # Calculate mean and std of returns
        mean_return = sum(returns) / Decimal(len(returns))
        variance = sum((r - mean_return) * (r - mean_return) for r in returns) / Decimal(
            len(returns)
        )
        std_return = Decimal(str(math.sqrt(float(variance))))

        if std_return == 0:
            return Decimal("0")

        # Annualize (assuming ~252 trading days)
        daily_rf_rate = risk_free_rate / Decimal(str(TRADING_DAYS_PER_YEAR))
        excess_return = mean_return - daily_rf_rate
        return (excess_return / std_return) * Decimal(str(math.sqrt(TRADING_DAYS_PER_YEAR)))

    @staticmethod
    def calculate_max_drawdown(portfolio_snapshots: list[PortfolioSnapshot]) -> Decimal:
        """Calculate maximum drawdown.

        Args:
            portfolio_snapshots: List of portfolio snapshots

        Returns:
            Maximum drawdown as a percentage

        """
        if len(portfolio_snapshots) < 2:
            return Decimal("0")

        max_value = portfolio_snapshots[0].total_value
        max_drawdown = Decimal("0")

        for snapshot in portfolio_snapshots:
            if snapshot.total_value > max_value:
                max_value = snapshot.total_value

            if max_value > 0:
                drawdown = (max_value - snapshot.total_value) / max_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        return max_drawdown

    @staticmethod
    def calculate_metrics(result: BacktestResult) -> None:
        """Calculate and update all performance metrics in result.

        Args:
            result: BacktestResult to update (modified in place)

        """
        logger.info("Calculating performance metrics")

        if not result.portfolio_snapshots:
            logger.warning("No portfolio snapshots available for metrics")
            return

        # Calculate Sharpe ratio
        result.sharpe_ratio = PerformanceMetrics.calculate_sharpe_ratio(result.portfolio_snapshots)

        # Calculate max drawdown
        result.max_drawdown = PerformanceMetrics.calculate_max_drawdown(result.portfolio_snapshots)

        # Calculate final value and total return
        if result.portfolio_snapshots:
            final_snapshot = result.portfolio_snapshots[-1]
            result.final_value = final_snapshot.total_value
            result.total_return = (
                (result.final_value - result.initial_capital) / result.initial_capital * 100
            )

        # Calculate win rate from trades
        if result.trades:
            winning_trades = 0
            sell_count = 0
            # Track buy positions for each symbol (FIFO)
            positions: dict[str, list[Decimal]] = {}

            for trade in result.trades:
                if trade.side == "BUY":
                    # Add buy price to position stack
                    if trade.symbol not in positions:
                        positions[trade.symbol] = []
                    positions[trade.symbol].append(trade.price)
                elif trade.side == "SELL":
                    # Pop corresponding buy price and check if profitable
                    sell_count += 1
                    symbol_positions = positions.get(trade.symbol, [])
                    if symbol_positions:
                        buy_price = symbol_positions.pop(0)  # FIFO
                        if trade.price > buy_price:
                            winning_trades += 1

            if sell_count > 0:
                result.win_rate = Decimal(winning_trades) / Decimal(sell_count) * 100
            else:
                result.win_rate = Decimal("0")

        result.total_trades = len(result.trades)

        logger.info(
            "Metrics calculated",
            sharpe_ratio=str(result.sharpe_ratio),
            max_drawdown=str(result.max_drawdown),
            win_rate=str(result.win_rate),
        )
