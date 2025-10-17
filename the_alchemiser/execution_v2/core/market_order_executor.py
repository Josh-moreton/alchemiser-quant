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
from the_alchemiser.shared.errors import (
    BuyingPowerError,
    DataProviderError,
    OrderExecutionError,
)
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

    def execute_market_order(
        self, symbol: str, side: str, quantity: Decimal, *, correlation_id: str | None = None
    ) -> OrderResult:
        """Execute a standard market order with preflight validation.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            correlation_id: Optional correlation ID for traceability

        Returns:
            OrderResult with order details

        Raises:
            OrderExecutionError: If order execution fails
            BuyingPowerError: If insufficient buying power for purchase

        """
        validation_result = self._preflight_validation(
            symbol, quantity, side, correlation_id=correlation_id
        )

        if not validation_result.is_valid:
            return self._build_validation_failure_result(
                symbol, side, quantity, validation_result, correlation_id=correlation_id
            )

        final_quantity = validation_result.adjusted_quantity or quantity

        self._log_validation_warnings(validation_result)

        try:
            if side.lower() == "buy":
                self._ensure_buying_power(symbol, final_quantity, correlation_id=correlation_id)

            broker_result = self._place_market_order_with_broker(symbol, side, final_quantity)
            return self._build_market_order_execution_result(
                symbol, side, final_quantity, broker_result, correlation_id=correlation_id
            )
        except (BuyingPowerError, OrderExecutionError):
            # Re-raise typed execution errors without wrapping
            raise
        except Exception as exc:
            return self._handle_market_order_exception(
                symbol, side, final_quantity, exc, correlation_id=correlation_id
            )

    def _preflight_validation(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        *,
        correlation_id: str | None = None,
    ) -> OrderValidationResult:
        """Run preflight validation for the market order.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: "buy" or "sell"
            correlation_id: Optional correlation ID for traceability

        Returns:
            OrderValidationResult with validation outcome

        """
        # Ensure side is lowercase for validator
        side_normalized = side.lower()
        if side_normalized not in ("buy", "sell"):
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Invalid side: {side}. Must be 'buy' or 'sell'",
                error_code="INVALID_SIDE",
                correlation_id=correlation_id,
            )

        return self.validator.validate_order(
            symbol=symbol,
            quantity=quantity,
            auto_adjust=True,
            correlation_id=correlation_id,
        )

    def _build_validation_failure_result(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        validation_result: OrderValidationResult,
        *,
        correlation_id: str | None = None,
    ) -> OrderResult:
        """Construct execution result for validation failure.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            validation_result: Validation result with error details
            correlation_id: Optional correlation ID for traceability

        Returns:
            OrderResult indicating validation failure

        """
        error_msg = validation_result.error_message or f"Validation failed for {symbol}"
        logger.error(
            "Preflight validation failed",
            symbol=symbol,
            side=side,
            error=error_msg,
            correlation_id=correlation_id,
        )
        side_upper = self._normalize_side(side)
        return OrderResult(
            symbol=symbol,
            action=side_upper,  # type: ignore[arg-type]
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
        """Log any warnings produced during validation.

        Args:
            validation_result: Validation result containing warnings

        """
        for warning in validation_result.warnings:
            logger.warning("Validation warning", warning=warning)

    def _normalize_side(self, side: str) -> str:
        """Normalize and validate order side.

        Args:
            side: Order side ("buy" or "sell", case-insensitive)

        Returns:
            Normalized side as "BUY" or "SELL"

        Raises:
            ValueError: If side is not "buy" or "sell"

        """
        side_upper = side.upper()
        if side_upper not in ("BUY", "SELL"):
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")
        return side_upper

    def _ensure_buying_power(
        self, symbol: str, quantity: Decimal, *, correlation_id: str | None = None
    ) -> None:
        """Verify sufficient buying power for a purchase.

        Args:
            symbol: Stock symbol
            quantity: Number of shares to buy
            correlation_id: Optional correlation ID for traceability

        Raises:
            BuyingPowerError: If insufficient buying power
            DataProviderError: If unable to get price data for validation

        """
        try:
            price = self.alpaca_manager.get_current_price(symbol)
        except Exception as exc:
            raise DataProviderError(
                f"Could not get price for {symbol} buying power check: {exc}",
                context={"symbol": symbol, "correlation_id": correlation_id},
            ) from exc

        if not price or price <= 0:
            raise DataProviderError(
                f"Invalid price for {symbol}: {price}",
                context={"symbol": symbol, "price": price, "correlation_id": correlation_id},
            )

        estimated_cost = quantity * Decimal(str(price))

        buying_power_check = self.buying_power_service.verify_buying_power_available(
            estimated_cost, correlation_id=correlation_id
        )

        if not buying_power_check[0]:
            available = buying_power_check[1]
            shortfall = estimated_cost - available
            raise BuyingPowerError(
                f"Insufficient buying power for {symbol}",
                symbol=symbol,
                required_amount=float(estimated_cost),
                available_amount=float(available),
                shortfall=float(shortfall),
            )

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
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        broker_result: ExecutedOrder,
        *,
        correlation_id: str | None = None,
    ) -> OrderResult:
        """Build execution result from broker response.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            broker_result: Broker order response
            correlation_id: Optional correlation ID for traceability

        Returns:
            OrderResult with execution details

        """
        # Extract order details from broker result
        order_id = str(broker_result.id) if hasattr(broker_result, "id") else None
        filled_qty = getattr(broker_result, "filled_qty", Decimal("0"))
        avg_fill_price = getattr(broker_result, "filled_avg_price", None)

        # Fix: Add parentheses to ensure correct operator precedence
        trade_amount = (filled_qty * avg_fill_price) if avg_fill_price else Decimal("0")

        log_order_flow(
            logger,
            stage="submission",
            symbol=symbol,
            quantity=quantity,
            price=avg_fill_price,
            order_id=order_id,
            execution_strategy="market",
            side=side.upper(),
            correlation_id=correlation_id,
        )

        side_upper = self._normalize_side(side)
        return OrderResult(
            symbol=symbol,
            action=side_upper,  # type: ignore[arg-type]
            trade_amount=trade_amount,
            shares=quantity,
            price=avg_fill_price,
            order_id=order_id,
            success=True,
            error_message=None,
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # This is a market order
            filled_at=(datetime.now(UTC) if avg_fill_price else None),  # Set filled_at if executed
        )

    def _handle_market_order_exception(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        exc: Exception,
        *,
        correlation_id: str | None = None,
    ) -> OrderResult:
        """Handle exceptions during market order execution.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            exc: Exception that occurred
            correlation_id: Optional correlation ID for traceability

        Returns:
            OrderResult with error details

        """
        error_msg = f"Market order execution failed: {exc}"
        logger.error(
            "Market order failed",
            symbol=symbol,
            side=side,
            quantity=quantity,
            error=str(exc),
            error_type=type(exc).__name__,
            correlation_id=correlation_id,
        )

        side_upper = self._normalize_side(side)
        return OrderResult(
            symbol=symbol,
            action=side_upper,  # type: ignore[arg-type]
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
