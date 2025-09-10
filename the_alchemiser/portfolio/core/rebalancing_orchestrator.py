"""Business Unit: portfolio assessment & management; Status: current.

Rebalancing Orchestrator for sequential SELL→settle→BUY execution.

This module provides orchestration for portfolio rebalancing with proper settlement
timing to avoid buying power issues. It delegates to PortfolioManagementFacade for
the actual execution phases and uses WebSocket-based monitoring for order completion.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from the_alchemiser.execution.core.execution_schemas import (
    WebSocketResultDTO,
)
from the_alchemiser.execution.monitoring.websocket_order_monitor import (
    OrderCompletionMonitor,
)
from the_alchemiser.shared.config.secrets_manager import SecretsManager
from the_alchemiser.shared.dto.broker_dto import WebSocketStatus
from the_alchemiser.shared.value_objects.core_types import OrderDetails
from the_alchemiser.strategy.registry.strategy_registry import StrategyType

if TYPE_CHECKING:
    from .portfolio_management_facade import (
        PortfolioManagementFacade,
    )


class RebalancingOrchestrator:
    """Orchestrates sequential portfolio rebalancing with proper settlement timing.

    Handles the SELL→settle→BUY sequence to prevent buying power issues by:
    1. Executing SELL orders first to free up capital
    2. Waiting for order settlement via WebSocket monitoring
    3. Executing BUY orders with refreshed buying power

    Delegates to PortfolioManagementFacade for phase-specific execution while
    handling the orchestration and settlement timing concerns.
    """

    def __init__(
        self,
        portfolio_facade: PortfolioManagementFacade,
        trading_client: Any,  # noqa: ANN401  # TradingClient from alpaca - external SDK object
        paper_trading: bool = True,
        account_info_provider: (Any | None) = None,  # noqa: ANN401  # External provider with get_account_info method
    ) -> None:
        """Initialize orchestrator with required dependencies.

        Args:
            portfolio_facade: Facade for portfolio management operations
            trading_client: Alpaca trading client for WebSocket monitoring
            paper_trading: Whether using paper trading (affects API credentials)
            account_info_provider: Provider for account information (e.g., TradingEngine)

        """
        self.portfolio_facade = portfolio_facade
        self.trading_client = trading_client
        self.paper_trading = paper_trading
        self.account_info_provider = account_info_provider

    def execute_sell_phase(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute SELL orders to free buying power.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages
            strategy_attribution: Dictionary mapping symbols to contributing strategies

        Returns:
            List of executed SELL orders as OrderDetails

        """
        logging.info("🔄 Phase 1: Executing SELL orders to free buying power")
        
        # === ENHANCED SELL PHASE DEBUGGING ===
        logging.info("=== SELL PHASE: TARGET PORTFOLIO RECEIVED ===")
        logging.info(f"SELL_PHASE_TARGET_TYPE: {type(target_portfolio)}")
        logging.info(f"SELL_PHASE_TARGET_COUNT: {len(target_portfolio) if target_portfolio else 0}")
        
        if target_portfolio:
            total_allocation = sum(target_portfolio.values())
            logging.info(f"SELL_PHASE_TOTAL_ALLOCATION: {total_allocation}")
            for symbol, allocation in target_portfolio.items():
                logging.info(f"SELL_PHASE_TARGET: {symbol} = {allocation} ({allocation * 100:.1f}%)")
        else:
            logging.error("❌ SELL_PHASE_RECEIVED_EMPTY_TARGET_PORTFOLIO")

        # Delegate to facade for SELL phase execution
        sell_orders = self.portfolio_facade.rebalance_portfolio_phase(
            target_portfolio, phase="sell"
        )

        if sell_orders:
            logging.info(f"Executed {len(sell_orders)} SELL orders")
            for order in sell_orders:
                logging.info(f"SELL {order['symbol']}: {order['qty']} shares")
        else:
            logging.info("No SELL orders needed")

        return sell_orders

    async def wait_for_settlement_and_bp_refresh(self, sell_orders: list[OrderDetails]) -> None:
        """Wait for sell order settlement and buying power refresh via WebSocket monitoring.

        Args:
            sell_orders: List of SELL orders to monitor for completion

        """
        if not sell_orders:
            logging.info("No SELL orders to monitor for settlement")
            return

        logging.info("⏳ Phase 2: Waiting for sell order settlements and buying power refresh...")

        # Extract valid order IDs for monitoring
        sell_order_ids = [order["id"] for order in sell_orders if order["id"] != "unknown"]

        if not sell_order_ids:
            logging.warning("No valid order IDs to monitor, using async fallback delay")
            await asyncio.sleep(5)  # Non-blocking fallback delay
            return

        try:
            # Get API credentials for WebSocket monitoring
            secrets_manager = SecretsManager()
            api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=self.paper_trading)

            # Initialize WebSocket monitor
            monitor = OrderCompletionMonitor(self.trading_client, api_key, secret_key)

            # Run WebSocket monitoring in executor to avoid blocking
            completion_result: WebSocketResultDTO = await asyncio.get_event_loop().run_in_executor(
                None, monitor.wait_for_order_completion, sell_order_ids, 30
            )

            # Handle completion results using enum comparisons (fix for previous string comparison bug)
            if completion_result.status == WebSocketStatus.COMPLETED:
                completed_order_ids = completion_result.orders_completed
                logging.info(
                    f"✅ {len(completed_order_ids)} sell orders completed, buying power should be refreshed"
                )
            elif completion_result.status == WebSocketStatus.TIMEOUT:
                completed_order_ids = completion_result.orders_completed
                logging.warning(
                    f"⏰ WebSocket monitoring timed out. {len(completed_order_ids)} orders completed out of {len(sell_order_ids)}"
                )
            else:  # WebSocketStatus.ERROR
                completed_order_ids = completion_result.orders_completed
                logging.error(
                    f"❌ WebSocket monitoring error: {completion_result.message} (completed={len(completed_order_ids)})"
                )

            # Brief additional non-blocking delay to ensure buying power propagation
            await asyncio.sleep(2)

        except Exception as e:
            logging.warning(f"WebSocket monitoring failed, using async fallback delay: {e}")
            # Use exponential backoff with timeout
            backoff = 2
            max_backoff_time = 15
            await asyncio.sleep(min(backoff * 2, max_backoff_time))

    def execute_buy_phase(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute BUY orders with refreshed buying power.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages
            strategy_attribution: Dictionary mapping symbols to contributing strategies

        Returns:
            List of executed BUY orders as OrderDetails

        """
        logging.info("🔄 Phase 3: Executing BUY orders with refreshed buying power")
        
        # === ENHANCED BUY PHASE DEBUGGING ===
        logging.info("=== BUY PHASE: TARGET PORTFOLIO RECEIVED ===")
        logging.info(f"BUY_PHASE_TARGET_TYPE: {type(target_portfolio)}")
        logging.info(f"BUY_PHASE_TARGET_COUNT: {len(target_portfolio) if target_portfolio else 0}")
        
        if target_portfolio:
            total_allocation = sum(target_portfolio.values())
            logging.info(f"BUY_PHASE_TOTAL_ALLOCATION: {total_allocation}")
            for symbol, allocation in target_portfolio.items():
                if allocation > 0.001:  # Log significant allocations
                    logging.info(f"BUY_PHASE_TARGET: {symbol} = {allocation} ({allocation * 100:.1f}%)")
        else:
            logging.error("❌ BUY_PHASE_RECEIVED_EMPTY_TARGET_PORTFOLIO")

        # Get fresh account info to update buying power if provider is available
        if self.account_info_provider and hasattr(self.account_info_provider, "get_account_info"):
            account_info = self.account_info_provider.get_account_info()
            current_buying_power = float(account_info["buying_power"])
            logging.info(f"Current buying power: ${current_buying_power:,.2f}")

        # Delegate to facade for BUY phase execution with scaled sizing
        buy_orders = self.portfolio_facade.rebalance_portfolio_phase(target_portfolio, phase="buy")

        if buy_orders:
            logging.info(f"Executed {len(buy_orders)} BUY orders")
            for order in buy_orders:
                logging.info(f"BUY {order['symbol']}: {order['qty']} shares")
        else:
            logging.info("No BUY orders needed")

        return buy_orders

    async def execute_full_rebalance_cycle(
        self,
        target_portfolio: dict[str, float],
        strategy_attribution: dict[str, list[StrategyType]] | None = None,
    ) -> list[OrderDetails]:
        """Execute complete sequential rebalancing: SELL→settle→BUY.

        Args:
            target_portfolio: Dictionary mapping symbols to target weight percentages
            strategy_attribution: Dictionary mapping symbols to contributing strategies

        Returns:
            List of all executed orders (SELLs and BUYs) as OrderDetails

        """
        # === ENHANCED LOGGING: ORCHESTRATOR ENTRY ===
        logging.info("=== REBALANCING ORCHESTRATOR: EXECUTE_FULL_REBALANCE_CYCLE ===")
        logging.info(f"ORCHESTRATOR_TYPE: {type(self).__name__}")
        logging.info(f"RECEIVED_TARGET_PORTFOLIO: {target_portfolio}")
        logging.info(f"RECEIVED_ATTRIBUTION: {strategy_attribution is not None}")

        if not target_portfolio:
            logging.error("❌ ORCHESTRATOR: Empty target portfolio provided to rebalance_portfolio")
            return []

        # Validate portfolio allocations
        total_allocation = sum(target_portfolio.values())
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(
                f"⚠️ ORCHESTRATOR: Portfolio allocation sums to {total_allocation:.1%}, expected ~100%"
            )

        # Enhanced rebalancing initiation logging
        logging.info("🚀 ORCHESTRATOR: Initiating sequential portfolio rebalancing")
        logging.info(f"ORCHESTRATOR: Processing {len(target_portfolio)} symbols")
        logging.debug(f"ORCHESTRATOR: Target allocations detail: {target_portfolio}")

        # Log each target allocation with enhanced detail
        significant_allocations = {}
        for symbol, allocation in target_portfolio.items():
            logging.info(
                f"ORCHESTRATOR_TARGET: {symbol} = {allocation:.3f} ({allocation * 100:.1f}%)"
            )
            if allocation > 0.001:  # Track significant allocations
                significant_allocations[symbol] = allocation

        logging.info(
            f"ORCHESTRATOR: {len(significant_allocations)} significant allocations identified"
        )

        try:
            all_orders: list[OrderDetails] = []

            # === DATA TRANSFER CHECKPOINT: BEFORE PHASE 1 ===
            logging.info("=== ORCHESTRATOR CHECKPOINT: BEFORE PHASE 1 (SELL) ===")
            logging.info(
                f"DATA_INTEGRITY_CHECK: {len(target_portfolio)} symbols, total={total_allocation:.4f}"
            )
            logging.info(f"PORTFOLIO_FACADE_TYPE: {type(self.portfolio_facade).__name__}")

            # Phase 1: Execute SELL orders to free buying power
            logging.info("=== REBALANCING PHASE 1: SELL ORDERS ===")
            sell_orders = self.execute_sell_phase(target_portfolio, strategy_attribution)
            all_orders.extend(sell_orders)

            # Enhanced phase 1 results logging
            logging.info(f"PHASE_1_COMPLETE: {len(sell_orders)} SELL orders executed")
            if sell_orders:
                for i, order in enumerate(sell_orders):
                    logging.info(f"  SELL_ORDER_{i + 1}: {order}")
            else:
                logging.info("PHASE_1: No SELL orders needed")

            # === DATA TRANSFER CHECKPOINT: BEFORE PHASE 2 ===
            logging.info("=== ORCHESTRATOR CHECKPOINT: BEFORE PHASE 2 (SETTLEMENT) ===")
            logging.info(f"SELL_ORDERS_FOR_MONITORING: {len(sell_orders)}")

            # Phase 2: Wait for sell order settlements and buying power refresh (now async)
            logging.info("=== REBALANCING PHASE 2: SETTLEMENT WAIT ===")
            await self.wait_for_settlement_and_bp_refresh(sell_orders)
            logging.info("PHASE_2_COMPLETE: Settlement and BP refresh done")

            # === DATA TRANSFER CHECKPOINT: BEFORE PHASE 3 ===
            logging.info("=== ORCHESTRATOR CHECKPOINT: BEFORE PHASE 3 (BUY) ===")
            logging.info(f"DATA_INTEGRITY_RECHECK: {len(target_portfolio)} symbols still available")

            # Phase 3: Execute BUY orders with refreshed buying power
            logging.info("=== REBALANCING PHASE 3: BUY ORDERS ===")
            buy_orders = self.execute_buy_phase(target_portfolio, strategy_attribution)
            all_orders.extend(buy_orders)

            # Enhanced phase 3 results logging
            logging.info(f"PHASE_3_COMPLETE: {len(buy_orders)} BUY orders executed")
            if buy_orders:
                for i, order in enumerate(buy_orders):
                    logging.info(f"  BUY_ORDER_{i + 1}: {order}")
            else:
                logging.info("PHASE_3: No BUY orders needed")

            # === FINAL ORCHESTRATOR SUMMARY ===
            sell_count = len(sell_orders)
            buy_count = len(buy_orders)
            total_orders = len(all_orders)

            logging.info("=== ORCHESTRATOR FINAL SUMMARY ===")
            logging.info("✅ Sequential portfolio rebalancing completed")
            logging.info(
                f"PHASE_BREAKDOWN: {sell_count} SELLs, {buy_count} BUYs, {total_orders} total orders"
            )
            logging.info(f"EXPECTED_SYMBOLS: {list(significant_allocations.keys())}")
            logging.info(f"ORDERS_CREATED_COUNT: {total_orders}")

            # Final validation against expectations
            if len(significant_allocations) > 0 and total_orders == 0:
                logging.error(
                    "🚨 ORCHESTRATOR TRADE LOSS: Expected orders for significant allocations but created 0"
                )
                for symbol, allocation in significant_allocations.items():
                    logging.error(f"🚨 MISSING: {symbol} with {allocation:.1%} allocation")

            # Log final order list in detail
            if all_orders:
                logging.info("FINAL_ORDER_LIST:")
                for i, order in enumerate(all_orders):
                    logging.info(f"  FINAL_ORDER_{i + 1}: {order}")
            else:
                logging.warning("❌ FINAL_ORDER_LIST: EMPTY - no orders created")

            logging.info("=== ORCHESTRATOR EXECUTION COMPLETE ===")
            return all_orders

        except Exception as e:
            logging.error(
                f"❌ ORCHESTRATOR EXCEPTION: Sequential portfolio rebalancing failed: {e}"
            )
            logging.exception("Full orchestrator exception details:")
            return []
