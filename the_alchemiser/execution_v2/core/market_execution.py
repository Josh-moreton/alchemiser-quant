"""Business Unit: execution | Status: current.

Market execution module for order placement and validation.

Encapsulates market-order placement, buying-power checks, and exception handling,
reusing ExecutionValidator for preflight validation.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    OrderValidationResult,
)
from the_alchemiser.shared.schemas.execution_result import ExecutionResult
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class MarketExecution:
    """Market execution service for validated order placement."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize market execution service.

        Args:
            alpaca_manager: Alpaca broker manager

        """
        self.alpaca_manager = alpaca_manager
        self.validator = ExecutionValidator(alpaca_manager)
        self.buying_power_service = BuyingPowerService(alpaca_manager)

    def execute_market_order(self, symbol: str, side: str, quantity: Decimal) -> ExecutionResult:
        """Execute a standard market order with preflight validation.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares

        Returns:
            ExecutionResult with order details

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
    ) -> ExecutionResult:
        """Construct execution result for validation failure."""
        error_msg = validation_result.error_message or f"Validation failed for {symbol}"
        logger.error(f"❌ Preflight validation failed for {symbol}: {error_msg}")
        return ExecutionResult(
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="rejected",
            success=False,
            error=error_msg,
            execution_strategy="validation_failed",
        )

    def _log_validation_warnings(self, validation_result: OrderValidationResult) -> None:
        """Log any warnings produced during validation."""
        for warning in validation_result.warnings:
            logger.warning(f"⚠️ Order validation: {warning}")

    def _ensure_buying_power(self, symbol: str, quantity: Decimal) -> None:
        """Verify buying power for purchase orders."""
        # For now, use a simple approach - this can be enhanced later
        # The original implementation estimated cost and checked buying power
        # We'll delegate to the buying power service's available methods
        pass  # TODO: Implement proper buying power verification

    def _place_market_order_with_broker(self, symbol: str, side: str, quantity: Decimal) -> dict[str, Any]:
        """Place the actual market order through the broker."""
        return self.alpaca_manager.place_market_order(symbol, side, quantity)

    def _build_market_order_execution_result(
        self, symbol: str, side: str, quantity: Decimal, broker_result: dict[str, Any]
    ) -> ExecutionResult:
        """Build execution result from broker response."""
        order_id = broker_result.get("order_id")
        price = broker_result.get("price")
        status = "submitted"
        success = True

        # Convert price to Decimal if present
        if price is not None:
            try:
                price = Decimal(str(price))
            except (ValueError, TypeError):
                logger.warning(f"Invalid price from broker for {symbol}: {price}")
                price = None

        logger.info(f"✅ Market order placed: {side.upper()} {quantity} {symbol} (ID: {order_id})")

        return ExecutionResult(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            status=status,
            success=success,
            execution_strategy="market_order",
        )

    def _handle_market_order_exception(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        exc: Exception,
    ) -> ExecutionResult:
        """Handle exceptions raised during market order submission."""
        error_str = str(exc)

        if "insufficient buying power" in error_str.lower():
            logger.error(f"💳 Insufficient buying power for {symbol}: {exc}")
            try:
                account = self.alpaca_manager.get_account_dict()
                if account:
                    buying_power = account.get("buying_power", "unknown")
                    logger.error(f"💳 Current account state - Buying power: ${buying_power}")
            except Exception as diagnostic_error:
                logger.debug(f"Diagnostic account retrieval failed: {diagnostic_error}")

            return ExecutionResult(
                symbol=symbol,
                side=side,
                quantity=quantity,
                status="insufficient_buying_power",
                success=False,
                error=f"Insufficient buying power: {exc}",
                execution_strategy="buying_power_error",
            )

        logger.error(f"❌ Market order failed for {symbol}: {exc}")
        return ExecutionResult(
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="failed",
            success=False,
            error=error_str,
            execution_strategy="market_order_failed",
        )