"""Business Unit: execution | Status: current.

Phase executor for executing lists of RebalancePlanItemDTO.

Reusable coroutine for executing a list of RebalancePlanItemDTO via the market execution
component, emitting OrderResultDTO and stats.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.market_execution import MarketExecution
from the_alchemiser.execution_v2.models.execution_result import OrderResultDTO
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItemDTO
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class PhaseExecutor:
    """Phase executor for processing lists of rebalance plan items."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
    ) -> None:
        """Initialize phase executor.

        Args:
            alpaca_manager: Alpaca broker manager
            pricing_service: Optional pricing service for quantity estimation

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.market_execution = MarketExecution(alpaca_manager)

    async def execute_phase_items(
        self, items: list[RebalancePlanItemDTO], phase_type: str
    ) -> tuple[list[OrderResultDTO], dict[str, int | Decimal]]:
        """Execute a list of rebalance plan items.

        Args:
            items: List of plan items to execute
            phase_type: Type of phase ("SELL" or "BUY") for logging

        Returns:
            Tuple of (order_results, execution_stats)

        """
        logger.info(f"🚀 {phase_type} phase: Executing {len(items)} items")

        orders: list[OrderResultDTO] = []
        placed_count = 0
        succeeded_count = 0
        total_trade_value = Decimal("0")

        for item in items:
            try:
                order_result = await self._execute_single_item(item)
                orders.append(order_result)

                if order_result.order_id:  # Order was placed
                    placed_count += 1

                if order_result.success:
                    succeeded_count += 1

                # Accumulate trade value
                if order_result.trade_amount:
                    total_trade_value += abs(order_result.trade_amount)

            except Exception as exc:
                logger.error(f"❌ Error executing {item.symbol}: {exc}")
                # Create a failed order result
                orders.append(
                    OrderResultDTO(
                        symbol=item.symbol,
                        action=item.action,
                        trade_amount=item.trade_amount,
                        shares=Decimal("0"),
                        success=False,
                        error_message=str(exc),
                        timestamp=datetime.now(UTC),
                    )
                )

        stats: dict[str, int | Decimal] = {
            "placed": placed_count,
            "succeeded": succeeded_count,
            "trade_value": total_trade_value,
        }

        logger.info(
            f"📊 {phase_type} phase completed: {succeeded_count}/{placed_count} orders succeeded, "
            f"${total_trade_value} traded"
        )

        return orders, stats

    async def _execute_single_item(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution results

        """
        try:
            side = "buy" if item.action == "BUY" else "sell"

            # Determine quantity (shares) to trade
            if item.action == "SELL" and item.target_weight == Decimal("0.0"):
                # For liquidation (0% target), use actual position quantity
                raw_shares = await asyncio.to_thread(self._get_position_quantity, item.symbol)
                shares = await asyncio.to_thread(
                    self._adjust_quantity_for_fractionability, item.symbol, raw_shares
                )
                logger.info(
                    f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)"
                )
            else:
                # Estimate shares from trade amount using best available price
                price = await asyncio.to_thread(self._get_price_for_estimation, item.symbol)
                if price is None or price <= Decimal("0"):
                    logger.warning(f"⚠️ No valid price for {item.symbol}, skipping order")
                    return OrderResultDTO(
                        symbol=item.symbol,
                        action=item.action,
                        trade_amount=item.trade_amount,
                        shares=Decimal("0"),
                        success=False,
                        error_message=f"No valid price available for {item.symbol}",
                        timestamp=datetime.now(UTC),
                    )

                # Calculate raw shares from trade amount and price
                raw_shares = abs(item.trade_amount) / price
                shares = await asyncio.to_thread(
                    self._adjust_quantity_for_fractionability, item.symbol, raw_shares
                )

                logger.info(
                    f"📊 {item.symbol}: ${abs(item.trade_amount)} ÷ ${price} = {shares} shares"
                )

            if shares <= Decimal("0"):
                logger.warning(f"⚠️ Zero quantity after adjustment for {item.symbol}, skipping")
                return OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=item.trade_amount,
                    shares=Decimal("0"),
                    success=False,
                    error_message="Zero quantity after fractionability adjustment",
                    timestamp=datetime.now(UTC),
                )

            # Execute the market order
            execution_result = await asyncio.to_thread(
                self.market_execution.execute_market_order, item.symbol, side, shares
            )

            # Convert ExecutionResult to OrderResultDTO
            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=shares,
                price=execution_result.price,
                order_id=execution_result.order_id,
                success=execution_result.success,
                error_message=execution_result.error,
                timestamp=datetime.now(UTC),
            )

        except Exception as exc:
            logger.error(f"❌ Failed to execute {item.symbol}: {exc}")
            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=Decimal("0"),
                success=False,
                error_message=str(exc),
                timestamp=datetime.now(UTC),
            )

    def _get_price_for_estimation(self, symbol: str) -> Decimal | None:
        """Get the best available price for quantity estimation."""
        # Try real-time pricing first if available
        if self.pricing_service:
            try:
                quote = self.pricing_service.get_real_time_quote(symbol)
                if quote and hasattr(quote, "mid_price") and quote.mid_price:
                    return Decimal(str(quote.mid_price))
                if quote and hasattr(quote, "bid_price") and quote.bid_price:
                    return Decimal(str(quote.bid_price))
            except Exception as exc:
                logger.debug(f"Real-time pricing failed for {symbol}: {exc}")

        # Fallback to Alpaca's latest quote
        try:
            latest_quote = self.alpaca_manager.get_latest_quote(symbol)
            if latest_quote and hasattr(latest_quote, "bid_price"):
                return Decimal(str(latest_quote.bid_price))
        except Exception as exc:
            logger.debug(f"Latest quote lookup failed for {symbol}: {exc}")

        # Final fallback to position average cost
        try:
            position = self.alpaca_manager.get_position(symbol)
            if position and hasattr(position, "avg_entry_price"):
                return Decimal(str(position.avg_entry_price))
        except Exception as exc:
            logger.debug(f"Position lookup failed for {symbol}: {exc}")

        logger.warning(f"⚠️ No price available for {symbol}")
        return None

    def _adjust_quantity_for_fractionability(self, symbol: str, raw_quantity: Decimal) -> Decimal:
        """Adjust quantity based on asset fractionability (moved from ExecutionValidator)."""
        if raw_quantity <= Decimal("0"):
            return Decimal("0")

        # Use ExecutionValidator for consistency
        validation = self.market_execution.validator.validate_order(
            symbol=symbol,
            quantity=raw_quantity,
            side="buy",
            auto_adjust=True,
        )

        if not validation.is_valid and validation.error_code == "ZERO_QUANTITY_AFTER_ROUNDING":
            return Decimal("0")

        adjusted = (
            validation.adjusted_quantity
            if validation.adjusted_quantity is not None
            else raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)
        )

        if adjusted != raw_quantity:
            logger.info(
                f"🔄 Portfolio sizing: {symbol} non-fractionable, adjusted {raw_quantity:.6f} → {adjusted} shares"
            )

        return max(adjusted, Decimal("0"))

    def _get_position_quantity(self, symbol: str) -> Decimal:
        """Get the actual quantity held for a symbol."""
        try:
            position = self.alpaca_manager.get_position(symbol)
            if position is None:
                logger.debug(f"No position found for {symbol}")
                return Decimal("0")

            # Use qty_available to account for shares tied up in orders
            qty = getattr(position, "qty_available", None) or getattr(position, "qty", 0)
            return Decimal(str(qty))
        except Exception as e:
            logger.warning(f"Error getting position for {symbol}: {e}")
            return Decimal("0")
