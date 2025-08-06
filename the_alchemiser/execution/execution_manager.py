import logging

from ..core.error_handler import handle_errors_with_retry
from ..core.exceptions import (
    TradingClientError,
)
from .reporting import build_portfolio_state_data, create_execution_summary, save_dashboard_data
from .types import MultiStrategyExecutionResult


class ExecutionManager:
    """Orchestrates multi-strategy execution for the TradingEngine."""

    def __init__(self, engine) -> None:
        self.engine = engine

    @handle_errors_with_retry(operation="multi_strategy_execution", critical=True, max_retries=1)
    def execute_multi_strategy(self):
        """Run all strategies and rebalance portfolio."""
        try:
            account_info_before = self.engine.get_account_info()
            if not account_info_before:
                raise TradingClientError(
                    "Unable to get account information",
                    context={"operation": "get_account_info", "engine": type(self.engine).__name__},
                )
            strategy_signals, consolidated_portfolio, strategy_attribution = (
                self.engine.strategy_manager.run_all_strategies()
            )
            if not consolidated_portfolio:
                consolidated_portfolio = {"BIL": 1.0}
                logging.info("No portfolio signals generated, defaulting to cash (BIL)")

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
            from the_alchemiser.core.logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(logger, e, "multi-strategy execution")
            return MultiStrategyExecutionResult(
                success=False,
                strategy_signals={},
                consolidated_portfolio={},
                orders_executed=[],
                account_info_before=(
                    account_info_before if "account_info_before" in locals() else {}
                ),
                account_info_after={},
                execution_summary={"error": str(e)},
                final_portfolio_state=None,
            )
