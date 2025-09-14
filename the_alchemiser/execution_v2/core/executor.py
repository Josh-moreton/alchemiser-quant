"""Business Unit: execution | Status: current.

Executor that consumes RebalancePlanDTO and places orders.

Core principle: iterate through plan items and place orders - nothing more.
No portfolio calculations, position fetching, or trade recalculation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO

logger = logging.getLogger(__name__)


@dataclass
class TradeValidationResult:
    """Result of pre-trade validation."""
    
    valid: bool
    error_message: str | None = None


class Executor:
    """Executor that processes RebalancePlanDTO items."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager."""
        self.alpaca_manager = alpaca_manager

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan by iterating items and placing orders.

        Args:
            plan: RebalancePlanDTO with items to execute

        Returns:
            ExecutionResultDTO with order results and success status

        """
        logger.info(f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items")

        orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        for item in plan.items:
            # Skip HOLD actions - only process trades
            if item.action == "HOLD":
                logger.debug(f"⏭️ Skipping HOLD action for {item.symbol}")
                continue

            logger.info(f"📦 Processing {item.action} ${item.trade_amount} {item.symbol}")

            # Execute the trade
            order_result = self._execute_trade_item(item)
            orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        # Calculate summary statistics
        orders_placed = len(orders)
        orders_succeeded = sum(1 for order in orders if order.success)
        overall_success = orders_succeeded == orders_placed if orders_placed > 0 else True

        result = ExecutionResultDTO(
            success=overall_success,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
        )

        logger.info(
            f"✅ Execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

    def _execute_trade_item(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
        """Execute a single trade item.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution result

        """
        timestamp = datetime.now(UTC)

        try:
            # Get current price
            price = self.alpaca_manager.get_current_price(item.symbol)
            if price is None:
                return OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=item.trade_amount,
                    shares=Decimal("0"),
                    price=None,
                    order_id=None,
                    success=False,
                    error_message=f"Could not get current price for {item.symbol}",
                    timestamp=timestamp,
                )

            # Calculate shares to trade
            price_decimal = Decimal(str(price))
            shares = abs(item.trade_amount) / price_decimal

            # Pre-trade validation to prevent order failures
            validation_result = self._validate_trade_constraints(item, shares, price_decimal)
            if not validation_result.valid:
                return OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=item.trade_amount,
                    shares=shares,
                    price=price_decimal,
                    order_id=None,
                    success=False,
                    error_message=validation_result.error_message,
                    timestamp=timestamp,
                )

            # Place market order - returns ExecutedOrderDTO
            side = item.action.lower()  # "BUY" -> "buy", "SELL" -> "sell"
            executed_order = self.alpaca_manager.place_market_order(
                symbol=item.symbol, side=side, qty=float(shares)
            )

            # Extract results from ExecutedOrderDTO
            order_id = executed_order.order_id if executed_order.order_id != "FAILED" and executed_order.order_id != "INVALID" else None
            success = executed_order.status not in ["REJECTED", "FAILED"] and order_id is not None
            error_message = executed_order.error_message if not success else None

            if success:
                logger.info(
                    f"✅ Order placed: {item.action} {shares:.4f} shares {item.symbol} → {order_id}"
                )
            else:
                logger.error(f"❌ Order failed: {item.action} {item.symbol} - {error_message}")

            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=shares,
                price=price_decimal,
                order_id=order_id,
                success=success,
                error_message=error_message,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"❌ Unexpected error executing {item.action} {item.symbol}: {e}")
            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=Decimal("0"),
                price=None,
                order_id=None,
                success=False,
                error_message=str(e),
                timestamp=timestamp,
            )
    
    def _validate_trade_constraints(
        self, item: RebalancePlanItemDTO, shares: Decimal, price: Decimal
    ) -> TradeValidationResult:
        """Validate trade constraints before placing order.
        
        Args:
            item: Trade item to validate
            shares: Number of shares to trade
            price: Current price per share
            
        Returns:
            TradeValidationResult indicating if trade is valid

        """
        try:
            if item.action == "BUY":
                return self._validate_buy_constraints(item, shares, price)
            if item.action == "SELL":
                return self._validate_sell_constraints(item, shares)
            return TradeValidationResult(
                valid=False, 
                error_message=f"Unknown action: {item.action}"
            )
        except Exception as e:
            logger.error(f"Error validating trade constraints for {item.symbol}: {e}")
            return TradeValidationResult(
                valid=False,
                error_message=f"Validation error: {e}"
            )
    
    def _validate_buy_constraints(
        self, item: RebalancePlanItemDTO, shares: Decimal, price: Decimal
    ) -> TradeValidationResult:
        """Validate buying power constraints for BUY orders."""
        try:
            # Get current buying power
            buying_power = self.alpaca_manager.get_buying_power()
            if buying_power is None:
                logger.warning(f"Could not get buying power for {item.symbol} BUY validation")
                # Allow trade to proceed - validation is best effort
                return TradeValidationResult(valid=True)
            
            # Calculate required amount (with small buffer for price fluctuations)
            required_amount = float(shares * price) * 1.01  # 1% buffer
            
            if buying_power < required_amount:
                return TradeValidationResult(
                    valid=False,
                    error_message=(
                        f"Insufficient buying power: ${buying_power:.2f} available, "
                        f"${required_amount:.2f} required for {shares:.4f} shares at ${price:.2f}"
                    )
                )
            
            return TradeValidationResult(valid=True)
            
        except Exception as e:
            logger.error(f"Error validating buying power for {item.symbol}: {e}")
            # Allow trade to proceed if validation fails
            return TradeValidationResult(valid=True)
    
    def _validate_sell_constraints(
        self, item: RebalancePlanItemDTO, shares: Decimal
    ) -> TradeValidationResult:
        """Validate available quantity constraints for SELL orders."""
        try:
            # Get current positions
            positions = self.alpaca_manager.get_positions_dict()
            available_shares = positions.get(item.symbol, 0.0)
            
            required_shares = float(shares)
            
            if available_shares < required_shares:
                return TradeValidationResult(
                    valid=False,
                    error_message=(
                        f"Insufficient shares available: {available_shares:.6f} available, "
                        f"{required_shares:.6f} required for {item.symbol}"
                    )
                )
            
            return TradeValidationResult(valid=True)
            
        except Exception as e:
            logger.error(f"Error validating available shares for {item.symbol}: {e}")
            # Allow trade to proceed if validation fails
            return TradeValidationResult(valid=True)
