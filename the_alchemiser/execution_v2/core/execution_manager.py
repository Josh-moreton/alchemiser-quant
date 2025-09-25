"""Business Unit: execution | Status: current.

Execution manager that coordinates Executor with AlpacaManager.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    OrderResult,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.execution.reports import ExecutedOrder
from the_alchemiser.shared.schemas.portfolio.rebalancing import RebalancePlan

logger = logging.getLogger(__name__)


class ExecutionManager:
    """Execution manager that delegates to Executor with smart execution capabilities."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        *,
        enable_smart_execution: bool = True,
        enable_trade_ledger: bool = False,
    ) -> None:
        """Initialize the execution manager.

        Args:
            alpaca_manager: The Alpaca broker manager
            execution_config: Configuration for smart execution strategies
            enable_smart_execution: Whether to enable smart execution features
            enable_trade_ledger: Whether to enable trade ledger recording

        """
        self.alpaca_manager = alpaca_manager
        self.enable_smart_execution = enable_smart_execution
        self.enable_trade_ledger = enable_trade_ledger

        # Initialize trade ledger writer if enabled
        if self.enable_trade_ledger:
            from the_alchemiser.shared.services.trade_ledger_writer import TradeLedgerWriter

            self.trade_ledger_writer: TradeLedgerWriter | None = TradeLedgerWriter()
            logger.info("Trade ledger recording enabled")
        else:
            self.trade_ledger_writer = None

        # Delegate all execution (and smart execution setup) to Executor
        self.executor = Executor(
            alpaca_manager=alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=enable_smart_execution,
        )

    def _record_execution_in_ledger(
        self, result: ExecutionResult, plan: RebalancePlan
    ) -> None:
        """Record execution results in the trade ledger.

        Args:
            result: Execution result with order details
            plan: Original rebalance plan for context

        """
        try:
            if not self.trade_ledger_writer:
                return

            # Convert OrderResult to ExecutedOrder format for trade ledger
            executed_orders = []
            for order in result.orders:
                if order.success and order.shares > 0:
                    # Convert OrderResult to ExecutedOrder
                    executed_order = self._convert_order_result_to_executed_order(order)
                    executed_orders.append(executed_order)

            if executed_orders:
                # Extract strategy name from metadata or use default
                strategy_name = "unknown"
                if result.metadata and "strategy_name" in result.metadata:
                    strategy_name = result.metadata["strategy_name"]

                # Record in trade ledger
                self.trade_ledger_writer.record_executions(
                    executed_orders,
                    strategy_name=strategy_name,
                    correlation_id=result.correlation_id,
                    causation_id=plan.causation_id,
                )

                logger.info(f"Recorded {len(executed_orders)} trades in ledger")

        except Exception as e:
            # Don't fail execution if trade ledger recording fails
            logger.error(f"Failed to record execution in trade ledger: {e}")

    def _convert_order_result_to_executed_order(self, order: OrderResult) -> ExecutedOrder:
        """Convert OrderResult to ExecutedOrder for trade ledger.

        Args:
            order: Order result from execution

        Returns:
            ExecutedOrder for trade ledger recording

        """
        # Calculate filled quantity (assume full fill if successful)
        filled_quantity = order.shares if order.success else Decimal("0")

        # Use price if available, otherwise calculate from trade_amount
        price = order.price
        if not price and order.shares and order.shares > 0:
            price = order.trade_amount / order.shares

        return ExecutedOrder(
            order_id=order.order_id or f"unknown-{order.symbol}-{order.timestamp.isoformat()}",
            symbol=order.symbol,
            action=order.action,
            quantity=order.shares,
            filled_quantity=filled_quantity,
            price=price or Decimal("0.01"),  # Fallback price
            total_value=order.trade_amount,
            status="FILLED" if order.success else "FAILED",
            execution_timestamp=order.timestamp,
            commission=None,  # Not available in OrderResult
            fees=None,  # Not available in OrderResult
            error_message=order.error_message,
        )

    def execute_rebalance_plan(self, plan: RebalancePlan) -> ExecutionResult:
        """Execute rebalance plan using executor.

        Args:
            plan: RebalancePlan to execute

        Returns:
            ExecutionResult with execution results

        """
        logger.info(f"🚀 NEW EXECUTION: {len(plan.items)} items (using execution_v2)")

        # Initialize TradingStream asynchronously in background - don't block on connection
        # This starts the WebSocket connection process early without waiting for completion
        import threading

        def start_trading_stream_async() -> None:
            """Start TradingStream in background without blocking main execution."""
            try:
                logger.info("📡 Starting TradingStream initialization in background...")
                self.alpaca_manager._ensure_trading_stream()
            except Exception as e:
                logger.warning(f"TradingStream background initialization failed: {e}")

        # Start TradingStream initialization in a separate thread so it doesn't block execution
        stream_init_thread = threading.Thread(
            target=start_trading_stream_async, name="TradingStreamInit", daemon=True
        )
        stream_init_thread.start()
        logger.info("✅ TradingStream initialization started in background")

        # Run the async executor in a new event loop
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use async directly
                raise RuntimeError("Cannot run asyncio.run() in an existing event loop")
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            result = asyncio.run(self.executor.execute_rebalance_plan(plan))
        else:
            # Event loop exists but not running, safe to use asyncio.run
            result = asyncio.run(self.executor.execute_rebalance_plan(plan))

        logger.info(f"✅ Execution complete: {result.success} ({result.orders_placed} orders)")

        # Record trades in ledger if enabled
        if self.enable_trade_ledger and self.trade_ledger_writer:
            self._record_execution_in_ledger(result, plan)

        return result

    @classmethod
    def create_with_config(
        cls,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        execution_config: ExecutionConfig | None = None,
        enable_smart_execution: bool = True,
        enable_trade_ledger: bool = False,
    ) -> ExecutionManager:
        """Create ExecutionManager with config and smart execution options.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading
            execution_config: Configuration for smart execution strategies
            enable_smart_execution: Whether to enable smart limit order execution
            enable_trade_ledger: Whether to enable trade ledger recording

        Returns:
            ExecutionManager instance with configured smart execution

        """
        alpaca_manager = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper)
        return cls(
            alpaca_manager=alpaca_manager,
            execution_config=execution_config,
            enable_smart_execution=enable_smart_execution,
            enable_trade_ledger=enable_trade_ledger,
        )
