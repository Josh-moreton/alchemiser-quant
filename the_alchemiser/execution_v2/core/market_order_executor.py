"""Business Unit: execution | Status: current.

Market order execution functionality extracted from the main executor.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    OrderValidationResult,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger, log_order_flow
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService

logger = get_logger(__name__)


class MarketOrderExecutor:
    """Handles market order execution with validation and error handling."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        validator: ExecutionValidator,
        buying_power_service: BuyingPowerService,
    ) -> None:
        """Initialize the market order executor.

        Args:
            alpaca_manager: Alpaca broker manager
            validator: Execution validator for preflight checks
            buying_power_service: Service for buying power verification

        """
        self.alpaca_manager = alpaca_manager
        self.validator = validator
        self.buying_power_service = buying_power_service

    def execute_market_order(self, symbol: str, side: str, quantity: Decimal) -> OrderResult:
        """Execute a standard market order with preflight validation.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares

        Returns:
            OrderResult with order details

        """
        validation_result = self._validate_market_order(symbol, quantity, side)

        if not validation_result.is_valid:
            return self._build_validation_failure_result(symbol, side, quantity, validation_result)

        final_quantity = validation_result.adjusted_quantity or quantity

        self._log_validation_warnings(validation_result)

        try:
            if side.lower() == "buy":
                self._ensure_buying_power(symbol, final_quantity)

            broker_result = self._place_market_order_with_broker(symbol, side, final_quantity)
            return self._build_market_order_execution_result(
                symbol, side, final_quantity, broker_result
            )
        except Exception as exc:
            return self._handle_market_order_exception(symbol, side, final_quantity, exc)

    def _validate_market_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
    ) -> OrderValidationResult:
        """Run preflight validation for the market order."""
        return self.validator.validate_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            auto_adjust=True,
        )

    def _build_validation_failure_result(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        validation_result: OrderValidationResult,
    ) -> OrderResult:
        """Construct execution result for validation failure."""
        error_msg = validation_result.error_message or f"Validation failed for {symbol}"
        logger.error(f"❌ Preflight validation failed for {symbol}: {error_msg}")
        return OrderResult(
            symbol=symbol,
            action=side.upper(),
            trade_amount=Decimal("0"),  # No trade executed
            shares=quantity,
            price=None,
            order_id=None,
            success=False,
            error_message=error_msg,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default order type
            filled_at=None,  # Not filled since validation failed
        )

    def _log_validation_warnings(self, validation_result: OrderValidationResult) -> None:
        """Log any warnings produced during validation."""
        for warning in validation_result.warnings:
            logger.warning(f"⚠️ {warning}")

    def _ensure_buying_power(self, symbol: str, quantity: Decimal) -> None:
        """Verify sufficient buying power for a purchase.

        Args:
            symbol: Stock symbol
            quantity: Number of shares to buy

        Raises:
            ValueError: If insufficient buying power

        """
        try:
            # Get current price to estimate required buying power
            try:
                price = self.alpaca_manager.get_current_price(symbol)
                if not price or price <= 0:
                    logger.warning(f"⚠️ Could not get price for {symbol} buying power check")
                    return  # Skip buying power check if no price available

                estimated_cost = quantity * Decimal(str(price))
            except Exception as exc:
                logger.warning(f"⚠️ Could not estimate cost for {symbol}: {exc}")
                return  # Skip buying power check if price unavailable

            buying_power_check = self.buying_power_service.verify_buying_power_available(
                estimated_cost
            )
            if not buying_power_check[0]:
                error_msg = (
                    f"Insufficient buying power for {symbol}: "
                    f"estimated cost=${estimated_cost:.2f}, "
                    f"available=${buying_power_check[1]:.2f}"
                )
                logger.error(f"💰 {error_msg}")
                raise ValueError(error_msg)
        except Exception as exc:
            if "Insufficient buying power" in str(exc):
                raise  # Re-raise buying power errors
            logger.warning(f"⚠️ Could not verify buying power for {symbol}: {exc}")
            # Skip buying power validation - broker will reject if insufficient funds
            return

    def _place_market_order_with_broker(
        self, symbol: str, side: str, quantity: Decimal
    ) -> ExecutedOrder:
        """Place market order with broker.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares

        Returns:
            Broker order object

        """
        return self.alpaca_manager.place_market_order(symbol, side, quantity)

    def _build_market_order_execution_result(
        self, symbol: str, side: str, quantity: Decimal, broker_result: ExecutedOrder
    ) -> OrderResult:
        """Build execution result from broker response.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            broker_result: Broker order response

        Returns:
            OrderResult with execution details

        """
        # Extract order details from broker result
        order_id = str(broker_result.id) if hasattr(broker_result, "id") else None
        filled_qty = getattr(broker_result, "filled_qty", Decimal("0"))
        avg_fill_price = getattr(broker_result, "filled_avg_price", None)

        trade_amount = filled_qty * avg_fill_price if avg_fill_price else Decimal("0")

        log_order_flow(
            logger,
            stage="submission",
            symbol=symbol,
            quantity=quantity,
            price=avg_fill_price,
            order_id=order_id,
            execution_strategy="market",
            side=side.upper(),
        )

        return OrderResult(
            symbol=symbol,
            action=side.upper(),
            trade_amount=trade_amount,
            shares=quantity,
            price=avg_fill_price,
            order_id=order_id,
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # This is a market order
            filled_at=datetime.now(UTC) if avg_fill_price else None,  # Set filled_at if executed
        )

    def _handle_market_order_exception(
        self, symbol: str, side: str, quantity: Decimal, exc: Exception
    ) -> OrderResult:
        """Handle exceptions during market order execution.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            exc: Exception that occurred

        Returns:
            OrderResult with error details

        """
        error_msg = f"Market order execution failed: {exc}"
        logger.error(f"❌ Market order failed for {symbol}: {error_msg}")

        return OrderResult(
            symbol=symbol,
            action=side.upper(),
            trade_amount=Decimal("0"),
            shares=quantity,
            price=None,
            order_id=None,
            success=False,
            error_message=error_msg,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default order type
            filled_at=None,  # Not filled due to error
        )
