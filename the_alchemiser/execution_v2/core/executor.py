"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.market_execution import MarketExecution
from the_alchemiser.execution_v2.core.rebalance_workflow import RebalanceWorkflow
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.core.subscription_service import SubscriptionService
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.execution_v2.utils.execution_validator import ExecutionValidator
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.execution_result import ExecutionResult
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
    )

logger = logging.getLogger(__name__)


class Executor:
    """Core executor for order placement - refactored to use modular collaborators."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        *,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize the executor.

        Args:
            alpaca_manager: Alpaca broker manager
            execution_config: Execution configuration
            enable_smart_execution: Whether to enable smart execution

        """
        self.alpaca_manager = alpaca_manager
        self.enable_smart_execution = enable_smart_execution
        self.execution_config = execution_config

        # Initialize core collaborators
        self.market_execution = MarketExecution(alpaca_manager)
        
        # Initialize WebSocket and pricing services for smart execution
        self.pricing_service: RealTimePricingService | None = None
        self.smart_strategy: SmartExecutionStrategy | None = None
        self.websocket_manager = None

        # Initialize smart execution if enabled
        if enable_smart_execution:
            try:
                logger.info("🚀 Initializing smart execution with shared WebSocket connection...")

                # Use shared WebSocket connection manager to prevent connection limits
                self.websocket_manager = WebSocketConnectionManager(
                    api_key=alpaca_manager.api_key,
                    secret_key=alpaca_manager.secret_key,
                    paper_trading=alpaca_manager.is_paper_trading,
                )

                # Get shared pricing service
                self.pricing_service = self.websocket_manager.get_pricing_service()

                # Initialize smart execution strategy
                self.smart_strategy = SmartExecutionStrategy(
                    alpaca_manager=alpaca_manager,
                    pricing_service=self.pricing_service,
                    config=execution_config,
                )

                logger.info("✅ Smart execution initialization complete")
            except Exception as exc:
                logger.warning(f"⚠️ Smart execution initialization failed: {exc}")
                self.enable_smart_execution = False

        # Initialize workflow orchestrator with all dependencies
        self.rebalance_workflow = RebalanceWorkflow(
            alpaca_manager=alpaca_manager,
            pricing_service=self.pricing_service,
            smart_strategy=self.smart_strategy,
            execution_config=execution_config,
        )
        
        # Initialize subscription service
        self.subscription_service = SubscriptionService(
            pricing_service=self.pricing_service,
            enable_subscriptions=enable_smart_execution,
        )

        # Keep backward compatibility attributes
        self.validator = self.market_execution.validator
        self.buying_power_service = self.market_execution.buying_power_service

    def __del__(self) -> None:
        """Clean up WebSocket connection when executor is destroyed."""
        if hasattr(self, "websocket_manager") and self.websocket_manager is not None:
            try:
                self.websocket_manager.release_pricing_service()
            except Exception as e:
                logger.debug(f"Error releasing WebSocket manager: {e}")

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        correlation_id: str | None = None,
    ) -> ExecutionResult:
        """Execute an order with smart execution if enabled.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            correlation_id: Correlation ID for tracking

        Returns:
            ExecutionResult with order details

        """
        # Try smart execution first if enabled
        if self.enable_smart_execution and self.smart_strategy:
            try:
                logger.info(f"🎯 Attempting smart execution for {symbol}")

                request = SmartOrderRequest(
                    symbol=symbol,
                    side=side.upper(),
                    quantity=Decimal(str(quantity)),
                    correlation_id=correlation_id or "",
                    urgency="NORMAL",
                )

                result = await self.smart_strategy.place_smart_order(request)

                if result.success:
                    # Success here means order was placed; fill will be checked later
                    logger.info(f"✅ Smart execution placed order for {symbol}")
                    return ExecutionResult(
                        order_id=result.order_id,
                        symbol=symbol,
                        side=side,
                        quantity=Decimal(str(quantity)),
                        price=(result.final_price if result.final_price else None),
                        status="submitted",
                        success=True,
                        execution_strategy=result.execution_strategy,
                    )
                logger.warning(f"⚠️ Smart execution failed for {symbol}: {result.error_message}")

            except Exception as e:
                logger.error(f"❌ Smart execution failed for {symbol}: {e}")

        # Fallback to regular market order
        logger.info(f"📈 Using standard market order for {symbol}")
        return self.market_execution.execute_market_order(symbol, side, Decimal(str(quantity)))

    async def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute a rebalance plan with settlement-aware sell-first, buy-second workflow.

        Delegates to RebalanceWorkflow for orchestration while maintaining backward compatibility.

        Args:
            plan: RebalancePlanDTO containing the rebalance plan

        Returns:
            ExecutionResultDTO with execution results

        """
        # Extract symbols and setup subscriptions
        all_symbols = self.subscription_service.extract_all_symbols(plan)
        subscription_result = self.subscription_service.bulk_subscribe_symbols(all_symbols)
        
        try:
            # Delegate to workflow orchestrator
            result = await self.rebalance_workflow.execute_rebalance_plan(plan)
            
            return result
        finally:
            # Clean up subscriptions
            self.subscription_service.cleanup_subscriptions(all_symbols)

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")

        if self.websocket_manager:
            try:
                self.websocket_manager.release_pricing_service()
                logger.info("✅ WebSocket manager released")
            except Exception as e:
                logger.debug(f"Error releasing WebSocket manager: {e}")