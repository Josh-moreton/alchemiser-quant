#!/usr/bin/env python3
"""Trading Engine for The Alchemiser.

Unified multi-strategy trading engine for Alpaca, supporting portfolio rebalancing,
strategy execution, reporting, and dashboard integration.

This is the main orchestrator that coordinates signal generation, execution, and reporting
across multiple trading strategies with comprehensive position management.

Example:
    Initialize and run multi-strategy trading:

    >>> engine = TradingEngine(paper_trading=True)
    >>> result = engine.execute_multi_strategy()
    >>> engine.display_multi_strategy_summary(result)
"""

import logging
from datetime import datetime
from typing import Any, Protocol

from alpaca.trading.enums import OrderSide  # TODO: Phase 15 - Added for type safety

from the_alchemiser.core.trading.strategy_manager import (
    MultiStrategyManager,
    StrategyType,
)

# TODO: Add imports for types once they are used:
# from ..core.types import AccountInfo, PositionsDict, OrderDetails, ExecutionResult, StrategyPnLSummary
from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer

from .account_service import AccountService
from .execution_manager import ExecutionManager
from .reporting import (
    build_portfolio_state_data,
)
from .types import MultiStrategyExecutionResult


# Protocol definitions for dependency injection
class AccountInfoProvider(Protocol):
    """Protocol for account information retrieval."""

    def get_account_info(
        self,
    ) -> dict[str, Any]:  # TODO: Change to AccountInfo once data structure matches
        """Get comprehensive account information."""
        ...


class PositionProvider(Protocol):
    """Protocol for position data retrieval."""

    def get_positions_dict(
        self,
    ) -> dict[str, dict[str, Any]]:  # TODO: Change to PositionsDict once data structure matches
        """Get current positions keyed by symbol."""
        ...


class PriceProvider(Protocol):
    """Protocol for current price data retrieval."""

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a single symbol."""
        ...

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols."""
        ...


class RebalancingService(Protocol):
    """Protocol for portfolio rebalancing operations."""

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[dict[str, Any]]:  # TODO: Change to list[OrderDetails] once implementation updated
        """Rebalance portfolio to target allocation."""
        ...


class MultiStrategyExecutor(Protocol):
    """Protocol for multi-strategy execution."""

    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """Execute all strategies and rebalance portfolio."""
        ...


class TradingEngine:
    """Unified multi-strategy trading engine for Alpaca.

    Coordinates signal generation, order execution, portfolio rebalancing, and reporting
    across multiple trading strategies. Supports both paper and live trading with
    comprehensive position management and performance tracking.

    Attributes:
        config: Configuration object containing trading parameters.
        paper_trading (bool): Whether using paper trading account.
        ignore_market_hours (bool): Whether to trade outside market hours.
        data_provider: Unified data provider for market data and account info.
        trading_client: Alpaca trading client for order execution.
        order_manager: Smart execution engine for order placement.
        portfolio_rebalancer: Portfolio rebalancing workflow manager.
        strategy_manager: Multi-strategy signal generation manager.
    """

    def __init__(
        self,
        paper_trading: bool = True,
        strategy_allocations: dict[StrategyType, float] | None = None,
        ignore_market_hours: bool = False,
        config: Any = None,  # TODO: Phase 15 - Add proper config type
    ) -> None:
        """Initialize the TradingEngine.

        Args:
            paper_trading (bool): Whether to use paper trading account. Defaults to True.
            strategy_allocations (Dict[StrategyType, float], optional): Portfolio allocation
                between strategies. If None, uses equal allocation.
            ignore_market_hours (bool): Whether to ignore market hours when placing orders.
                Defaults to False.
            config: Configuration object. If None, loads from global config.

        Note:
            The engine automatically sets up data providers, trading clients, order managers,
            and strategy managers based on the provided configuration.
        """
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import load_settings

            config = load_settings()

        self.config = config
        self.paper_trading = paper_trading
        self.ignore_market_hours = ignore_market_hours

        # Data provider and trading client setup
        from the_alchemiser.core.data.data_provider import UnifiedDataProvider

        self.data_provider = UnifiedDataProvider(paper_trading=self.paper_trading, config=config)
        self.trading_client = self.data_provider.trading_client

        # Order manager setup
        from the_alchemiser.execution.smart_execution import SmartExecution

        self.order_manager = SmartExecution(
            trading_client=self.trading_client,
            data_provider=self.data_provider,
            ignore_market_hours=self.ignore_market_hours,
            config=config if isinstance(config, dict) else {},
        )

        # Portfolio rebalancer
        self.portfolio_rebalancer = PortfolioRebalancer(self)

        # Strategy manager - pass our data provider to ensure same trading mode
        self.strategy_manager = MultiStrategyManager(
            strategy_allocations,
            shared_data_provider=self.data_provider,  # Pass our data provider
            config=config,
        )

        # Supporting services for composition-based access
        self.account_service = AccountService(self.data_provider)
        self.execution_manager = ExecutionManager(self)

        # Compose dependencies for type-safe delegation
        self._account_info_provider: AccountInfoProvider = self.account_service
        self._position_provider: PositionProvider = self.account_service
        self._price_provider: PriceProvider = self.account_service
        self._rebalancing_service: RebalancingService = self.portfolio_rebalancer
        self._multi_strategy_executor: MultiStrategyExecutor = self.execution_manager

        # Logging setup
        logging.info(f"TradingEngine initialized - Paper Trading: {self.paper_trading}")

    # --- Account and Position Methods ---
    def get_account_info(
        self,
    ) -> dict[str, Any]:  # TODO: Change to AccountInfo once data structure matches
        """Get comprehensive account information including P&L data.

        Retrieves detailed account information including portfolio value, equity,
        buying power, recent portfolio history, open positions, and closed P&L data.

        Returns:
            Dict: Account information containing:
                - account_number: Account identifier
                - portfolio_value: Total portfolio value
                - equity: Account equity
                - buying_power: Available buying power
                - cash: Available cash
                - day_trade_count: Number of day trades
                - status: Account status
                - portfolio_history: Recent portfolio performance
                - open_positions: Current open positions
                - recent_closed_pnl: Recent closed position P&L (last 7 days)

        Note:
            Returns empty dict if account information cannot be retrieved.
        """
        try:
            account_info = self._account_info_provider.get_account_info()

            # Add trading engine context
            if account_info:
                account_info["trading_mode"] = "paper" if self.paper_trading else "live"
                account_info["market_hours_ignored"] = self.ignore_market_hours

            return account_info
        except Exception as e:
            logging.error(f"Failed to retrieve account information: {e}")

            # Enhanced error handling
            try:
                from the_alchemiser.core.error_handler import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="account information retrieval",
                    component="TradingEngine.get_account_info",
                    additional_data={"paper_trading": self.paper_trading},
                )
            except ImportError:
                pass  # Fallback for backward compatibility

            return {}

    def get_positions(self) -> dict[str, Any]:
        """Get current positions via account service with engine context.

        Returns:
            Dict of current positions keyed by symbol, enhanced with trading context.
        """
        try:
            positions = self._position_provider.get_positions_dict()

            # Add engine context to positions data
            if positions:
                for _symbol, position_data in positions.items():
                    if isinstance(position_data, dict):
                        position_data["retrieved_via"] = "trading_engine"
                        position_data["trading_mode"] = "paper" if self.paper_trading else "live"

            return positions
        except Exception as e:
            logging.error(f"Failed to retrieve positions: {e}")
            return {}

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol with engine-level validation.

        Args:
            symbol: Stock symbol to get price for.

        Returns:
            Current price as float, or 0.0 if price unavailable.
        """
        if not symbol or not isinstance(symbol, str):
            logging.warning(f"Invalid symbol provided to get_current_price: {symbol}")
            return 0.0

        try:
            price = self._price_provider.get_current_price(symbol.upper())

            # Engine-level validation
            if price and price > 0:
                logging.debug(f"Retrieved price for {symbol}: ${price:.2f}")
                return price
            else:
                logging.warning(f"Invalid price received for {symbol}: {price}")
                return 0.0

        except Exception as e:
            logging.error(f"Failed to get current price for {symbol}: {e}")
            return 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols with engine-level validation.

        Args:
            symbols: List of stock symbols to get prices for.

        Returns:
            Dict mapping symbols to current prices, excluding symbols with invalid prices.
        """
        if not symbols or not isinstance(symbols, list):
            logging.warning(f"Invalid symbols list provided: {symbols}")
            return {}

        # Clean and validate symbols
        valid_symbols = [s.upper() for s in symbols if isinstance(s, str) and s.strip()]

        if not valid_symbols:
            logging.warning("No valid symbols provided to get_current_prices")
            return {}

        try:
            prices = self._price_provider.get_current_prices(valid_symbols)

            # Engine-level validation and logging
            valid_prices = {}
            for symbol, price in prices.items():
                if price and price > 0:
                    valid_prices[symbol] = price
                else:
                    logging.warning(f"Invalid price for {symbol}: {price}")

            logging.debug(
                f"Retrieved {len(valid_prices)} valid prices out of {len(valid_symbols)} requested"
            )
            return valid_prices

        except Exception as e:
            logging.error(f"Failed to get current prices: {e}")
            return {}

    # --- Order and Rebalancing Methods ---
    def wait_for_settlement(
        self, sell_orders: list[dict[str, Any]], max_wait_time: int = 60, poll_interval: float = 2.0
    ) -> bool:
        """Wait for sell orders to settle by polling their status.

        Args:
            sell_orders: List of sell order dictionaries with order_id keys.
            max_wait_time: Maximum time to wait in seconds. Defaults to 60.
            poll_interval: Polling interval in seconds. Defaults to 2.0.

        Returns:
            True if all orders settled successfully, False otherwise.
        """
        return self.order_manager.wait_for_settlement(sell_orders, max_wait_time, poll_interval)

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: OrderSide,  # TODO: Phase 15 - Now using proper Alpaca enum
        max_retries: int = 3,
        poll_timeout: int = 30,
        poll_interval: float = 2.0,
        slippage_bps: float | None = None,
    ) -> str | None:
        """Place a limit or market order using the smart execution engine.

        Args:
            symbol: Stock symbol to trade.
            qty: Quantity to trade.
            side: Order side (BUY or SELL).
            max_retries: Maximum number of retry attempts. Defaults to 3.
            poll_timeout: Timeout for order polling in seconds. Defaults to 30.
            poll_interval: Polling interval in seconds. Defaults to 2.0.
            slippage_bps: Maximum slippage in basis points. Defaults to None.

        Returns:
            Order ID if successful, None if failed.
        """
        return self.order_manager.place_order(
            symbol, qty, side, max_retries, poll_timeout, poll_interval, slippage_bps
        )

    def rebalance_portfolio(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[dict[str, Any]]:  # TODO: Change to list[OrderDetails] once implementation updated
        """Rebalance portfolio to target allocation with engine-level orchestration.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages.
            strategy_attribution: Dictionary mapping symbols to contributing strategies.

        Returns:
            List of executed orders during rebalancing.
        """
        if not target_portfolio:
            logging.warning("Empty target portfolio provided to rebalance_portfolio")
            return []

        # Validate portfolio allocations
        total_allocation = sum(target_portfolio.values())
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")

        # Log rebalancing initiation
        logging.info(f"Initiating portfolio rebalancing with {len(target_portfolio)} symbols")
        logging.debug(f"Target allocations: {target_portfolio}")

        try:
            # Use composed rebalancing service
            orders = self._rebalancing_service.rebalance_portfolio(
                target_portfolio, strategy_attribution
            )

            # Engine-level post-processing
            if orders:
                logging.info(f"Portfolio rebalancing completed with {len(orders)} orders")

                # Add engine context to orders
                for order in orders:
                    if isinstance(order, dict):
                        order["executed_via"] = "trading_engine"
                        order["trading_mode"] = "paper" if self.paper_trading else "live"
            else:
                logging.info("Portfolio rebalancing completed with no orders needed")

            return orders

        except Exception as e:
            logging.error(f"Portfolio rebalancing failed: {e}")
            return []

    def execute_rebalancing(
        self, target_allocations: dict[str, float], mode: str = "market"
    ) -> dict[str, Any]:
        """
        Execute portfolio rebalancing with the specified mode.

        Args:
            target_allocations: Target allocation percentages by symbol
            mode: Rebalancing mode ('market', 'limit', 'paper') - currently unused but kept for compatibility

        Returns:
            Dictionary with trading summary and order details for compatibility
        """
        orders = self.rebalance_portfolio(target_allocations)

        # Create a summary structure for test compatibility
        return {
            "trading_summary": {"total_orders": len(orders), "orders_executed": orders},
            "orders": orders,
        }

    # --- Multi-Strategy Execution ---
    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """Execute all strategies and rebalance portfolio with engine orchestration.

        Returns:
            MultiStrategyExecutionResult with comprehensive execution details.
        """
        logging.info("Initiating multi-strategy execution")

        # Pre-execution validation
        try:
            account_info = self.get_account_info()
            if not account_info:
                logging.error(
                    "Cannot proceed with multi-strategy execution: account info unavailable"
                )
                return MultiStrategyExecutionResult(
                    success=False,
                    strategy_signals={},
                    consolidated_portfolio={},
                    orders_executed=[],
                    account_info_before={},
                    account_info_after={},
                    execution_summary={"error": "Failed to retrieve account information"},
                    final_portfolio_state={},
                )
        except Exception as e:
            logging.error(f"Pre-execution validation failed: {e}")
            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before={},
                account_info_after={},
                execution_summary={"error": f"Pre-execution validation failed: {e}"},
                final_portfolio_state={},
            )

        try:
            # Use composed multi-strategy executor
            result = self._multi_strategy_executor.execute_multi_strategy()

            # Engine-level post-processing
            if result.success:
                logging.info("Multi-strategy execution completed successfully")

                # Add engine context to result
                if result.execution_summary:
                    result.execution_summary["engine_mode"] = (
                        "paper" if self.paper_trading else "live"
                    )
                    result.execution_summary["market_hours_ignored"] = self.ignore_market_hours

            else:
                logging.warning("Multi-strategy execution completed with issues")

            return result

        except Exception as e:
            logging.error(f"Multi-strategy execution failed: {e}")

            # Enhanced error handling
            try:
                from the_alchemiser.core.error_handler import handle_trading_error

                handle_trading_error(
                    error=e,
                    context="multi-strategy execution",
                    component="TradingEngine.execute_multi_strategy",
                    additional_data={
                        "paper_trading": self.paper_trading,
                        "ignore_market_hours": self.ignore_market_hours,
                    },
                )
            except ImportError:
                pass  # Fallback for backward compatibility

            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before={},
                account_info_after={},
                execution_summary={"error": f"Execution failed: {e}"},
                final_portfolio_state={},
            )

    # --- Reporting and Dashboard Methods ---
    def _archive_daily_strategy_pnl(self, pnl_summary: dict[str, Any]) -> None:  # noqa: ARG002
        """Archive daily strategy P&L for historical tracking."""
        try:
            from the_alchemiser.tracking.strategy_order_tracker import get_strategy_tracker

            # Get current positions and prices
            current_positions = self.get_positions()
            symbols_in_portfolio = set(current_positions.keys())
            current_prices = self.get_current_prices(list(symbols_in_portfolio))

            # Archive the daily P&L snapshot
            tracker = get_strategy_tracker(paper_trading=self.paper_trading)
            tracker.archive_daily_pnl(current_prices)

            logging.info("Successfully archived daily strategy P&L snapshot")

        except Exception as e:
            logging.error(f"Failed to archive daily strategy P&L: {e}")

    def get_multi_strategy_performance_report(
        self,
    ) -> dict[str, Any]:  # TODO: Change to StrategyPnLSummary once implementation updated
        """Generate comprehensive performance report for all strategies"""
        try:
            current_positions = self.get_positions()
            report = {
                "timestamp": datetime.now().isoformat(),
                "strategy_allocations": {
                    k.value: v for k, v in self.strategy_manager.strategy_allocations.items()
                },
                "current_positions": current_positions,
                "performance_summary": self.strategy_manager.get_strategy_performance_summary(),
            }
            return report
        except Exception as e:
            logging.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

    def _build_portfolio_state_data(
        self,
        target_portfolio: dict[str, float],
        account_info: dict[str, Any],  # TODO: Change to AccountInfo once structure matches
        current_positions: dict[str, Any],  # TODO: Change to PositionsDict once structure matches
    ) -> dict[str, Any]:  # TODO: Change to ExecutionResult once structure matches
        """Build portfolio state data for reporting purposes."""
        return build_portfolio_state_data(target_portfolio, account_info, current_positions)

    def _trigger_post_trade_validation(
        self, strategy_signals: dict[StrategyType, Any], orders_executed: list[dict[str, Any]]
    ) -> None:  # TODO: Phase 15 - Added return type annotation
        """
        Trigger post-trade technical indicator validation for live trading
        Args:
            strategy_signals: Strategy signals that led to trades
            orders_executed: List of executed orders
        """
        try:
            nuclear_symbols = []
            tecl_symbols = []
            for strategy_type, signal in strategy_signals.items():
                symbol = signal.get("symbol")
                if symbol and symbol != "NUCLEAR_PORTFOLIO" and symbol != "BEAR_PORTFOLIO":
                    if strategy_type == StrategyType.NUCLEAR:
                        nuclear_symbols.append(symbol)
                    elif strategy_type == StrategyType.TECL:
                        tecl_symbols.append(symbol)
            order_symbols = {order["symbol"] for order in orders_executed if "symbol" in order}
            nuclear_strategy_symbols = [
                "SPY",
                "IOO",
                "TQQQ",
                "VTV",
                "XLF",
                "VOX",
                "UVXY",
                "BTAL",
                "QQQ",
                "SQQQ",
                "PSQ",
                "UPRO",
                "TLT",
                "IEF",
                "SMR",
                "BWXT",
                "LEU",
                "EXC",
                "NLR",
                "OKLO",
            ]
            tecl_strategy_symbols = ["XLK", "KMLM", "SPXL", "TECL", "BIL", "BSV", "UVXY", "SQQQ"]
            for symbol in order_symbols:
                if symbol in nuclear_strategy_symbols and symbol not in nuclear_symbols:
                    nuclear_symbols.append(symbol)
                elif symbol in tecl_strategy_symbols and symbol not in tecl_symbols:
                    tecl_symbols.append(symbol)
            nuclear_symbols = list(set(nuclear_symbols))[:5]
            tecl_symbols = list(set(tecl_symbols))[:5]
            if nuclear_symbols or tecl_symbols:
                logging.info(
                    f"🔍 Triggering post-trade validation for Nuclear: {nuclear_symbols}, TECL: {tecl_symbols}"
                )
            else:
                logging.info("🔍 No symbols to validate in post-trade validation")
        except Exception as e:
            logging.error(f"❌ Post-trade validation failed: {e}")

    def display_target_vs_current_allocations(
        self,
        target_portfolio: dict[str, float],
        account_info: dict[str, Any],
        current_positions: dict[str, Any],
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Display target vs current allocations and return calculated values.

        Shows a comparison between target portfolio weights and current position values,
        helping to visualize rebalancing needs.

        Args:
            target_portfolio (Dict[str, float]): Target allocation weights by symbol.
            account_info (Dict): Account information including portfolio value.
            current_positions (Dict): Current position data by symbol.

        Returns:
            Tuple[Dict[str, float], Dict[str, float]]: A tuple containing:
                - target_values: Target dollar values by symbol
                - current_values: Current market values by symbol

        Note:
            Uses Rich table formatting via cli_formatter for beautiful display.
        """
        from the_alchemiser.core.ui.cli_formatter import render_target_vs_current_allocations
        from the_alchemiser.utils.account_utils import (
            calculate_portfolio_values,
            extract_current_position_values,
        )

        # Use helper functions to calculate values
        target_values = calculate_portfolio_values(target_portfolio, account_info)
        current_values = extract_current_position_values(current_positions)

        # Use existing formatter for display
        render_target_vs_current_allocations(target_portfolio, account_info, current_positions)

        return target_values, current_values

    def display_multi_strategy_summary(
        self, execution_result: MultiStrategyExecutionResult
    ) -> None:  # TODO: Phase 15 - Added return type
        """
        Display a summary of multi-strategy execution results using Rich
        Args:
            execution_result: The execution result to display
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        # Type annotation for orders_table that can be either Table or Panel
        orders_table: Table | Panel

        console = Console()

        if not execution_result.success:
            console.print(
                Panel(
                    f"[bold red]Execution failed: {execution_result.execution_summary.get('error', 'Unknown error')}[/bold red]",
                    title="Execution Result",
                    style="red",
                )
            )
            return

        # Portfolio allocation display
        portfolio_table = Table(title="Consolidated Portfolio", show_lines=False)
        portfolio_table.add_column("Symbol", style="bold cyan", justify="center")
        portfolio_table.add_column("Allocation", style="bold green", justify="right")
        portfolio_table.add_column("Visual", style="white", justify="left")

        sorted_portfolio = sorted(
            execution_result.consolidated_portfolio.items(), key=lambda x: x[1], reverse=True
        )

        for symbol, weight in sorted_portfolio:
            # Create visual bar
            bar_length = int(weight * 20)  # Scale to 20 chars max
            bar = "█" * bar_length + "░" * (20 - bar_length)

            portfolio_table.add_row(symbol, f"{weight:.1%}", f"[green]{bar}[/green]")

        # Orders executed table
        if execution_result.orders_executed:
            orders_table = Table(
                title=f"Orders Executed ({len(execution_result.orders_executed)})", show_lines=False
            )
            orders_table.add_column("Type", style="bold", justify="center")
            orders_table.add_column("Symbol", style="cyan", justify="center")
            orders_table.add_column("Quantity", style="white", justify="right")
            orders_table.add_column("Estimated Value", style="green", justify="right")

            for order in execution_result.orders_executed:
                side = order.get("side", "")
                if hasattr(side, "value"):
                    side_value = side.value
                else:
                    side_value = str(side)

                side_color = "green" if side_value == "BUY" else "red"

                orders_table.add_row(
                    f"[{side_color}]{side_value}[/{side_color}]",
                    order.get("symbol", ""),
                    f"{order.get('qty', 0):.6f}",
                    f"${order.get('estimated_value', 0):.2f}",
                )
        else:
            orders_table = Panel(
                "[green]Portfolio already balanced - no trades needed[/green]",
                title="Orders Executed",
                style="green",
            )

        # Account summary
        if execution_result.account_info_after:
            account = execution_result.account_info_after
            account_content = Text()
            account_content.append(
                f"Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}\n",
                style="bold green",
            )
            account_content.append(
                f"Cash Balance: ${float(account.get('cash', 0)):,.2f}\n", style="bold blue"
            )

            # Add portfolio history P&L if available
            portfolio_history = account.get("portfolio_history", {})
            if portfolio_history and "profit_loss" in portfolio_history:
                profit_loss = portfolio_history.get("profit_loss", [])
                profit_loss_pct = portfolio_history.get("profit_loss_pct", [])
                if profit_loss:
                    recent_pl = profit_loss[-1]
                    recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                    pl_color = "green" if recent_pl >= 0 else "red"
                    pl_sign = "+" if recent_pl >= 0 else ""
                    account_content.append(
                        f"Recent P&L: {pl_sign}${recent_pl:,.2f} ({pl_sign}{recent_pl_pct*100:.2f}%)",
                        style=f"bold {pl_color}",
                    )

            account_panel = Panel(account_content, title="Account Summary", style="bold white")
        else:
            account_panel = Panel(
                "Account information not available", title="Account Summary", style="yellow"
            )

        # Recent closed positions P&L table
        closed_pnl_table = None
        if execution_result.account_info_after and execution_result.account_info_after.get(
            "recent_closed_pnl"
        ):
            closed_pnl = execution_result.account_info_after["recent_closed_pnl"]
            if closed_pnl:
                closed_pnl_table = Table(
                    title="Recent Closed Positions P&L (Last 7 Days)", show_lines=False
                )
                closed_pnl_table.add_column("Symbol", style="bold cyan", justify="center")
                closed_pnl_table.add_column("Realized P&L", style="bold", justify="right")
                closed_pnl_table.add_column("P&L %", style="bold", justify="right")
                closed_pnl_table.add_column("Trades", style="white", justify="center")

                total_realized_pnl = 0

                for position in closed_pnl[:8]:  # Show top 8 in CLI summary
                    symbol = position.get("symbol", "N/A")
                    realized_pnl = position.get("realized_pnl", 0)
                    realized_pnl_pct = position.get("realized_pnl_pct", 0)
                    trade_count = position.get("trade_count", 0)

                    total_realized_pnl += realized_pnl

                    # Color coding for P&L
                    pnl_color = "green" if realized_pnl >= 0 else "red"
                    pnl_sign = "+" if realized_pnl >= 0 else ""

                    closed_pnl_table.add_row(
                        symbol,
                        f"[{pnl_color}]{pnl_sign}${realized_pnl:,.2f}[/{pnl_color}]",
                        f"[{pnl_color}]{pnl_sign}{realized_pnl_pct:.2f}%[/{pnl_color}]",
                        str(trade_count),
                    )

                # Add total row
                if len(closed_pnl) > 0:
                    total_pnl_color = "green" if total_realized_pnl >= 0 else "red"
                    total_pnl_sign = "+" if total_realized_pnl >= 0 else ""
                    closed_pnl_table.add_row(
                        "[bold]TOTAL[/bold]",
                        f"[bold {total_pnl_color}]{total_pnl_sign}${total_realized_pnl:,.2f}[/bold {total_pnl_color}]",
                        "-",
                        "-",
                    )

        # Display everything
        console.print()
        console.print(portfolio_table)
        console.print()

        if isinstance(orders_table, Table):
            console.print(orders_table)
        else:
            console.print(orders_table)
        console.print()

        # Display closed P&L table if available
        if closed_pnl_table:
            console.print(closed_pnl_table)
            console.print()

        console.print(account_panel)
        console.print()

        console.print(
            Panel(
                "[bold green]Multi-strategy execution completed successfully[/bold green]",
                title="Execution Complete",
                style="green",
            )
        )


def main():
    """Test TradingEngine multi-strategy execution"""
    from rich.console import Console

    console = Console()

    logging.basicConfig(level=logging.WARNING)  # Reduced verbosity
    console.print("[bold cyan]Trading Engine Test[/bold cyan]")
    console.print("─" * 50)

    trader = TradingEngine(
        paper_trading=True, strategy_allocations={StrategyType.NUCLEAR: 0.5, StrategyType.TECL: 0.5}
    )

    console.print("[yellow]Executing multi-strategy...[/yellow]")
    result = trader.execute_multi_strategy()
    trader.display_multi_strategy_summary(result)

    console.print("[yellow]Getting performance report...[/yellow]")
    report = trader.get_multi_strategy_performance_report()
    if "error" not in report:
        console.print("[green]Performance report generated successfully[/green]")
        console.print(f"   Current positions: {len(report['current_positions'])}")
        console.print(f"   Strategy tracking: {len(report['performance_summary'])}")
    else:
        console.print(f"[red]Error generating report: {report['error']}[/red]")


if __name__ == "__main__":
    main()
