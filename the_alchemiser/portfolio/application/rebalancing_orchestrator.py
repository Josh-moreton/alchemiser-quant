"""Business Unit: portfolio assessment & management; Status: current.

Rebalancing Orchestrator for sequential SELL→settle→BUY execution.

This module provides orchestration for portfolio rebalancing with proper settlement
timing to avoid buying power issues. It delegates to PortfolioManagementFacade for
the actual execution phases and uses WebSocket-based monitoring for order completion.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared_kernel.domain import StrategyType
from the_alchemiser.shared_kernel.domain.types import OrderDetails
from the_alchemiser.shared_kernel.infrastructure.secrets_manager import SecretsManager
from the_alchemiser.shared_kernel.infrastructure.websocket_order_monitor import (
    OrderCompletionMonitor,
)
from the_alchemiser.shared_kernel.interfaces.execution import (
    WebSocketResultDTO,
    WebSocketStatus,
)

if TYPE_CHECKING:
    from the_alchemiser.portfolio.application.services.portfolio_management_facade import (
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

    def wait_for_settlement_and_bp_refresh(self, sell_orders: list[OrderDetails]) -> None:
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
            logging.warning("No valid order IDs to monitor, using time-based delay")
            time.sleep(5)  # Fallback delay
            return

        try:
            # Get API credentials for WebSocket monitoring
            secrets_manager = SecretsManager()
            api_key, secret_key = secrets_manager.get_alpaca_keys(paper_trading=self.paper_trading)

            # Initialize WebSocket monitor
            monitor = OrderCompletionMonitor(self.trading_client, api_key, secret_key)

            # Wait for all sell orders to complete (30 second timeout)
            completion_result: WebSocketResultDTO = monitor.wait_for_order_completion(
                sell_order_ids, max_wait_seconds=30
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

            # Brief additional delay to ensure buying power propagation
            time.sleep(2)

        except Exception as e:
            logging.warning(f"WebSocket monitoring failed, using fallback delay: {e}")
            time.sleep(10)  # Fallback delay if WebSocket fails

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

    def execute_full_rebalance_cycle(
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
        if not target_portfolio:
            logging.warning("Empty target portfolio provided to rebalance_portfolio")
            return []
        # Validate portfolio allocations
        total_allocation = sum(target_portfolio.values())
        if abs(total_allocation - 1.0) > 0.05:
            logging.warning(f"Portfolio allocation sums to {total_allocation:.1%}, expected ~100%")

        # Log rebalancing initiation
        logging.info(
            f"🚀 Initiating sequential portfolio rebalancing with {len(target_portfolio)} symbols"
        )
        logging.debug(f"Target allocations: {target_portfolio}")

        try:
            all_orders: list[OrderDetails] = []

            # Phase 1: Execute SELL orders to free buying power
            sell_orders = self.execute_sell_phase(target_portfolio, strategy_attribution)
            all_orders.extend(sell_orders)

            # Phase 2: Wait for sell order settlements and buying power refresh
            self.wait_for_settlement_and_bp_refresh(sell_orders)

            # Phase 3: Execute BUY orders with refreshed buying power
            buy_orders = self.execute_buy_phase(target_portfolio, strategy_attribution)
            all_orders.extend(buy_orders)

            # Final summary
            sell_count = len(sell_orders)
            buy_count = len(buy_orders)
            logging.info(
                f"✅ Sequential portfolio rebalancing completed: "
                f"{sell_count} SELLs, {buy_count} BUYs, {len(all_orders)} total orders"
            )

            return all_orders

        except Exception as e:
            logging.error(f"Sequential portfolio rebalancing failed: {e}")
            return []
