#!/usr/bin/env python3
"""
Multi-Strategy Alpaca Trader

Enhanced Alpaca trading integration that supports multiple strategy execution
with proper position tracking and allocation management.

Key Features:
- Multi-strategy portfolio execution
- Position tracking per strategy
- Consolidated portfolio rebalancing
- Strategy performance attribution
- Enhanced reporting and logging
- Post-trade indicator validation (live trading only)
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
from the_alchemiser.execution.alpaca_trader import AlpacaTradingBot


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


class MultiStrategyAlpacaTrader(AlpacaTradingBot):
    """Enhanced Alpaca trader with multi-strategy support"""
    
    def __init__(self, paper_trading: bool = True, strategy_allocations: Optional[Dict[StrategyType, float]] = None, 
                 ignore_market_hours: bool = False, config=None):
        """
        Initialize multi-strategy Alpaca trader
        
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
        
        super().__init__(paper_trading=paper_trading, ignore_market_hours=ignore_market_hours, config=config)
        
        # Initialize strategy manager
        self.strategy_manager = MultiStrategyManager(strategy_allocations, config=config)
        
        # Store config reference
        self.config = config
        
        # Logging setup - always use config for log path
        self.multi_strategy_log = self.config['logging'].get('multi_strategy_log', 'data/logs/multi_strategy_execution.log')
    
    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """
        Execute all strategies and rebalance portfolio accordingly
        
        Returns:
            MultiStrategyExecutionResult with complete execution details
        """
        try:
            # Get account info before execution
            account_info_before = self.get_account_info()
            if not account_info_before:
                raise Exception("Unable to get account information")
            
            # Run all strategies
            strategy_signals, consolidated_portfolio = self.strategy_manager.run_all_strategies()
            
            # Validate consolidated portfolio
            if not consolidated_portfolio:
                consolidated_portfolio = {'BIL': 1.0}  # Default to cash equivalent
            
            total_allocation = sum(consolidated_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:
                logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")
            
            # Execute portfolio rebalancing
            orders_executed = self.rebalance_portfolio_with_tracking(consolidated_portfolio, strategy_signals)
            
            # Get account info after execution
            account_info_after = self.get_account_info()
            
            # Create execution summary
            execution_summary = self._create_execution_summary(
                strategy_signals, consolidated_portfolio, orders_executed,
                account_info_before, account_info_after
            )
            
            # Log execution details
            self._log_multi_strategy_execution(execution_summary)
            
            # Post-trade validation (live trading only)
            if not self.paper_trading and orders_executed:
                self._trigger_post_trade_validation(strategy_signals, orders_executed)
            
            # Capture final portfolio state for reporting
            final_positions = self.get_positions()
            final_portfolio_state = self._build_portfolio_state_data(
                consolidated_portfolio, account_info_after, final_positions
            )
            
            # Create result object
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
            
            # Save dashboard data to S3
            self._save_dashboard_data(result)
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Multi-strategy execution failed: {e}")
            import traceback
            logging.error(f"Stack trace: {traceback.format_exc()}")
            
            # Return failed result
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
    
    def rebalance_portfolio_with_tracking(self, target_portfolio: Dict[str, float], 
                                        strategy_signals: Dict[StrategyType, Any]) -> List[Dict]:
        """
        Simple wrapper for rebalancing, no strategy order tracking.
        """
        return super().rebalance_portfolio(target_portfolio)
    
    
    
    def _create_execution_summary(self, strategy_signals: Dict[StrategyType, Any], 
                                 consolidated_portfolio: Dict[str, float],
                                 orders_executed: List[Dict],
                                 account_before: Dict, account_after: Dict) -> Dict:
        """Create comprehensive execution summary"""
        
        # Analyze orders
        total_trades = len(orders_executed)
        buy_orders = []
        sell_orders = []
        
        for order in orders_executed:
            side = order.get('side')
            if side:
                # Handle both string and enum values - normalize to uppercase for comparison
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
        
        # Strategy allocation summary
        strategy_allocations = {}
        for strategy_type, allocation in self.strategy_manager.strategy_allocations.items():
            signal = strategy_signals.get(strategy_type, {})
            strategy_allocations[strategy_type.value] = {
                'allocation': allocation,
                'signal': f"{signal.get('action', 'HOLD')} {signal.get('symbol', 'N/A')}",
                'reason': signal.get('reason', 'No signal')
            }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'execution_mode': 'PAPER' if self.paper_trading else 'LIVE',
            'strategy_summary': strategy_allocations,
            'portfolio_allocation': consolidated_portfolio,
            'trading_summary': {
                'total_trades': total_trades,
                'buy_orders': len(buy_orders),
                'sell_orders': len(sell_orders),
                'total_buy_value': total_buy_value,
                'total_sell_value': total_sell_value,
                'net_trading_value': total_buy_value - total_sell_value
            },
            'orders_executed': orders_executed
        }
    
    def _log_multi_strategy_execution(self, execution_summary: Dict):
        """Log detailed execution summary to file"""
        try:
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            
            if self.multi_strategy_log.startswith('s3://'):
                # Log to S3
                s3_handler.append_text(self.multi_strategy_log, json.dumps(execution_summary, indent=2, default=str) + '\n')
            else:
                # Log to local file
                import os
                os.makedirs(os.path.dirname(self.multi_strategy_log), exist_ok=True)
                with open(self.multi_strategy_log, 'a') as f:
                    f.write(json.dumps(execution_summary, indent=2, default=str) + '\n')
            
            # Only log to file, no terminal output
            logging.info(f"Multi-strategy execution logged to {self.multi_strategy_log}")
            
        except Exception as e:
            logging.error(f"Error logging multi-strategy execution: {e}")
    
    def _save_dashboard_data(self, execution_result: MultiStrategyExecutionResult):
        """Save structured data for dashboard consumption to S3"""
        try:
            from the_alchemiser.core.utils.s3_utils import get_s3_handler
            s3_handler = get_s3_handler()
            
            # Create dashboard-specific data structure
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
            
            # Extract portfolio data from account info
            if execution_result.account_info_after:
                account = execution_result.account_info_after
                dashboard_data["portfolio"]["total_value"] = float(account.get('equity', 0))
                dashboard_data["portfolio"]["cash"] = float(account.get('cash', 0))
                dashboard_data["portfolio"]["equity"] = float(account.get('equity', 0))
                
                # Extract portfolio history if available
                portfolio_history = account.get('portfolio_history', {})
                if portfolio_history:
                    profit_loss = portfolio_history.get('profit_loss', [])
                    profit_loss_pct = portfolio_history.get('profit_loss_pct', [])
                    
                    if profit_loss:
                        latest_pl = profit_loss[-1] if profit_loss else 0
                        latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                        
                        dashboard_data["portfolio"]["daily_pl"] = float(latest_pl)
                        dashboard_data["portfolio"]["daily_pl_percent"] = float(latest_pl_pct) * 100
                
                # Extract open positions
                open_positions = account.get('open_positions', [])
                for position in open_positions:
                    dashboard_data["positions"].append({
                        "symbol": position.get('symbol', ''),
                        "quantity": float(position.get('qty', 0)),
                        "market_value": float(position.get('market_value', 0)),
                        "unrealized_pl": float(position.get('unrealized_pl', 0)),
                        "unrealized_pl_percent": float(position.get('unrealized_plpc', 0)) * 100,
                        "current_price": float(position.get('current_price', 0)),
                        "avg_entry_price": float(position.get('avg_entry_price', 0)),
                        "side": position.get('side', 'long'),
                        "change_today": float(position.get('change_today', 0))
                    })
            
            # Extract strategy information
            for strategy_type, signal_data in execution_result.strategy_signals.items():
                strategy_name = strategy_type.value if hasattr(strategy_type, 'value') else str(strategy_type)
                dashboard_data["strategies"][strategy_name] = {
                    "signal": signal_data.get('action', 'HOLD'),
                    "symbol": signal_data.get('symbol', ''),
                    "reason": signal_data.get('reason', ''),
                    "timestamp": signal_data.get('timestamp', datetime.now().isoformat()),
                    "allocation": self.strategy_manager.strategy_allocations.get(strategy_type, 0)
                }
                
                # Store detailed signal data
                dashboard_data["signals"][strategy_name] = signal_data
            
            # Extract recent trades from execution
            if execution_result.orders_executed:
                for order in execution_result.orders_executed[-10:]:  # Last 10 trades
                    dashboard_data["recent_trades"].append({
                        "symbol": order.get('symbol', ''),
                        "side": order.get('side', ''),
                        "quantity": float(order.get('qty', 0)),
                        "price": float(order.get('price', 0)),
                        "value": float(order.get('estimated_value', 0)),
                        "timestamp": order.get('timestamp', datetime.now().isoformat()),
                        "status": order.get('status', 'executed')
                    })
            
            # Save to S3 bucket for dashboard consumption
            dashboard_s3_path = "s3://the-alchemiser-s3/dashboard/latest_execution.json"
            success = s3_handler.write_json(dashboard_s3_path, dashboard_data)
            
            if success:
                logging.info(f"Dashboard data saved to {dashboard_s3_path}")
                
                # Also save historical data with timestamp
                historical_s3_path = f"s3://the-alchemiser-s3/dashboard/executions/{datetime.now().strftime('%Y/%m/%d')}/execution_{datetime.now().strftime('%H%M%S')}.json"
                s3_handler.write_json(historical_s3_path, dashboard_data)
                logging.info(f"Historical dashboard data saved to {historical_s3_path}")
            else:
                logging.error("Failed to save dashboard data to S3")
                
        except Exception as e:
            logging.error(f"Error saving dashboard data: {e}")
    
    def get_multi_strategy_performance_report(self) -> Dict:
        """Generate comprehensive performance report for all strategies"""
        try:
            # Get current positions from Alpaca
            current_positions = self.get_positions()
            
            # Create comprehensive report
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
    
    def _build_portfolio_state_data(self, target_portfolio: Dict[str, float], 
                                   account_info: Dict, current_positions: Dict) -> Dict:
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
            # If pos is a dict, get 'market_value', else assume it's a float
            if isinstance(pos, dict):
                current_value = pos.get('market_value', 0.0)
            else:
                try:
                    current_value = float(pos) if pos else 0.0
                except Exception:
                    current_value = 0.0
            current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0
            allocations[symbol] = {
                'target_percent': target_weight * 100,
                'current_percent': current_weight * 100,
                'target_value': target_value,
                'current_value': current_value
            }
        return {
            'total_value': portfolio_value,
            'allocations': allocations
        }
    
    def display_multi_strategy_summary(self, execution_result: MultiStrategyExecutionResult):
        """Display comprehensive summary of multi-strategy execution using rich formatting"""
        from the_alchemiser.core.ui.cli_formatter import (
            render_strategy_signals, render_portfolio_allocation, 
            render_trading_summary, render_header, render_footer
        )

        if not execution_result.success:
            render_header("❌ EXECUTION FAILED", "Multi-Strategy Trading")
            from rich.console import Console
            Console().print(f"[bold red]Error: {execution_result.execution_summary.get('error', 'Unknown error')}[/bold red]")
            return

        summary = execution_result.execution_summary

        # Display strategy signals
        render_strategy_signals(execution_result.strategy_signals)

        # Display actual portfolio allocation after trades, if available
        if execution_result.final_portfolio_state and 'allocations' in execution_result.final_portfolio_state:
            # Convert the final portfolio state to the format expected by render_portfolio_allocation
            allocations = execution_result.final_portfolio_state['allocations']
            current_portfolio = {
                symbol: data['current_percent'] / 100.0 
                for symbol, data in allocations.items() 
                if data['current_percent'] > 0.1  # Only show positions > 0.1%
            }
            if current_portfolio:
                render_portfolio_allocation(current_portfolio, "🏁 CURRENT PORTFOLIO ALLOCATION")
            else:
                render_portfolio_allocation(execution_result.consolidated_portfolio)
        else:
            render_portfolio_allocation(execution_result.consolidated_portfolio)

        # Display trading summary using executed orders
        render_trading_summary(execution_result.orders_executed)

        render_footer("Operation completed successfully!")
    
    def _trigger_post_trade_validation(self, strategy_signals: Dict[StrategyType, Any], 
                                     orders_executed: List[Dict]):
        """
        Trigger post-trade technical indicator validation for live trading
        
        Args:
            strategy_signals: Strategy signals that led to trades
            orders_executed: List of executed orders
        """
        try:
            
            # Extract symbols from strategy signals that were actually used
            nuclear_symbols = []
            tecl_symbols = []
            
            # Get symbols from strategy signals
            for strategy_type, signal in strategy_signals.items():
                symbol = signal.get('symbol')
                if symbol and symbol != 'NUCLEAR_PORTFOLIO' and symbol != 'BEAR_PORTFOLIO':
                    if strategy_type == StrategyType.NUCLEAR:
                        nuclear_symbols.append(symbol)
                    elif strategy_type == StrategyType.TECL:
                        tecl_symbols.append(symbol)
            
            # Also include symbols from executed orders to ensure we validate everything traded
            order_symbols = {order['symbol'] for order in orders_executed if 'symbol' in order}
            
            # Map order symbols to strategies based on our known strategy symbols
            nuclear_strategy_symbols = ['SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX', 'UVXY', 'BTAL', 
                                      'QQQ', 'SQQQ', 'PSQ', 'UPRO', 'TLT', 'IEF', 
                                      'SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO']
            tecl_strategy_symbols = ['XLK', 'KMLM', 'SPXL', 'TECL', 'BIL', 'BSV', 'UVXY', 'SQQQ']
            
            for symbol in order_symbols:
                if symbol in nuclear_strategy_symbols and symbol not in nuclear_symbols:
                    nuclear_symbols.append(symbol)
                elif symbol in tecl_strategy_symbols and symbol not in tecl_symbols:
                    tecl_symbols.append(symbol)
            
            # Remove duplicates and limit to avoid rate limits
            nuclear_symbols = list(set(nuclear_symbols))[:5]  # Limit to 5 symbols per strategy
            tecl_symbols = list(set(tecl_symbols))[:5]
            
            if nuclear_symbols or tecl_symbols:
                logging.info(f"🔍 Triggering post-trade validation for Nuclear: {nuclear_symbols}, TECL: {tecl_symbols}")
                # Post-trade validation temporarily disabled
            else:
                logging.info("🔍 No symbols to validate in post-trade validation")
                
        except Exception as e:
            logging.error(f"❌ Post-trade validation failed: {e}")
            # Don't raise - validation failure shouldn't affect trading


def main():
    """Test multi-strategy execution"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Multi-Strategy Alpaca Trader Test")
    print("=" * 50)
    
    # Initialize trader with paper trading
    trader = MultiStrategyAlpacaTrader(
        paper_trading=True,
        strategy_allocations={
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }
    )
    
    # Execute multi-strategy
    print("⚡ Executing multi-strategy...")
    result = trader.execute_multi_strategy()
    
    # Display results
    trader.display_multi_strategy_summary(result)
    
    # Get performance report
    print("\n📈 Getting performance report...")
    report = trader.get_multi_strategy_performance_report()
    
    if 'error' not in report:
        print(f"✅ Performance report generated successfully")
        print(f"   Current positions: {len(report['current_positions'])}")
        print(f"   Strategy tracking: {len(report['strategy_position_tracking'])}")
    else:
        print(f"❌ Error generating report: {report['error']}")


if __name__ == "__main__":
    main()
