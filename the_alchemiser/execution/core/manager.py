"""Business Unit: execution; Status: current.

Coordinate execution of multiple trading strategies.

This module implements the MultiStrategyExecutor protocol for strategy orchestration.
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.execution.execution_protocols import MultiStrategyExecutor
from the_alchemiser.shared.errors.error_handler import handle_errors_with_retry
from the_alchemiser.shared.logging.logging_utils import (
    log_data_transfer_checkpoint,
    log_trade_expectation_vs_reality,
)
from the_alchemiser.shared.mappers.execution_summary_mapping import (
    dict_to_execution_summary_dto,
    dict_to_portfolio_state_dto,
)
from the_alchemiser.shared.reporting.reporting import (
    build_portfolio_state_data,
    create_execution_summary,
    save_dashboard_data,
)
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.shared.types.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.value_objects.core_types import AccountInfo
from the_alchemiser.strategy.mappers.mappers import (
    map_signals_dict as _map_signals_to_typed,
)


class ExecutionManager(MultiStrategyExecutor):
    """Orchestrates multi-strategy execution for the TradingEngine.

    Implements the MultiStrategyExecutor protocol for strategy coordination
    and portfolio rebalancing. This is the proper class to use for running
    multiple strategies and coordinating portfolio rebalancing.

    Flow: ExecutionManager → engine.strategy_manager.run_all_strategies()
          → engine.rebalance_portfolio() → broker services via facade
    """

    def __init__(self, engine: Any) -> None:
        """Store the trading engine used for order execution."""
        self.engine = engine

    def _process_strategy_signals(self, strategy_signals: Any) -> dict[str, Any]:
        """Process and convert strategy signals to string-keyed format."""
        # === UNIVERSAL STRATEGY SIGNAL TRACKING ===
        logging.info("=== _PROCESS_STRATEGY_SIGNALS ENTRY ===")
        logging.info(f"SIGNAL_PROCESSING_INPUT_TYPE: {type(strategy_signals)}")
        logging.info(f"SIGNAL_PROCESSING_INPUT: {strategy_signals}")

        try:
            original_signals = strategy_signals
            strategy_signals = _map_signals_to_typed(strategy_signals)
            # Convert StrategyType keys to strings for DTO compatibility
            processed_signals = {k.value: v for k, v in strategy_signals.items()}

            logging.info(f"SIGNAL_PROCESSING_OUTPUT_TYPE: {type(processed_signals)}")
            logging.info(f"SIGNAL_PROCESSING_OUTPUT: {processed_signals}")
            logging.info(
                f"SIGNAL_PROCESSING_SUCCESS: Mapped {len(original_signals) if original_signals else 0} → {len(processed_signals)} signals"
            )

            return processed_signals
        except Exception as e:  # pragma: no cover - defensive
            logging.error(f"❌ SIGNAL_PROCESSING_FAILED: {e}")
            logging.warning(f"Failed to map strategy signals to typed: {e}")
            logging.info("SIGNAL_PROCESSING_FALLBACK: Returning original signals")
            return strategy_signals

    def _validate_portfolio_allocation(
        self, consolidated_portfolio: dict[str, float]
    ) -> dict[str, float]:
        """Validate and normalize portfolio allocation."""
        # === UNIVERSAL DATA TRACKING IN VALIDATION ===
        logging.info("=== _VALIDATE_PORTFOLIO_ALLOCATION ENTRY ===")
        input_total = sum(consolidated_portfolio.values()) if consolidated_portfolio else 0
        input_count = len(consolidated_portfolio) if consolidated_portfolio else 0
        logging.info(f"VALIDATION_INPUT: {input_count} symbols, total={input_total:.6f}")

        if not consolidated_portfolio:
            logging.error("❌ CRITICAL: VALIDATION RECEIVED EMPTY PORTFOLIO!")
            logging.error("❌ UNIVERSAL FAILURE: No portfolio data reached validation stage")
            consolidated_portfolio = {"BIL": 1.0}
            logging.info("No portfolio signals generated, defaulting to cash (BIL)")
        else:
            # Log input data for tracking
            input_meaningful = {s: a for s, a in consolidated_portfolio.items() if a > 0.001}
            logging.info(f"VALIDATION_INPUT_MEANINGFUL: {len(input_meaningful)} symbols > 0.1%")
            for symbol, allocation in input_meaningful.items():
                logging.info(f"  VALIDATION_INPUT: {symbol} = {allocation:.6f}")

        total_allocation = sum(consolidated_portfolio.values())
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")

        # === UNIVERSAL DATA TRACKING AT VALIDATION EXIT ===
        output_total = sum(consolidated_portfolio.values())
        output_count = len(consolidated_portfolio)
        output_meaningful = {s: a for s, a in consolidated_portfolio.items() if a > 0.001}

        logging.info(f"VALIDATION_OUTPUT: {output_count} symbols, total={output_total:.6f}")
        logging.info(f"VALIDATION_OUTPUT_MEANINGFUL: {len(output_meaningful)} symbols > 0.1%")

        if len(output_meaningful) == 0:
            logging.error("❌ CRITICAL: VALIDATION OUTPUT HAS NO MEANINGFUL ALLOCATIONS!")
            logging.error("❌ VALIDATION BUG: Method eliminated ALL trading opportunities")

        return consolidated_portfolio

    def _validate_and_filter_orders(self, orders_executed: list[Any]) -> list[Any]:
        """Validate orders and filter out those with None IDs."""
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

        return valid_orders

    def _create_error_account_info(self) -> AccountInfo:
        """Create empty AccountInfo for error cases."""
        return {
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

    def _handle_data_provider_error(self, e: DataProviderError) -> MultiStrategyExecutionResultDTO:
        """Handle DataProviderError by returning a safe result."""
        from the_alchemiser.shared.logging.logging_utils import (
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

        empty_account_info = self._create_error_account_info()
        return MultiStrategyExecutionResultDTO(
            success=False,
            strategy_signals={},
            consolidated_portfolio={"BIL": 1.0},  # Safe fallback to cash
            orders_executed=[],
            account_info_before=empty_account_info,
            account_info_after=empty_account_info,
            execution_summary=dict_to_execution_summary_dto(
                {
                    "error": str(e),
                    "mode": "error",
                    "account_info_before": empty_account_info,
                    "account_info_after": empty_account_info,
                }
            ),
            final_portfolio_state=None,
        )

    def _handle_configuration_strategy_error(self, e: Exception) -> None:
        """Handle configuration and strategy errors by logging and re-raising as TradingClientError."""
        from the_alchemiser.shared.logging.logging_utils import (
            get_logger,
            log_error_with_context,
        )

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "multi_strategy_execution",
            engine_type=type(self.engine).__name__,
            error_type=type(e).__name__,
        )
        raise TradingClientError(
            f"Configuration/strategy error in multi-strategy execution: {e!s}",
            context={
                "original_error": type(e).__name__,
                "operation": "multi_strategy_execution",
            },
        ) from e

    @handle_errors_with_retry(operation="multi_strategy_execution", critical=True, max_retries=1)
    def execute_multi_strategy(
        self,
        pre_calculated_signals: Any = None,
        pre_calculated_portfolio: dict[str, float] | None = None,
        pre_calculated_attribution: Any = None,
    ) -> Any:
        """Run all strategies and rebalance portfolio.

        Args:
            pre_calculated_signals: Pre-calculated strategy signals to avoid double calculation
            pre_calculated_portfolio: Pre-calculated consolidated portfolio
            pre_calculated_attribution: Pre-calculated strategy attribution

        """
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

            # === ENHANCED LOGGING: EXECUTION MANAGER START ===
            logging.info("=== MULTI-STRATEGY EXECUTOR START ===")
            logging.info(f"ENGINE TYPE: {type(self.engine).__name__}")
            logging.info(f"ACCOUNT EQUITY BEFORE: ${account_info_before.get('equity', 0):,.2f}")
            logging.info(f"BUYING POWER BEFORE: ${account_info_before.get('buying_power', 0):,.2f}")

            # === UNIVERSAL DATA FLOW TRACKING ===
            logging.info("=== UNIVERSAL DATA FLOW TRACKING START ===")
            logging.info("TRACKING: All portfolio data through execution pipeline")
            logging.info("PURPOSE: Identify where ALL position data is lost in the system")

            # Enhanced input validation logging
            logging.info("=== INPUT DATA VALIDATION ===")
            logging.info(f"Received pre_calculated_signals: {pre_calculated_signals is not None}")
            logging.info(
                f"Received pre_calculated_portfolio: {pre_calculated_portfolio is not None}"
            )
            logging.info(
                f"Received pre_calculated_attribution: {pre_calculated_attribution is not None}"
            )

            if pre_calculated_signals is not None:
                logging.info(f"PRE_CALC_SIGNALS type: {type(pre_calculated_signals)}")
                logging.info(
                    f"PRE_CALC_SIGNALS keys: {getattr(pre_calculated_signals, 'keys', lambda: 'N/A')()}"
                )

            if pre_calculated_portfolio is not None:
                logging.info(f"PRE_CALC_PORTFOLIO type: {type(pre_calculated_portfolio)}")
                logging.info(f"PRE_CALC_PORTFOLIO content: {pre_calculated_portfolio}")
                total_pre = (
                    sum(pre_calculated_portfolio.values()) if pre_calculated_portfolio else 0
                )
                logging.info(f"PRE_CALC_PORTFOLIO total allocation: {total_pre:.3f}")

                # === UNIVERSAL DATA INTEGRITY CHECK ===
                logging.info("=== PRE-CALCULATED PORTFOLIO UNIVERSAL INTEGRITY CHECK ===")
                if total_pre == 0:
                    logging.error("❌ CRITICAL: PRE_CALC_PORTFOLIO HAS ZERO TOTAL ALLOCATION!")
                    logging.error(
                        "❌ UNIVERSAL FAILURE: No allocations for ANY symbols in pre-calculated data"
                    )
                elif abs(total_pre - 1.0) > 0.05:
                    logging.warning(
                        f"⚠️ PRE_CALC_PORTFOLIO allocation integrity issue: {total_pre:.3f}"
                    )
                else:
                    logging.info(f"✅ PRE_CALC_PORTFOLIO integrity check passed: {total_pre:.3f}")

            # Use pre-calculated signals if provided to avoid double calculation
            if (
                pre_calculated_signals is not None
                and pre_calculated_portfolio is not None
                and pre_calculated_attribution is not None
            ):
                strategy_signals = pre_calculated_signals
                consolidated_portfolio = pre_calculated_portfolio
                strategy_attribution = pre_calculated_attribution
                logging.info("✅ USING PRE-CALCULATED DATA from rebalancer")
                logging.info(f"Pre-calculated portfolio has {len(consolidated_portfolio)} symbols")

                # Enhanced pre-calculated data logging
                logging.info("=== PRE-CALCULATED DATA DETAILS ===")
                for symbol, allocation in consolidated_portfolio.items():
                    logging.info(
                        f"  PRE_CALC: {symbol} = {allocation:.4f} ({allocation * 100:.2f}%)"
                    )

                # === UNIVERSAL PRE-CALC VALIDATION ===
                pre_calc_meaningful = {s: a for s, a in consolidated_portfolio.items() if a > 0.001}
                logging.info(
                    f"PRE_CALC_MEANINGFUL_SYMBOLS: {len(pre_calc_meaningful)} symbols have >0.1% allocation"
                )
                if len(pre_calc_meaningful) == 0:
                    logging.error(
                        "❌ CRITICAL: PRE_CALC has no meaningful allocations for ANY symbols!"
                    )
                else:
                    logging.info(
                        f"✅ PRE_CALC has meaningful allocations for {len(pre_calc_meaningful)} symbols"
                    )
            else:
                logging.warning("⚠️ RECALCULATING portfolio balance (potential bug source)")
                strategy_signals, consolidated_portfolio, strategy_attribution = (
                    self.engine.strategy_manager.run_all_strategies()
                )
                logging.info("Calculating fresh strategy signals")
                logging.info(
                    f"Fresh calculated portfolio has {len(consolidated_portfolio)} symbols"
                )

                # Enhanced fresh calculation logging
                logging.info("=== FRESH CALCULATION DATA DETAILS ===")
                for symbol, allocation in consolidated_portfolio.items():
                    logging.info(
                        f"  FRESH_CALC: {symbol} = {allocation:.4f} ({allocation * 100:.2f}%)"
                    )

                # === UNIVERSAL FRESH CALC VALIDATION ===
                fresh_calc_meaningful = {
                    s: a for s, a in consolidated_portfolio.items() if a > 0.001
                }
                logging.info(
                    f"FRESH_CALC_MEANINGFUL_SYMBOLS: {len(fresh_calc_meaningful)} symbols have >0.1% allocation"
                )
                if len(fresh_calc_meaningful) == 0:
                    logging.error(
                        "❌ CRITICAL: FRESH_CALC has no meaningful allocations for ANY symbols!"
                    )
                    logging.error(
                        "❌ SYSTEMIC ISSUE: Strategy calculation resulted in zero meaningful allocations"
                    )
                else:
                    logging.info(
                        f"✅ FRESH_CALC has meaningful allocations for {len(fresh_calc_meaningful)} symbols"
                    )

            strategy_signals = self._process_strategy_signals(strategy_signals)
            consolidated_portfolio = self._validate_portfolio_allocation(consolidated_portfolio)

            # === UNIVERSAL POST-PROCESSING DATA INTEGRITY CHECK ===
            logging.info("=== UNIVERSAL POST-PROCESSING DATA INTEGRITY CHECK ===")
            post_process_total = (
                sum(consolidated_portfolio.values()) if consolidated_portfolio else 0
            )
            post_process_meaningful = (
                {s: a for s, a in consolidated_portfolio.items() if a > 0.001}
                if consolidated_portfolio
                else {}
            )

            logging.info(f"POST_PROCESSING_TOTAL_ALLOCATION: {post_process_total:.6f}")
            logging.info(f"POST_PROCESSING_MEANINGFUL_COUNT: {len(post_process_meaningful)}")

            if post_process_total == 0:
                logging.error("❌ CRITICAL: POST_PROCESSING RESULTED IN ZERO TOTAL ALLOCATION!")
                logging.error(
                    "❌ UNIVERSAL FAILURE: _validate_portfolio_allocation() zeroed out ALL data"
                )
            elif len(post_process_meaningful) == 0:
                logging.error("❌ CRITICAL: POST_PROCESSING REMOVED ALL MEANINGFUL ALLOCATIONS!")
                logging.error(
                    "❌ SYSTEMIC BUG: Processing pipeline eliminated ALL trading opportunities"
                )
            else:
                logging.info(
                    f"✅ POST_PROCESSING: {len(post_process_meaningful)} symbols retain meaningful allocations"
                )

            # Enhanced portfolio state logging before rebalancing
            logging.info("=== PORTFOLIO ANALYSIS STAGE ===")
            logging.info(f"FINAL portfolio to rebalance: {consolidated_portfolio}")
            total_allocation = sum(consolidated_portfolio.values())
            logging.info(
                f"FINAL total allocation: {total_allocation:.3f} ({total_allocation * 100:.1f}%)"
            )

            # Log detailed target vs current allocations
            current_positions = (
                self.engine.get_positions_dict()
                if hasattr(self.engine, "get_positions_dict")
                else {}
            )
            current_portfolio_value = float(account_info_before.get("equity", 0))

            logging.info("=== TARGET VS CURRENT ALLOCATION ANALYSIS ===")
            logging.info(f"Current portfolio value: ${current_portfolio_value:,.2f}")
            logging.info(f"Current positions: {dict(current_positions)}")

            trade_calculations = {}
            for symbol, target_allocation in consolidated_portfolio.items():
                target_value = target_allocation * current_portfolio_value
                current_value = float(current_positions.get(symbol, 0))
                trade_amount = target_value - current_value
                trade_calculations[symbol] = {
                    "target_allocation": target_allocation,
                    "target_value": target_value,
                    "current_value": current_value,
                    "trade_amount": trade_amount,
                }
                if abs(trade_amount) > 1.0:  # Only log significant trades
                    action = "BUY" if trade_amount > 0 else "SELL"
                    logging.info(
                        f"  {symbol}: {action} ${abs(trade_amount):,.2f} (target: ${target_value:,.2f}, current: ${current_value:,.2f})"
                    )

            # Log which symbols have allocations
            significant_allocations = {}
            for symbol, allocation in consolidated_portfolio.items():
                if allocation > 0.001:  # Log allocations > 0.1%
                    significant_allocations[symbol] = allocation
                    logging.info(
                        f"Target allocation {symbol}: {allocation:.3f} ({allocation * 100:.1f}%)"
                    )

            logging.info(f"SIGNIFICANT ALLOCATIONS COUNT: {len(significant_allocations)}")
            logging.info(f"TRADE CALCULATIONS READY: {len(trade_calculations)} symbols analyzed")

            # === DATA TRANSFER POINT: ENGINE.REBALANCE_PORTFOLIO ===
            logging.info("=== DATA TRANSFER POINT: PASSING TO ENGINE.REBALANCE_PORTFOLIO ===")

            # === ENHANCED DATA INTEGRITY VERIFICATION ===
            logging.info(
                "=== CRITICAL DATA INTEGRITY VERIFICATION BEFORE ENGINE.REBALANCE_PORTFOLIO ==="
            )

            # Data type validation
            logging.info(f"CONSOLIDATED_PORTFOLIO_TYPE: {type(consolidated_portfolio)}")
            logging.info(
                f"CONSOLIDATED_PORTFOLIO_IS_DICT: {isinstance(consolidated_portfolio, dict)}"
            )
            logging.info(
                f"CONSOLIDATED_PORTFOLIO_COUNT: {len(consolidated_portfolio) if consolidated_portfolio else 0}"
            )

            if consolidated_portfolio:
                # Verify data integrity
                total_allocation_check = sum(consolidated_portfolio.values())
                logging.info(f"TOTAL_ALLOCATION_VERIFICATION: {total_allocation_check:.6f}")
                logging.info(
                    f"ALLOCATION_SUM_IS_NEAR_ONE: {abs(total_allocation_check - 1.0) < 0.01}"
                )

                # Log each allocation with data type information
                logging.info("=== DETAILED ALLOCATION BREAKDOWN WITH TYPE VERIFICATION ===")
                for symbol, allocation in consolidated_portfolio.items():
                    logging.info(
                        f"ALLOCATION_DETAIL: {symbol} = {allocation} (type: {type(allocation)}, is_numeric: {isinstance(allocation, int | float)})"
                    )

                    # Validate allocation value range
                    if allocation < 0 or allocation > 1:
                        logging.error(
                            f"❌ INVALID_ALLOCATION_RANGE: {symbol} = {allocation} (outside 0-1 range)"
                        )
                    elif allocation > 0.001:  # Log significant allocations
                        logging.info(
                            f"✅ SIGNIFICANT_ALLOCATION: {symbol} = {allocation:.4f} ({allocation * 100:.2f}%)"
                        )

                # Verify no NaN or infinite values
                for symbol, allocation in consolidated_portfolio.items():
                    if not isinstance(allocation, int | float) or str(allocation).lower() in [
                        "nan",
                        "inf",
                        "-inf",
                    ]:
                        logging.error(
                            f"❌ INVALID_ALLOCATION_VALUE: {symbol} = {allocation} (not a valid number)"
                        )

                # Create data checksum for tracking
                data_values = list(consolidated_portfolio.values())
                data_checksum = f"symbols:{len(consolidated_portfolio)}_total:{sum(data_values):.6f}_hash:{hash(frozenset(consolidated_portfolio.items()))}"
                logging.info(f"DATA_CHECKSUM_BEFORE_ENGINE: {data_checksum}")

                # Check if any allocations might cause issues downstream
                zero_allocations = [s for s, a in consolidated_portfolio.items() if a == 0]
                positive_allocations = [s for s, a in consolidated_portfolio.items() if a > 0]
                logging.info(
                    f"ZERO_ALLOCATIONS: {zero_allocations} (count: {len(zero_allocations)})"
                )
                logging.info(
                    f"POSITIVE_ALLOCATIONS: {positive_allocations} (count: {len(positive_allocations)})"
                )

                # Verify we have meaningful trades to execute - UNIVERSAL CHECK
                if len(positive_allocations) == 0:
                    logging.error(
                        "❌ CRITICAL: NO POSITIVE ALLOCATIONS - This will result in no BUY orders!"
                    )
                    logging.error(
                        "❌ UNIVERSAL TRADE FAILURE: No symbols have positive allocations to trade"
                    )
                else:
                    logging.info(
                        f"✅ DATA_VALIDATION_PASSED: {len(positive_allocations)} symbols with positive allocations"
                    )
            else:
                logging.error(
                    "❌ CRITICAL: CONSOLIDATED_PORTFOLIO IS EMPTY - No data to pass to engine!"
                )
                logging.error("❌ This explains why no trades are generated!")

            # Use utility function for standardized logging
            log_data_transfer_checkpoint(
                logging.getLogger(__name__),
                stage="ExecutionManager→TradingEngine",
                data=consolidated_portfolio,
                context="Passing consolidated portfolio to engine.rebalance_portfolio()",
                attribution_provided=strategy_attribution is not None,
                engine_type=type(self.engine).__name__,
            )

            # Enhanced pre-call validation
            logging.info("=== FINAL PRE-CALL VALIDATION ===")
            logging.info(f"ENGINE_TYPE: {type(self.engine).__name__}")
            logging.info(
                f"ENGINE_HAS_REBALANCE_PORTFOLIO: {hasattr(self.engine, 'rebalance_portfolio')}"
            )
            logging.info(f"STRATEGY_ATTRIBUTION_PROVIDED: {strategy_attribution is not None}")

            if strategy_attribution:
                logging.info(f"STRATEGY_ATTRIBUTION_TYPE: {type(strategy_attribution)}")
                logging.info(
                    f"STRATEGY_ATTRIBUTION_COUNT: {len(strategy_attribution) if strategy_attribution else 0}"
                )

            # Call the engine rebalance method
            logging.info("🚀 CALLING ENGINE.REBALANCE_PORTFOLIO() NOW...")
            orders_executed = self.engine.rebalance_portfolio(
                consolidated_portfolio, strategy_attribution
            )
            logging.info("📥 ENGINE.REBALANCE_PORTFOLIO() RETURNED")

            # Enhanced rebalancing results logging
            logging.info("=== EXECUTION PIPELINE RESULTS ===")
            logging.info(f"ORDERS_RETURNED_TYPE: {type(orders_executed)}")
            logging.info(f"ORDERS_RETURNED_COUNT: {len(orders_executed) if orders_executed else 0}")

            if orders_executed:
                logging.info("✅ ORDERS RECEIVED FROM REBALANCING:")
                for i, order in enumerate(orders_executed):
                    logging.info(f"  Order {i + 1}: {order}")
                    if (
                        hasattr(order, "symbol")
                        and hasattr(order, "qty")
                        and hasattr(order, "side")
                    ):
                        logging.info(f"    Details: {order.side} {order.qty} {order.symbol}")
            else:
                logging.error("❌ NO ORDERS RETURNED from rebalance_portfolio")
                logging.error(
                    "*** UNIVERSAL TRADE FAILURE: Expected ANY trades but got empty result ***"
                )
                logging.error(
                    f"Expected trades for ANY symbols with positive allocations: {list(significant_allocations.keys())}"
                )
                logging.error(
                    f"Trade calculations showed {len([t for t in trade_calculations.values() if abs(t['trade_amount']) > 1.0])} significant trades needed across ALL symbols"
                )

            # Use utility function for expectation vs reality comparison
            log_trade_expectation_vs_reality(
                logging.getLogger(__name__),
                expected_trades=[
                    {
                        "symbol": symbol,
                        "action": "BUY" if calc["trade_amount"] > 0 else "SELL",
                        "amount": abs(calc["trade_amount"]),
                    }
                    for symbol, calc in trade_calculations.items()
                    if abs(calc["trade_amount"]) > 1.0
                ],
                actual_orders=orders_executed,
                stage="ExecutionManager-PostRebalance",
            )
            logging.info("=== REBALANCING RESULTS ANALYSIS COMPLETE ===")

            orders_executed = self._validate_and_filter_orders(orders_executed)

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
                execution_summary=dict_to_execution_summary_dto(execution_summary),
                final_portfolio_state=dict_to_portfolio_state_dto(final_portfolio_state),
            )

            save_dashboard_data(self.engine, result)
            self.engine._archive_daily_strategy_pnl(execution_summary.get("pnl_summary", {}))
            return result

        except TradingClientError as e:
            from the_alchemiser.shared.logging.logging_utils import (
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
            return self._handle_data_provider_error(e)

        except (
            ConfigurationError,
            StrategyExecutionError,
            ValueError,
            AttributeError,
        ) as e:
            self._handle_configuration_strategy_error(e)
