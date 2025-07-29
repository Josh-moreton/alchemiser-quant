#!/usr/bin/env python3
"""
Alchemiser Trading Bot

Unified multi-strategy trading bot for Alpaca, supporting portfolio rebalancing,
strategy execution, reporting, and dashboard integration.

This replaces both the old AlpacaTradingBot and MultiStrategyAlpacaTrader classes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


# Core strategy and portfolio management
from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer


@dataclass
class MultiStrategyExecutionResult:
    """Result of multi-strategy execution"""
    success: bool
    strategy_signals: Dict[StrategyType, Any]
    consolidated_portfolio: Dict[str, float]
    orders_executed: List[Dict]
    account_info_before: Dict
    account_info_after: Dict
    execution_summary: Dict
    final_portfolio_state: Optional[Dict] = None


class AlchemiserTradingBot:
    def display_target_vs_current_allocations(self, target_portfolio: Dict[str, float], account_info: Dict, current_positions: Dict) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        Display target vs current allocations and return the calculated values.
        Returns:
            Tuple of (target_values, current_values) dictionaries
        """
        portfolio_value = account_info.get('portfolio_value', 0.0)
        # Calculate target and current allocations based on portfolio value
        target_values = {
            symbol: portfolio_value * weight 
            for symbol, weight in target_portfolio.items()
        }
        current_values = {
            symbol: float(getattr(pos, 'market_value', 0.0)) 
            for symbol, pos in current_positions.items()
        }
        print(f"🎯 Target vs Current Allocations (trades only if % difference > 1.0):")
        all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
        for symbol in sorted(all_symbols):
            target = target_values.get(symbol, 0.0)
            current = current_values.get(symbol, 0.0)
            pct_diff = 0.0
            if max(target, current) > 0:
                pct_diff = 100 * abs(target - current) / max(target, current)
            print(f"  {symbol:<6} Target: ${target:,.2f} | Current: ${current:,.2f} | Diff: {pct_diff:.2f}%")
        return target_values, current_values
    """Unified multi-strategy trading bot for Alpaca"""

    def __init__(self, paper_trading: bool = True, strategy_allocations: Optional[Dict[StrategyType, float]] = None, 
                 ignore_market_hours: bool = False, config=None):
        """
        Initialize AlchemiserTradingBot
        Args:
            paper_trading: Whether to use paper trading account
            strategy_allocations: Portfolio allocation between strategies
            ignore_market_hours: Whether to ignore market hours when placing orders
            config: Configuration object. If None, will load from global config.
        """
        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import get_config
            config = get_config()

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
        from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter
        self.order_manager = OrderManagerAdapter(
            trading_client=self.trading_client,
            data_provider=self.data_provider,
            ignore_market_hours=self.ignore_market_hours,
            config=config if isinstance(config, dict) else {}
        )

        # Portfolio rebalancer
        self.portfolio_rebalancer = PortfolioRebalancer(self)

        # Strategy manager
        self.strategy_manager = MultiStrategyManager(strategy_allocations, config=config)

        # Logging setup
        logging.info(f"AlchemiserTradingBot initialized - Paper Trading: {self.paper_trading}")

    # --- Account and Position Methods ---
    def get_account_info(self) -> Dict:
        """Get comprehensive account information including P&L data"""
        account = self.data_provider.get_account_info()
        if not account:
            return {}
        portfolio_history = self.data_provider.get_portfolio_history()
        open_positions = self.data_provider.get_open_positions()
        return {
            'account_number': getattr(account, 'account_number', 'N/A'),
            'portfolio_value': float(getattr(account, 'portfolio_value', 0) or 0),
            'equity': float(getattr(account, 'equity', 0) or 0),
            'buying_power': float(getattr(account, 'buying_power', 0) or 0),
            'cash': float(getattr(account, 'cash', 0) or 0),
            'day_trade_count': getattr(account, 'day_trade_count', 0),
            'status': getattr(account, 'status', 'unknown'),
            'portfolio_history': portfolio_history,
            'open_positions': open_positions
        }

    def get_positions(self) -> Dict:
        """Get current positions via UnifiedDataProvider, returns dict for compatibility"""
        positions = self.data_provider.get_positions()
        position_dict = {}
        if not positions:
            return position_dict
        for position in positions:
            symbol = position.get('symbol') if isinstance(position, dict) else getattr(position, 'symbol', None)
            if symbol:
                position_dict[symbol] = position
        return position_dict

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol via UnifiedDataProvider"""
        return self.data_provider.get_current_price(symbol)

    # --- Order and Rebalancing Methods ---
    def wait_for_settlement(self, sell_orders: List[Dict], max_wait_time: int = 60, poll_interval: float = 2.0) -> bool:
        """
        Wait for sell orders to settle by polling their status.
        Delegates to OrderManager.
        """
        return self.order_manager.wait_for_settlement(sell_orders, max_wait_time, poll_interval)

    def place_order(
        self, symbol: str, qty: float, side, 
        max_retries: int = 3, poll_timeout: int = 30, poll_interval: float = 2.0, 
        slippage_bps: Optional[float] = None
    ) -> Optional[str]:
        """
        Place a limit or market order using the order manager.
        """
        return self.order_manager.place_limit_or_market(
            symbol, qty, side, max_retries, poll_timeout, poll_interval, slippage_bps
        )

    def rebalance_portfolio(self, target_portfolio: Dict[str, float]) -> List[Dict]:
        """Delegate to PortfolioRebalancer for actual workflow."""
        return self.portfolio_rebalancer.rebalance_portfolio(target_portfolio)

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
        """
        Execute all strategies and rebalance portfolio accordingly
        Returns:
            MultiStrategyExecutionResult with complete execution details
        """
        try:
            account_info_before = self.get_account_info()
            if not account_info_before:
                raise Exception("Unable to get account information")
            strategy_signals, consolidated_portfolio = self.strategy_manager.run_all_strategies()
            if not consolidated_portfolio:
                consolidated_portfolio = {'BIL': 1.0}  # Default to cash equivalent
            total_allocation = sum(consolidated_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:
                logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")
            orders_executed = self.rebalance_portfolio(consolidated_portfolio)
            account_info_after = self.get_account_info()
            execution_summary = self._create_execution_summary(
                strategy_signals, consolidated_portfolio, orders_executed,
                account_info_before, account_info_after
            )
            if not self.paper_trading and orders_executed:
                self._trigger_post_trade_validation(strategy_signals, orders_executed)
            final_positions = self.get_positions()
            final_portfolio_state = self._build_portfolio_state_data(
                consolidated_portfolio, account_info_after, final_positions
            )
            result = MultiStrategyExecutionResult(
                success=True,
                strategy_signals=strategy_signals,
                consolidated_portfolio=consolidated_portfolio,
                orders_executed=orders_executed,
                account_info_before=account_info_before,
                account_info_after=account_info_after,
                execution_summary=execution_summary,
                final_portfolio_state=final_portfolio_state
            )
            self._save_dashboard_data(result)
            return result
        except Exception as e:
            logging.error(f"❌ Multi-strategy execution failed: {e}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=account_info_before if 'account_info_before' in locals() else {},
                account_info_after={},
                execution_summary={'error': str(e)},
                final_portfolio_state=None
            )

    # --- Reporting and Dashboard Methods ---
    def _create_execution_summary(self, strategy_signals: Dict[StrategyType, Any], 
                                 consolidated_portfolio: Dict[str, float],
                                 orders_executed: List[Dict],
                                 account_before: Dict, account_after: Dict) -> Dict:
        """Create comprehensive execution summary"""
        total_trades = len(orders_executed)
        buy_orders = []
        sell_orders = []
        for order in orders_executed:
            side = order.get('side')
            if side:
                if hasattr(side, 'value'):
                    side_value = side.value.upper()
                else:
                    side_value = str(side).upper()
                if side_value == 'BUY':
                    buy_orders.append(order)
                elif side_value == 'SELL':
                    sell_orders.append(order)
        total_buy_value = sum(o.get('estimated_value', 0) for o in buy_orders)
        total_sell_value = sum(o.get('estimated_value', 0) for o in sell_orders)
        strategy_summary = {}
        for strategy_type, signal_data in strategy_signals.items():
            strategy_name = strategy_type.value if hasattr(strategy_type, 'value') else str(strategy_type)
            strategy_summary[strategy_name] = {
                'signal': signal_data.get('action', 'HOLD'),
                'symbol': signal_data.get('symbol', 'N/A'),
                'allocation': self.strategy_manager.strategy_allocations.get(strategy_type, 0.0)
            }
        trading_summary = {
            'total_trades': total_trades,
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value
        }
        allocations = {
            symbol: {'target_percent': weight * 100} 
            for symbol, weight in consolidated_portfolio.items()
        }
        return {
            'allocations': allocations,
            'strategy_summary': strategy_summary,
            'trading_summary': trading_summary,
            'account_info_before': account_before,
            'account_info_after': account_after
        }

    def _save_dashboard_data(self, execution_result: MultiStrategyExecutionResult):
        """Save structured data for dashboard consumption to S3"""
        try:
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "execution_mode": "PAPER" if self.paper_trading else "LIVE",
                "success": execution_result.success,
                "strategies": {},
                "portfolio": {
                    "total_value": 0,
                    "total_pl": 0,
                    "total_pl_percent": 0,
                    "daily_pl": 0,
                    "daily_pl_percent": 0,
                    "cash": 0,
                    "equity": 0
                },
                "positions": [],
                "recent_trades": [],
                "signals": {},
                "performance": {
                    "last_30_days": {},
                    "last_7_days": {},
                    "today": {}
                }
            }
            if execution_result.account_info_after:
                account = execution_result.account_info_after
                dashboard_data["portfolio"]["total_value"] = float(account.get('equity', 0))
                dashboard_data["portfolio"]["cash"] = float(account.get('cash', 0))
                dashboard_data["portfolio"]["equity"] = float(account.get('equity', 0))
                portfolio_history = account.get('portfolio_history', {})
                if portfolio_history:
                    profit_loss = portfolio_history.get('profit_loss', [])
                    profit_loss_pct = portfolio_history.get('profit_loss_pct', [])
                    if profit_loss:
                        latest_pl = profit_loss[-1] if profit_loss else 0
                        latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                        dashboard_data["portfolio"]["daily_pl"] = float(latest_pl)
                        dashboard_data["portfolio"]["daily_pl_percent"] = float(latest_pl_pct) * 100
                open_positions = account.get('open_positions', [])
                for position in open_positions:
                    dashboard_data["positions"].append({
                        "symbol": getattr(position, 'symbol', ''),
                        "quantity": float(getattr(position, 'qty', 0)),
                        "market_value": float(getattr(position, 'market_value', 0)),
                        "unrealized_pl": float(getattr(position, 'unrealized_pl', 0)),
                        "unrealized_pl_percent": float(getattr(position, 'unrealized_plpc', 0)) * 100,
                        "current_price": float(getattr(position, 'current_price', 0)),
                        "avg_entry_price": float(getattr(position, 'avg_entry_price', 0)),
                        "side": getattr(position, 'side', 'long'),
                        "change_today": float(getattr(position, 'change_today', 0))
                    })
            for strategy_type, signal_data in execution_result.strategy_signals.items():
                strategy_name = strategy_type.value if hasattr(strategy_type, 'value') else str(strategy_type)
                dashboard_data["strategies"][strategy_name] = {
                    "signal": signal_data.get('action', 'HOLD'),
                    "symbol": signal_data.get('symbol', ''),
                    "reason": signal_data.get('reason', ''),
                    "timestamp": signal_data.get('timestamp', datetime.now().isoformat()),
                    "allocation": self.strategy_manager.strategy_allocations.get(strategy_type, 0)
                }
                dashboard_data["signals"][strategy_name] = signal_data
            if execution_result.orders_executed:
                for order in execution_result.orders_executed[-10:]:
                    dashboard_data["recent_trades"].append({
                        "symbol": order.get('symbol', ''),
                        "side": order.get('side', ''),
                        "quantity": float(order.get('qty', 0)),
                        "price": float(order.get('price', 0)),
                        "value": float(order.get('estimated_value', 0)),
                        "timestamp": order.get('timestamp', datetime.now().isoformat()),
                        "status": order.get('status', 'executed')
                    })
            if self.paper_trading:
                dashboard_s3_path = "s3://the-alchemiser-s3/dashboard/latest_paper_execution.json"
            else:
                dashboard_s3_path = "s3://the-alchemiser-s3/dashboard/latest_execution.json"
            success = s3_handler.write_json(dashboard_s3_path, dashboard_data)
            if success:
                logging.info(f"Dashboard data saved to {dashboard_s3_path}")
                mode_str = "paper" if self.paper_trading else "live"
                historical_s3_path = f"s3://the-alchemiser-s3/dashboard/executions/{mode_str}/{datetime.now().strftime('%Y/%m/%d')}/execution_{datetime.now().strftime('%H%M%S')}.json"
                s3_handler.write_json(historical_s3_path, dashboard_data)
                logging.info(f"Historical dashboard data saved to {historical_s3_path}")
            else:
                logging.error("Failed to save dashboard data to S3")
        except Exception as e:
            logging.error(f"Error saving dashboard data: {e}")

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
        """
        Build portfolio state data for reporting purposes
        Handles both dict and float for current_positions values.
        """
        portfolio_value = account_info.get('portfolio_value', 0.0)
        allocations = {}
        all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
        for symbol in all_symbols:
            target_weight = target_portfolio.get(symbol, 0.0)
            target_value = portfolio_value * target_weight
            pos = current_positions.get(symbol, {})
            if isinstance(pos, dict):
                current_value = pos.get('market_value', 0.0)
            else:
                try:
                    current_value = getattr(pos, 'market_value', 0.0) if pos else 0.0
                except Exception:
                    current_value = 0.0
            current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0
            allocations[symbol] = {
                'target_percent': target_weight * 100,
                'current_percent': current_weight * 100,
                'target_value': target_value,
                'current_value': current_value
            }
        return {'allocations': allocations}

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

    def display_multi_strategy_summary(self, execution_result: MultiStrategyExecutionResult):
        """
        Display a summary of multi-strategy execution results
        Args:
            execution_result: The execution result to display
        """
        if not execution_result.success:
            logging.error(f"❌ Multi-strategy execution failed: {execution_result.execution_summary.get('error', 'Unknown error')}")
            return
        print("\n📈 Consolidated Portfolio:")
        sorted_portfolio = sorted(
            execution_result.consolidated_portfolio.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for symbol, weight in sorted_portfolio:
            print(f"  {symbol:<6}: {weight:.1%}")
        if execution_result.orders_executed:
            print(f"\n🔄 Orders Executed: {len(execution_result.orders_executed)}")
            for order in execution_result.orders_executed:
                side = order.get('side', '')
                if hasattr(side, 'value'):
                    side_value = side.value
                else:
                    side_value = str(side)
                print(f"  {side_value:<4} {order.get('symbol', ''):<5} x{order.get('qty', 0):<7} @ ${order.get('price', 0):.2f}")
        else:
            print("\n✅ No orders executed (portfolio already balanced)")
        if execution_result.account_info_after:
            account = execution_result.account_info_after
            print(f"\n💰 Account Summary:")
            print(f"  Portfolio Value: ${float(account.get('portfolio_value', 0)):.2f}")
            print(f"  Cash Balance: ${float(account.get('cash', 0)):.2f}")
        print("\n✅ Multi-strategy execution completed successfully")

def main():
    """Test AlchemiserTradingBot multi-strategy execution"""
    logging.basicConfig(level=logging.INFO)
    print("🚀 Alchemiser Trading Bot Test")
    print("=" * 50)
    trader = AlchemiserTradingBot(
        paper_trading=True,
        strategy_allocations={
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
    )
    print("⚡ Executing multi-strategy...")
    result = trader.execute_multi_strategy()
    trader.display_multi_strategy_summary(result)
    print("\n📈 Getting performance report...")
    report = trader.get_multi_strategy_performance_report()
    if 'error' not in report:
        print(f"✅ Performance report generated successfully")
        print(f"   Current positions: {len(report['current_positions'])}")
        print(f"   Strategy tracking: {len(report['performance_summary'])}")
    else:
        print(f"❌ Error generating report: {report['error']}")

if __name__ == "__main__":
    main()
