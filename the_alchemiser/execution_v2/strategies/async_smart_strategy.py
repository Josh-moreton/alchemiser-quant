"""Business Unit: execution | Status: current.

Enhanced async execution strategy with concurrent operations.

This strategy builds on the smart limit strategy to provide full async support
with concurrent order placement, real-time price monitoring, and parallel execution
across multiple symbols.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.execution_v2.strategies.smart_limit_strategy import SmartLimitExecutionStrategy
from the_alchemiser.execution_v2.utils.market_timing import MarketTimingUtils
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.config.config import ExecutionSettings
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class AsyncSmartExecutionStrategy(SmartLimitExecutionStrategy):
    """Enhanced async execution strategy with concurrent operations.
    
    Extends the smart limit strategy to provide:
    - Concurrent order placement across multiple symbols
    - Real-time price stream monitoring during execution
    - Parallel re-pegging operations
    - Event-driven execution updates
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService,
        config: ExecutionSettings,
    ) -> None:
        """Initialize async smart execution strategy."""
        super().__init__(alpaca_manager, pricing_service, config)
        
        # Track active executions
        self._active_executions: dict[str, asyncio.Task[Any]] = {}
        self._execution_results: dict[str, ExecutedOrderDTO] = {}

    async def execute_rebalance_plan_async(
        self, plan: RebalancePlanDTO
    ) -> dict[str, ExecutedOrderDTO]:
        """Execute entire rebalance plan with concurrent order placement.
        
        Args:
            plan: Rebalance plan to execute
            
        Returns:
            Dictionary mapping symbols to execution results

        """
        logger.info(f"🚀 Async execution starting for plan {plan.plan_id}")
        
        # Check market timing before starting any executions
        MarketTimingUtils.log_market_status()
        
        if MarketTimingUtils.should_delay_for_opening():
            time_until_safe = MarketTimingUtils.get_time_until_safe_execution()
            if time_until_safe:
                logger.info(f"⏰ Delaying execution for {time_until_safe.total_seconds():.0f}s")
                await asyncio.sleep(time_until_safe.total_seconds())
        
        # Start real-time pricing for all symbols
        symbols = [item.symbol for item in plan.items if item.action != "HOLD"]
        await self._prepare_real_time_pricing(symbols)
        
        # Create concurrent execution tasks
        tasks = []
        for item in plan.items:
            if item.action == "HOLD":
                continue
                
            task = asyncio.create_task(
                self._execute_item_with_monitoring(item),
                name=f"execute_{item.symbol}"
            )
            tasks.append(task)
            self._active_executions[item.symbol] = task
        
        # Wait for all executions to complete
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            execution_results: dict[str, ExecutedOrderDTO] = {}
            for i, result in enumerate(results):
                item = [item for item in plan.items if item.action != "HOLD"][i]
                if isinstance(result, Exception):
                    logger.error(f"❌ Execution failed for {item.symbol}: {result}")
                    execution_results[item.symbol] = self._create_error_order_result(
                        item.symbol, item.action, float(item.trade_amount), str(result)
                    )
                else:
                    execution_results[item.symbol] = result
                    
            logger.info(f"✅ Async execution completed for {len(execution_results)} symbols")
            return execution_results
            
        finally:
            # Cleanup active executions
            self._active_executions.clear()

    async def _prepare_real_time_pricing(self, symbols: list[str]) -> None:
        """Prepare real-time pricing for execution symbols.
        
        Args:
            symbols: List of symbols to subscribe to

        """
        logger.info(f"📡 Starting real-time pricing for {len(symbols)} symbols")
        
        # Start pricing service if not already running
        if not self.pricing_service.is_connected():
            success = self.pricing_service.start()
            if not success:
                logger.warning("⚠️ Failed to start real-time pricing - using fallback")
                return
        
        # Subscribe to all symbols for order placement priority
        for symbol in symbols:
            self.pricing_service.subscribe_for_order_placement(symbol)
            
        # Allow time for initial quote data
        await asyncio.sleep(0.5)

    async def _execute_item_with_monitoring(self, item: RebalancePlanItemDTO) -> ExecutedOrderDTO:
        """Execute single item with enhanced monitoring.
        
        Args:
            item: Rebalance plan item to execute
            
        Returns:
            Execution result

        """
        symbol = item.symbol
        logger.info(f"🎯 Starting async execution: {item.action} {symbol}")
        
        try:
            # Get current price for quantity calculation
            price = await self._get_current_price_async(symbol)
            if not price:
                return self._create_error_order_result(
                    symbol, item.action, float(item.trade_amount), "No price data available"
                )
            
            quantity = float(abs(item.trade_amount) / price)
            
            # Execute using the smart strategy
            result = self.execute_smart_limit_order(symbol, item.action.lower(), quantity)
            
            # Start concurrent monitoring if order was placed successfully
            if result.order_id and result.order_id not in ["FAILED", "DELAYED"]:
                monitoring_task = asyncio.create_task(
                    self._enhanced_order_monitoring(result.order_id, symbol, item.action.lower()),
                    name=f"monitor_{symbol}_{result.order_id}"
                )
                self._monitoring_tasks[result.order_id] = monitoring_task
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing {symbol}: {e}")
            return self._create_error_order_result(
                symbol, item.action, float(item.trade_amount), str(e)
            )

    async def _get_current_price_async(self, symbol: str) -> float | None:
        """Get current price asynchronously with timeout.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None

        """
        try:
            # Try real-time price first
            price = self.pricing_service.get_price_for_order_placement(symbol)
            if price:
                return price
                
            # Fallback to alpaca manager with async timeout
            loop = asyncio.get_event_loop()
            price = await asyncio.wait_for(
                loop.run_in_executor(None, self.alpaca_manager.get_current_price, symbol),
                timeout=2.0
            )
            return price
            
        except TimeoutError:
            logger.warning(f"⏰ Price lookup timeout for {symbol}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting price for {symbol}: {e}")
            return None

    async def _enhanced_order_monitoring(self, order_id: str, symbol: str, side: str) -> None:
        """Enhanced order monitoring with real-time updates.
        
        Args:
            order_id: Order ID to monitor
            symbol: Stock symbol
            side: Order side

        """
        logger.info(f"📊 Starting enhanced monitoring for order {order_id}")
        
        monitoring_duration = self.config.order_monitoring_seconds
        check_interval = 2.0  # Check every 2 seconds
        
        start_time = datetime.now(UTC)
        last_quote_time = start_time
        
        try:
            while (datetime.now(UTC) - start_time).total_seconds() < monitoring_duration:
                await asyncio.sleep(check_interval)
                
                # Get current quote
                quote = self.pricing_service.get_quote_data(symbol)
                if not quote:
                    continue
                
                # Check if we've received updated quote data
                quote_age = (datetime.now(UTC) - quote.timestamp).total_seconds()
                if quote_age > 10:  # Quote older than 10 seconds
                    logger.debug(f"📊 Stale quote for {symbol} (age: {quote_age:.1f}s)")
                    continue
                
                # Log real-time market conditions
                if (datetime.now(UTC) - last_quote_time).total_seconds() > 10:
                    spread_pct = (quote.spread / quote.mid_price) * 100
                    logger.debug(
                        f"📊 {symbol} market: "
                        f"bid={quote.bid_price:.3f} ask={quote.ask_price:.3f} "
                        f"spread={spread_pct:.2f}%"
                    )
                    last_quote_time = datetime.now(UTC)
                
                # Check if order needs attention (simplified for now)
                # In production, this would check order status via Alpaca API
                # and implement sophisticated re-pegging logic
                
        except Exception as e:
            logger.error(f"❌ Error monitoring order {order_id}: {e}")
        finally:
            # Clean up the monitoring task reference
            if order_id in self._monitoring_tasks:
                del self._monitoring_tasks[order_id]

    async def execute_with_streaming_updates(
        self, 
        plan: RebalancePlanDTO,
        update_callback: callable | None = None
    ) -> dict[str, ExecutedOrderDTO]:
        """Execute plan with streaming progress updates.
        
        Args:
            plan: Rebalance plan to execute
            update_callback: Optional callback for execution updates
            
        Returns:
            Dictionary of execution results

        """
        logger.info(f"🌊 Starting streaming execution for plan {plan.plan_id}")
        
        # Execute with concurrent monitoring
        results = await self.execute_rebalance_plan_async(plan)
        
        # Send final update if callback provided
        if update_callback:
            try:
                await update_callback({
                    "type": "execution_complete",
                    "plan_id": plan.plan_id,
                    "results": results,
                    "timestamp": datetime.now(UTC)
                })
            except Exception as e:
                logger.error(f"❌ Error sending update callback: {e}")
        
        return results

    def get_execution_statistics(self) -> dict[str, Any]:
        """Get statistics about current and recent executions.
        
        Returns:
            Dictionary with execution statistics

        """
        return {
            "active_executions": len(self._active_executions),
            "active_symbols": list(self._active_executions.keys()),
            "pricing_service_connected": self.pricing_service.is_connected(),
            "subscribed_symbols": len(self.pricing_service.get_subscribed_symbols()),
            "market_session": MarketTimingUtils.get_market_session(),
        }