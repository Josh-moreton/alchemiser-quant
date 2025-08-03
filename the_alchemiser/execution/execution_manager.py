import logging
from typing import Dict, List, Any

from the_alchemiser.core.trading.strategy_manager import StrategyType
from .reporting import create_execution_summary, save_dashboard_data, build_portfolio_state_data
from .types import MultiStrategyExecutionResult


class ExecutionManager:
    """Orchestrates multi-strategy execution for the TradingEngine."""

    def __init__(self, engine):
        self.engine = engine

    def execute_multi_strategy(self):
        """Run all strategies and rebalance portfolio."""
        try:
            account_info_before = self.engine.get_account_info()
            if not account_info_before:
                raise Exception("Unable to get account information")
            strategy_signals, consolidated_portfolio, strategy_attribution = (
                self.engine.strategy_manager.run_all_strategies()
            )
            if not consolidated_portfolio:
                consolidated_portfolio = {"BIL": 1.0}
            total_allocation = sum(consolidated_portfolio.values())
            if abs(total_allocation - 1.0) > 0.05:
                logging.warning(
                    f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%"
                )
            orders_executed = self.engine.rebalance_portfolio(
                consolidated_portfolio, strategy_attribution
            )
            account_info_after = self.engine.get_account_info()
            execution_summary = create_execution_summary(
                self.engine,
                strategy_signals,
                consolidated_portfolio,
                orders_executed,
                account_info_before,
                account_info_after,
            )
            if not self.engine.paper_trading and orders_executed:
                self.engine._trigger_post_trade_validation(strategy_signals, orders_executed)
            final_positions = self.engine.get_positions()
            final_portfolio_state = build_portfolio_state_data(
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
                final_portfolio_state=final_portfolio_state,
            )
            save_dashboard_data(self.engine, result)
            self.engine._archive_daily_strategy_pnl(execution_summary.get("pnl_summary", {}))
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
                account_info_before=account_info_before if "account_info_before" in locals() else {},
                account_info_after={},
                execution_summary={"error": str(e)},
                final_portfolio_state=None,
            )
