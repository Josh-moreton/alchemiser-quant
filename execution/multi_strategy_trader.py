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
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from core.config import Config
from core.strategy_manager import MultiStrategyManager, StrategyType
from core.strategy_order_tracker import StrategyOrderTracker
from execution.alpaca_trader import AlpacaTradingBot


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


class MultiStrategyAlpacaTrader(AlpacaTradingBot):
    """Enhanced Alpaca trader with multi-strategy support"""
    
    def __init__(self, paper_trading: bool = True, strategy_allocations: Optional[Dict[StrategyType, float]] = None):
        """
        Initialize multi-strategy Alpaca trader
        
        Args:
            paper_trading: Whether to use paper trading account
            strategy_allocations: Portfolio allocation between strategies
        """
        super().__init__(paper_trading=paper_trading)
        
        # Initialize strategy manager
        self.strategy_manager = MultiStrategyManager(strategy_allocations)
        
        # Initialize order tracker
        self.order_tracker = StrategyOrderTracker()
        
        # Configuration
        self.config = Config()
        
        # Logging setup
        self.multi_strategy_log = self.config['logging'].get('multi_strategy_log', 
                                                            'data/logs/multi_strategy_execution.log')
        
        logging.info(f"MultiStrategyAlpacaTrader initialized with allocations: {self.strategy_manager.strategy_allocations}")
        logging.info(f"Order tracking enabled: {self.order_tracker.orders_file}")
    
    def execute_multi_strategy(self) -> MultiStrategyExecutionResult:
        """
        Execute all strategies and rebalance portfolio accordingly
        
        Returns:
            MultiStrategyExecutionResult with complete execution details
        """
        try:
            logging.info("🚀 Starting multi-strategy execution")
            
            # Get account info before execution
            account_info_before = self.get_account_info()
            if not account_info_before:
                raise Exception("Unable to get account information")
            
            logging.info(f"Account value before execution: ${account_info_before.get('portfolio_value', 0):,.2f}")
            
            # Run all strategies
            logging.info("📊 Running all strategies...")
            strategy_signals, consolidated_portfolio = self.strategy_manager.run_all_strategies()
            
            # Log strategy results
            for strategy_type, signal in strategy_signals.items():
                logging.info(f"{strategy_type.value} Strategy: {signal['action']} {signal['symbol']} - {signal['reason']}")
            
            # Validate consolidated portfolio
            if not consolidated_portfolio:
                logging.warning("No positions recommended by any strategy - holding cash")
                consolidated_portfolio = {'BIL': 1.0}  # Default to cash equivalent
            
            total_allocation = sum(consolidated_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:
                logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")
            
            logging.info(f"Consolidated portfolio: {consolidated_portfolio}")
            
            # Execute portfolio rebalancing
            logging.info("⚡ Executing portfolio rebalancing...")
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
            
            # Create result object
            result = MultiStrategyExecutionResult(
                success=True,
                strategy_signals=strategy_signals,
                consolidated_portfolio=consolidated_portfolio,
                orders_executed=orders_executed,
                account_info_before=account_info_before,
                account_info_after=account_info_after,
                execution_summary=execution_summary
            )
            
            logging.info("✅ Multi-strategy execution completed successfully")
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
                execution_summary={'error': str(e)}
            )
    
    def rebalance_portfolio_with_tracking(self, target_portfolio: Dict[str, float], 
                                        strategy_signals: Dict[StrategyType, Any]) -> List[Dict]:
        """
        Enhanced portfolio rebalancing with strategy order tracking
        
        Args:
            target_portfolio: Target allocations by symbol
            strategy_signals: Strategy signals that led to these allocations
            
        Returns:
            List of executed orders with strategy attribution
        """
        try:
            logging.info("🔄 Starting portfolio rebalancing with strategy tracking...")
            
            # First, update our position tracking with current Alpaca state
            current_positions = self.get_positions()
            if current_positions:
                strategy_positions = self.order_tracker.reconcile_positions_with_alpaca(current_positions)
                logging.info(f"Reconciled positions across {len(strategy_positions)} strategies")
            
            # Execute parent class rebalancing
            orders_executed = super().rebalance_portfolio(target_portfolio)
            
            # Enhanced order tracking with strategy attribution
            for order in orders_executed:
                if order.get('order_id'):
                    # Determine which strategy(ies) drove this order
                    contributing_strategies = self._determine_order_strategy(
                        order['symbol'], order['side'], strategy_signals
                    )
                    
                    for strategy_type in contributing_strategies:
                        reason = strategy_signals.get(strategy_type, {}).get('reason', 'Multi-strategy rebalancing')
                        
                        # Record the order with strategy attribution
                        self.order_tracker.record_order(
                            order_id=order['order_id'],
                            strategy_type=strategy_type,
                            symbol=order['symbol'],
                            side=order['side'].value if hasattr(order['side'], 'value') else str(order['side']),
                            quantity=order['qty'],
                            price=order.get('price'),
                            reason=reason
                        )
                        
                        logging.info(f"Tracked order {order['order_id']} for {strategy_type.value}: "
                                   f"{order['side']} {order['qty']} {order['symbol']}")
            
            # Clean up old orders periodically
            if len(orders_executed) > 0:
                cleaned_orders = self.order_tracker.cleanup_old_orders(days_to_keep=90)
                if cleaned_orders > 0:
                    logging.info(f"Cleaned up {cleaned_orders} old order records")
            
            return orders_executed
            
        except Exception as e:
            logging.error(f"Error in enhanced portfolio rebalancing: {e}")
            # Fallback to parent method
            return super().rebalance_portfolio(target_portfolio)
    
    def _determine_order_strategy(self, symbol: str, side: Any, 
                                strategy_signals: Dict[StrategyType, Any]) -> List[StrategyType]:
        """
        Determine which strategy(ies) are responsible for an order
        
        Args:
            symbol: Symbol being traded
            side: Order side (BUY/SELL)
            strategy_signals: Current strategy signals
            
        Returns:
            List of strategies that contributed to this order
        """
        contributing_strategies = []
        
        side_str = side.value if hasattr(side, 'value') else str(side)
        
        for strategy_type, signal in strategy_signals.items():
            signal_symbol = signal.get('symbol', '')
            signal_action = signal.get('action', 'HOLD')
            
            # Direct symbol match
            if signal_symbol == symbol:
                if (signal_action == 'BUY' and side_str == 'BUY') or \
                   (signal_action == 'SELL' and side_str == 'SELL'):
                    contributing_strategies.append(strategy_type)
            
            # Cash/defensive position logic
            elif symbol in ['BIL', 'SHY', 'CASH'] and signal_action in ['SELL', 'HOLD']:
                # Defensive positions can be attributed to any strategy going defensive
                contributing_strategies.append(strategy_type)
        
        # If no specific attribution found, attribute to all active strategies
        # (for rebalancing orders that maintain overall portfolio structure)
        if not contributing_strategies:
            contributing_strategies = list(strategy_signals.keys())
        
        return contributing_strategies
    
    def get_strategy_attribution_report(self) -> Dict:
        """Get detailed strategy attribution and performance report"""
        try:
            current_positions = self.get_positions()
            strategy_attribution = self.order_tracker.get_strategy_attribution()
            
            # Reconcile with current positions if we have any
            if current_positions:
                strategy_positions = self.order_tracker.reconcile_positions_with_alpaca(current_positions)
            else:
                strategy_positions = {strategy.value: [] for strategy in StrategyType}
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_portfolio_value': sum(pos.get('market_value', 0) for pos in current_positions.values()),
                'strategy_attribution': strategy_attribution,
                'detailed_positions': strategy_positions,
                'strategy_allocations': {
                    strategy.value: allocation 
                    for strategy, allocation in self.strategy_manager.strategy_allocations.items()
                }
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating strategy attribution report: {e}")
            return {'error': str(e)}
    
    def _create_execution_summary(self, strategy_signals: Dict[StrategyType, Any], 
                                 consolidated_portfolio: Dict[str, float],
                                 orders_executed: List[Dict],
                                 account_before: Dict, account_after: Dict) -> Dict:
        """Create comprehensive execution summary"""
        
        # Calculate portfolio changes
        portfolio_value_before = account_before.get('portfolio_value', 0)
        portfolio_value_after = account_after.get('portfolio_value', 0)
        value_change = portfolio_value_after - portfolio_value_before
        value_change_pct = (value_change / portfolio_value_before * 100) if portfolio_value_before > 0 else 0
        
        # Analyze orders
        total_trades = len(orders_executed)
        buy_orders = [o for o in orders_executed if o.get('side') == 'BUY' or (hasattr(o.get('side'), 'value') and o['side'].value == 'BUY')]
        sell_orders = [o for o in orders_executed if o.get('side') == 'SELL' or (hasattr(o.get('side'), 'value') and o['side'].value == 'SELL')]
        
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
            'account_summary': {
                'portfolio_value_before': portfolio_value_before,
                'portfolio_value_after': portfolio_value_after,
                'value_change': value_change,
                'value_change_pct': value_change_pct,
                'cash_before': account_before.get('cash', 0),
                'cash_after': account_after.get('cash', 0)
            },
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
            from core.s3_utils import get_s3_handler
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
            
            logging.info(f"Multi-strategy execution logged to {self.multi_strategy_log}")
            
        except Exception as e:
            logging.error(f"Error logging multi-strategy execution: {e}")
    
    def get_multi_strategy_performance_report(self) -> Dict:
        """Generate comprehensive performance report for all strategies"""
        try:
            # Get current positions from Alpaca
            current_positions = self.get_positions()
            
            # Get strategy position tracking
            strategy_positions = self.strategy_manager.get_current_positions()
            
            # Get account information
            account_info = self.get_account_info()
            
            # Create comprehensive report
            report = {
                'timestamp': datetime.now().isoformat(),
                'account_summary': {
                    'portfolio_value': account_info.get('portfolio_value', 0),
                    'buying_power': account_info.get('buying_power', 0),
                    'cash': account_info.get('cash', 0),
                    'paper_trading': self.paper_trading
                },
                'strategy_allocations': {
                    k.value: v for k, v in self.strategy_manager.strategy_allocations.items()
                },
                'current_positions': current_positions,
                'strategy_position_tracking': {
                    strategy.value: [pos.to_dict() for pos in positions]
                    for strategy, positions in strategy_positions.items()
                },
                'performance_summary': self.strategy_manager.get_strategy_performance_summary()
            }
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    def display_multi_strategy_summary(self, execution_result: MultiStrategyExecutionResult):
        """Display comprehensive summary of multi-strategy execution"""
        print("\n" + "="*80)
        print("🎯 MULTI-STRATEGY EXECUTION SUMMARY")
        print("="*80)
        
        if not execution_result.success:
            print("❌ EXECUTION FAILED")
            print(f"Error: {execution_result.execution_summary.get('error', 'Unknown error')}")
            return
        
        summary = execution_result.execution_summary
        
        # Account changes
        account = summary['account_summary']
        print(f"💰 Account Performance:")
        print(f"   Portfolio Value: ${account['portfolio_value_before']:,.2f} → ${account['portfolio_value_after']:,.2f}")
        print(f"   Change: ${account['value_change']:+,.2f} ({account['value_change_pct']:+.2f}%)")
        print(f"   Mode: {summary['execution_mode']}")
        
        # Strategy signals
        print(f"\n📊 Strategy Signals:")
        for strategy, details in summary['strategy_summary'].items():
            print(f"   {strategy} ({details['allocation']:.0%}): {details['signal']}")
            print(f"      └─ {details['reason']}")
        
        # Portfolio allocation
        print(f"\n🎯 Final Portfolio Allocation:")
        for symbol, weight in execution_result.consolidated_portfolio.items():
            print(f"   {symbol}: {weight:.1%}")
        
        # Trading summary
        trading = summary['trading_summary']
        if trading['total_trades'] > 0:
            print(f"\n⚡ Trading Activity:")
            print(f"   Total Trades: {trading['total_trades']} ({trading['buy_orders']} buys, {trading['sell_orders']} sells)")
            print(f"   Buy Value: ${trading['total_buy_value']:,.2f}")
            print(f"   Sell Value: ${trading['total_sell_value']:,.2f}")
            print(f"   Net Activity: ${trading['net_trading_value']:+,.2f}")
        else:
            print(f"\n⚡ No trades needed - portfolio already aligned")
        
        print("="*80)


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
