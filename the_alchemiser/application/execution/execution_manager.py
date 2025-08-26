"""Coordinate execution of multiple trading strategies."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.application.trading.engine_service import TradingEngine

from the_alchemiser.application.mapping.execution_summary_mapping import (
    safe_dict_to_execution_summary_dto,
    safe_dict_to_portfolio_state_dto,
)
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    map_signals_dict as _map_signals_to_typed,
)
from the_alchemiser.domain.types import AccountInfo
from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.services.errors import handle_errors_with_retry
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)

from ..reporting.reporting import (
    build_portfolio_state_data,
    create_execution_summary,
    save_dashboard_data,
)


class ExecutionManager:
    """Orchestrates multi-strategy execution for the TradingEngine."""

    def __init__(self, engine: TradingEngine) -> None:
        """Store the trading engine used for order execution."""
        self.engine = engine

    @handle_errors_with_retry(operation="multi_strategy_execution", critical=True, max_retries=1)
    def execute_multi_strategy(self) -> MultiStrategyExecutionResultDTO:
        """Run all strategies and rebalance portfolio."""
        try:
            account_info_before = self.engine.get_account_info()
            if not account_info_before:
                raise TradingClientError(
                    "Unable to get account information",
                    context={
                        "operation": "get_account_info",
                        "engine": type(self.engine).__name__,
                    },
                )
            strategy_signals, consolidated_portfolio, strategy_attribution = (
                self.engine.strategy_manager.run_all_strategies()
            )
            # Always migrate strategy signals to typed (using typed domain)
            try:
                strategy_signals = _map_signals_to_typed(strategy_signals)
            except Exception as e:  # pragma: no cover - defensive
                logging.warning(f"Failed to map strategy signals to typed: {e}")
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

            # Enhanced validation: Orders with None IDs should no longer occur due to upstream fixes
            # If any are found, it indicates a serious execution pipeline failure that should be surfaced
            orders_with_none_ids = []
            valid_orders = []

            for order in orders_executed:
                if order and hasattr(order, "id") and order.id is not None:
                    valid_orders.append(order)
                else:
                    orders_with_none_ids.append(order)
                    logging.error(
                        "order_execution_none_id_detected",
                        extra={
                            "order": str(order),
                            "has_id_attr": hasattr(order, "id") if order else False,
                            "id_value": getattr(order, "id", "NO_ATTR") if order else "NULL_ORDER",
                        },
                    )

            if orders_with_none_ids:
                # This should not happen with our upstream fixes - surface as critical error
                error_msg = f"CRITICAL: {len(orders_with_none_ids)} orders executed with None IDs - execution pipeline failure"
                logging.critical(error_msg)
                raise TradingClientError(
                    error_msg,
                    context={
                        "failed_orders_count": len(orders_with_none_ids),
                        "valid_orders_count": len(valid_orders),
                        "failed_orders": [str(o) for o in orders_with_none_ids],
                    },
                )

            orders_executed = valid_orders
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
            result = MultiStrategyExecutionResultDTO(
                success=True,
                strategy_signals=strategy_signals,
                consolidated_portfolio=consolidated_portfolio,
                orders_executed=orders_executed,
                account_info_before=account_info_before,
                account_info_after=account_info_after,
                execution_summary=safe_dict_to_execution_summary_dto(execution_summary),
                final_portfolio_state=safe_dict_to_portfolio_state_dto(final_portfolio_state),
            )
            save_dashboard_data(self.engine, result)
            self.engine._archive_daily_strategy_pnl(execution_summary.get("pnl_summary", {}))
            return result
        except TradingClientError as e:
            from the_alchemiser.infrastructure.logging.logging_utils import (
                get_logger,
                log_error_with_context,
            )

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "multi_strategy_execution",
                engine_type=type(self.engine).__name__,
                error_type="trading_client_error",
            )
            raise  # Re-raise to let upper layers handle
        except DataProviderError as e:
            from the_alchemiser.infrastructure.logging.logging_utils import (
                get_logger,
                log_error_with_context,
            )

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "multi_strategy_execution",
                engine_type=type(self.engine).__name__,
                error_type="data_provider_error",
            )
            # For data errors, return a safe result rather than crashing
            # Create empty/error AccountInfo for error cases
            empty_account_info: AccountInfo = {
                "account_id": "error",
                "equity": 0.0,
                "cash": 0.0,
                "buying_power": 0.0,
                "day_trades_remaining": 0,
                "portfolio_value": 0.0,
                "last_equity": 0.0,
                "daytrading_buying_power": 0.0,
                "regt_buying_power": 0.0,
                "status": "INACTIVE",
            }

            return MultiStrategyExecutionResultDTO(
                success=False,
                strategy_signals={},
                consolidated_portfolio={"BIL": 1.0},  # Safe fallback to cash
                orders_executed=[],
                account_info_before=empty_account_info,
                account_info_after=empty_account_info,
                execution_summary=safe_dict_to_execution_summary_dto(
                    {
                        "error": str(e),
                        "mode": "error",
                        "account_info_before": empty_account_info,
                        "account_info_after": empty_account_info,
                    }
                ),
                final_portfolio_state=safe_dict_to_portfolio_state_dto({}),
            )
        except (
            ConfigurationError,
            StrategyExecutionError,
            ValueError,
            AttributeError,
        ) as e:
            from the_alchemiser.infrastructure.logging.logging_utils import (
                get_logger,
                log_error_with_context,
            )

            logger = get_logger(__name__)
            # Configuration and strategy errors are critical
            log_error_with_context(
                logger,
                e,
                "multi_strategy_execution",
                engine_type=type(self.engine).__name__,
                error_type=type(e).__name__,
            )
            # Convert to our exception type for better handling
            raise TradingClientError(
                f"Configuration/strategy error in multi-strategy execution: {e!s}",
                context={
                    "original_error": type(e).__name__,
                    "operation": "multi_strategy_execution",
                },
            ) from e
