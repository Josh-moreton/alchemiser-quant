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

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


# Core strategy and portfolio management
from the_alchemiser.core.trading.strategy_manager import (
    MultiStrategyManager,
    StrategyType,
)
from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer
from the_alchemiser.tracking.strategy_order_tracker import get_strategy_tracker
from .account_service import AccountService
from .execution_manager import ExecutionManager
from .reporting import (
    build_portfolio_state_data,
)
from .types import MultiStrategyExecutionResult


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

    def __init__(self, paper_trading: bool = True, strategy_allocations: Optional[Dict[StrategyType, float]] = None, 
                 ignore_market_hours: bool = False, config=None):
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
        self.data_provider = UnifiedDataProvider(
            paper_trading=self.paper_trading,
            config=config
        )
        self.trading_client = self.data_provider.trading_client

        # Order manager setup
        from the_alchemiser.execution.smart_execution import SmartExecution
        self.order_manager = SmartExecution(
            trading_client=self.trading_client,
            data_provider=self.data_provider,
            ignore_market_hours=self.ignore_market_hours,
            config=config if isinstance(config, dict) else {}
        )

        # Portfolio rebalancer
        self.portfolio_rebalancer = PortfolioRebalancer(self)

        # Strategy manager - pass our data provider to ensure same trading mode
        self.strategy_manager = MultiStrategyManager(
            strategy_allocations,
            shared_data_provider=self.data_provider,  # Pass our data provider
            config=config,
        )

        # Supporting services
        self.account_service = AccountService(self.data_provider)
        self.execution_manager = ExecutionManager(self)

        # Logging setup
        logging.info(
            f"TradingEngine initialized - Paper Trading: {self.paper_trading}"
        )

    # --- Account and Position Methods ---
    def get_account_info(self) -> Dict:
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
        return self.account_service.get_account_info()

    def get_positions(self) -> Dict:
        """Get current positions via UnifiedDataProvider.
        
        Returns:
            Dict of current positions keyed by symbol for compatibility with legacy code.
        """
        return self.account_service.get_positions()

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol via UnifiedDataProvider.
        
        Args:
            symbol: Stock symbol to get price for.
            
        Returns:
            Current price as float, or 0.0 if price unavailable.
        """
        return self.account_service.get_current_price(symbol)
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols.
        
        Args:
            symbols: List of stock symbols to get prices for.
            
        Returns:
            Dictionary mapping symbols to current prices.
        """
        return self.account_service.get_current_prices(symbols)

    # --- Order and Rebalancing Methods ---
    def wait_for_settlement(self, sell_orders: List[Dict], max_wait_time: int = 60, poll_interval: float = 2.0) -> bool:
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
        self, symbol: str, qty: float, side, 
        max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
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

    def rebalance_portfolio(self, target_portfolio: Dict[str, float], 
                          strategy_attribution: Optional[Dict[str, List[StrategyType]]] = None) -> List[Dict]:
        """Rebalance portfolio to target allocation.
        
        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages.
            strategy_attribution: Dictionary mapping symbols to contributing strategies.
            
        Returns:
            List of executed orders during rebalancing.
        """
        return self.portfolio_rebalancer.rebalance_portfolio(target_portfolio, strategy_attribution)

    def execute_rebalancing(self, target_allocations: Dict[str, float], mode: str = 'market') -> Dict:
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
            'trading_summary': {
                'total_orders': len(orders),
                'orders_executed': orders
            },
            'orders': orders
        }

    # --- Multi-Strategy Execution ---
    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """Execute all strategies and rebalance portfolio."""
        return self.execution_manager.execute_multi_strategy()

    # --- Reporting and Dashboard Methods ---
    def _archive_daily_strategy_pnl(self, pnl_summary: Dict) -> None:
        """Archive daily strategy P&L for historical tracking."""
        try:
            from the_alchemiser.utils.account_utils import extract_current_position_values
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

    def get_multi_strategy_performance_report(self) -> Dict:
        """Generate comprehensive performance report for all strategies"""
        try:
            current_positions = self.get_positions()
            report = {
                'timestamp': datetime.now().isoformat(),
                'strategy_allocations': {
                    k.value: v for k, v in self.strategy_manager.strategy_allocations.items()
                },
                'current_positions': current_positions,
                'performance_summary': self.strategy_manager.get_strategy_performance_summary()
            }
            return report
        except Exception as e:
            logging.error(f"Error generating performance report: {e}")
            return {'error': str(e)}

    def _build_portfolio_state_data(self, target_portfolio: Dict[str, float], account_info: Dict, current_positions: Dict) -> Dict:
        """Build portfolio state data for reporting purposes."""
        return build_portfolio_state_data(target_portfolio, account_info, current_positions)

    def _trigger_post_trade_validation(self, strategy_signals: Dict[StrategyType, Any], 
                                     orders_executed: List[Dict]):
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
                symbol = signal.get('symbol')
                if symbol and symbol != 'NUCLEAR_PORTFOLIO' and symbol != 'BEAR_PORTFOLIO':
                    if strategy_type == StrategyType.NUCLEAR:
                        nuclear_symbols.append(symbol)
                    elif strategy_type == StrategyType.TECL:
                        tecl_symbols.append(symbol)
            order_symbols = {order['symbol'] for order in orders_executed if 'symbol' in order}
            nuclear_strategy_symbols = ['SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX', 'UVXY', 'BTAL', 
                                      'QQQ', 'SQQQ', 'PSQ', 'UPRO', 'TLT', 'IEF', 
                                      'SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
            tecl_strategy_symbols = ['XLK', 'KMLM', 'SPXL', 'TECL', 'BIL', 'BSV', 'UVXY', 'SQQQ']
            for symbol in order_symbols:
                if symbol in nuclear_strategy_symbols and symbol not in nuclear_symbols:
                    nuclear_symbols.append(symbol)
                elif symbol in tecl_strategy_symbols and symbol not in tecl_symbols:
                    tecl_symbols.append(symbol)
            nuclear_symbols = list(set(nuclear_symbols))[:5]
            tecl_symbols = list(set(tecl_symbols))[:5]
            if nuclear_symbols or tecl_symbols:
                logging.info(f"🔍 Triggering post-trade validation for Nuclear: {nuclear_symbols}, TECL: {tecl_symbols}")
            else:
                logging.info("🔍 No symbols to validate in post-trade validation")
        except Exception as e:
            logging.error(f"❌ Post-trade validation failed: {e}")

    def display_target_vs_current_allocations(self, target_portfolio: Dict[str, float], account_info: Dict, current_positions: Dict) -> Tuple[Dict[str, float], Dict[str, float]]:
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
        from the_alchemiser.utils.account_utils import calculate_portfolio_values, extract_current_position_values
        from the_alchemiser.core.ui.cli_formatter import render_target_vs_current_allocations
        
        # Use helper functions to calculate values
        target_values = calculate_portfolio_values(target_portfolio, account_info)
        current_values = extract_current_position_values(current_positions)
        
        # Use existing formatter for display
        render_target_vs_current_allocations(target_portfolio, account_info, current_positions)
        
        return target_values, current_values

    def display_multi_strategy_summary(self, execution_result: MultiStrategyExecutionResult):
        """
        Display a summary of multi-strategy execution results using Rich
        Args:
            execution_result: The execution result to display
        """
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        
        console = Console()
        
        if not execution_result.success:
            console.print(Panel(
                f"[bold red]Execution failed: {execution_result.execution_summary.get('error', 'Unknown error')}[/bold red]",
                title="Execution Result",
                style="red"
            ))
            return

        # Portfolio allocation display
        portfolio_table = Table(title="Consolidated Portfolio", show_lines=False)
        portfolio_table.add_column("Symbol", style="bold cyan", justify="center")
        portfolio_table.add_column("Allocation", style="bold green", justify="right")
        portfolio_table.add_column("Visual", style="white", justify="left")
        
        sorted_portfolio = sorted(
            execution_result.consolidated_portfolio.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        for symbol, weight in sorted_portfolio:
            # Create visual bar
            bar_length = int(weight * 20)  # Scale to 20 chars max
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            portfolio_table.add_row(
                symbol,
                f"{weight:.1%}",
                f"[green]{bar}[/green]"
            )
        
        # Orders executed table
        if execution_result.orders_executed:
            orders_table = Table(title=f"Orders Executed ({len(execution_result.orders_executed)})", show_lines=False)
            orders_table.add_column("Type", style="bold", justify="center")
            orders_table.add_column("Symbol", style="cyan", justify="center")
            orders_table.add_column("Quantity", style="white", justify="right")
            orders_table.add_column("Estimated Value", style="green", justify="right")
            
            for order in execution_result.orders_executed:
                side = order.get('side', '')
                if hasattr(side, 'value'):
                    side_value = side.value
                else:
                    side_value = str(side)
                
                side_color = "green" if side_value == 'BUY' else "red"
                
                orders_table.add_row(
                    f"[{side_color}]{side_value}[/{side_color}]",
                    order.get('symbol', ''),
                    f"{order.get('qty', 0):.6f}",
                    f"${order.get('estimated_value', 0):.2f}"
                )
        else:
            orders_table = Panel(
                "[green]Portfolio already balanced - no trades needed[/green]",
                title="Orders Executed",
                style="green"
            )

        # Account summary
        if execution_result.account_info_after:
            account = execution_result.account_info_after
            account_content = Text()
            account_content.append(f"Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}\n", style="bold green")
            account_content.append(f"Cash Balance: ${float(account.get('cash', 0)):,.2f}\n", style="bold blue")
            
            # Add portfolio history P&L if available
            portfolio_history = account.get('portfolio_history', {})
            if portfolio_history and 'profit_loss' in portfolio_history:
                profit_loss = portfolio_history.get('profit_loss', [])
                profit_loss_pct = portfolio_history.get('profit_loss_pct', [])
                if profit_loss:
                    recent_pl = profit_loss[-1]
                    recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                    pl_color = "green" if recent_pl >= 0 else "red"
                    pl_sign = "+" if recent_pl >= 0 else ""
                    account_content.append(f"Recent P&L: {pl_sign}${recent_pl:,.2f} ({pl_sign}{recent_pl_pct*100:.2f}%)", style=f"bold {pl_color}")
            
            account_panel = Panel(account_content, title="Account Summary", style="bold white")
        else:
            account_panel = Panel("Account information not available", title="Account Summary", style="yellow")

        # Recent closed positions P&L table
        closed_pnl_table = None
        if execution_result.account_info_after and execution_result.account_info_after.get('recent_closed_pnl'):
            closed_pnl = execution_result.account_info_after['recent_closed_pnl']
            if closed_pnl:
                closed_pnl_table = Table(title="Recent Closed Positions P&L (Last 7 Days)", show_lines=False)
                closed_pnl_table.add_column("Symbol", style="bold cyan", justify="center")
                closed_pnl_table.add_column("Realized P&L", style="bold", justify="right")
                closed_pnl_table.add_column("P&L %", style="bold", justify="right")
                closed_pnl_table.add_column("Trades", style="white", justify="center")
                
                total_realized_pnl = 0
                
                for position in closed_pnl[:8]:  # Show top 8 in CLI summary
                    symbol = position.get('symbol', 'N/A')
                    realized_pnl = position.get('realized_pnl', 0)
                    realized_pnl_pct = position.get('realized_pnl_pct', 0)
                    trade_count = position.get('trade_count', 0)
                    
                    total_realized_pnl += realized_pnl
                    
                    # Color coding for P&L
                    pnl_color = "green" if realized_pnl >= 0 else "red"
                    pnl_sign = "+" if realized_pnl >= 0 else ""
                    
                    closed_pnl_table.add_row(
                        symbol,
                        f"[{pnl_color}]{pnl_sign}${realized_pnl:,.2f}[/{pnl_color}]",
                        f"[{pnl_color}]{pnl_sign}{realized_pnl_pct:.2f}%[/{pnl_color}]",
                        str(trade_count)
                    )
                
                # Add total row
                if len(closed_pnl) > 0:
                    total_pnl_color = "green" if total_realized_pnl >= 0 else "red"
                    total_pnl_sign = "+" if total_realized_pnl >= 0 else ""
                    closed_pnl_table.add_row(
                        "[bold]TOTAL[/bold]",
                        f"[bold {total_pnl_color}]{total_pnl_sign}${total_realized_pnl:,.2f}[/bold {total_pnl_color}]",
                        "-",
                        "-"
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
        
        console.print(Panel(
            "[bold green]Multi-strategy execution completed successfully[/bold green]",
            title="Execution Complete",
            style="green"
        ))

def main():
    """Test TradingEngine multi-strategy execution"""
    from rich.console import Console
    console = Console()
    
    logging.basicConfig(level=logging.WARNING)  # Reduced verbosity
    console.print("[bold cyan]Trading Engine Test[/bold cyan]")
    console.print("─" * 50)
    
    trader = TradingEngine(
        paper_trading=True,
        strategy_allocations={
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
    )
    
    console.print("[yellow]Executing multi-strategy...[/yellow]")
    result = trader.execute_multi_strategy()
    trader.display_multi_strategy_summary(result)
    
    console.print("[yellow]Getting performance report...[/yellow]")
    report = trader.get_multi_strategy_performance_report()
    if 'error' not in report:
        console.print("[green]Performance report generated successfully[/green]")
        console.print(f"   Current positions: {len(report['current_positions'])}")
        console.print(f"   Strategy tracking: {len(report['performance_summary'])}")
    else:
        console.print(f"[red]Error generating report: {report['error']}[/red]")

if __name__ == "__main__":
    main()
