"""Business Unit: execution | Status: current.

Execution Validation Service.

Provides preflight validation for orders including fractionability checks
and quantity adjustments for non-fractionable assets.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors import AlchemiserError
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class ExecutionValidationError(AlchemiserError):
    """Exception raised when execution validation fails.

    This exception is raised during pre-flight order validation when an order
    cannot be placed due to validation constraints (e.g., non-tradable asset,
    invalid quantity, non-fractionable asset with fractional quantity).
    """

    def __init__(self, message: str, *, symbol: str, code: str | None = None) -> None:
        """Initialize with error details.

        Args:
            message: Error message
            symbol: Symbol that caused the error
            code: Optional error code (e.g., "40310000" for non-fractionable)

        """
        super().__init__(message)
        self.symbol = symbol
        self.code = code


class OrderValidationResult(BaseModel):
    """Result of order validation including any adjustments.

    This frozen DTO represents the outcome of order validation, including
    whether the order is valid, any quantity adjustments made, warnings,
    and error details if validation failed.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        extra="forbid",
    )

    is_valid: bool = Field(..., description="Whether order is valid and can proceed")
    adjusted_quantity: Decimal | None = Field(
        default=None, description="Adjusted quantity if changes were made"
    )
    warnings: tuple[str, ...] = Field(
        default_factory=tuple, description="Warnings about adjustments"
    )
    error_message: str | None = Field(
        default=None, description="Error message if validation failed"
    )
    error_code: str | None = Field(default=None, description="Error code if validation failed")
    schema_version: str = Field(default="1.0", description="Schema version for evolution tracking")
    correlation_id: str | None = Field(
        default=None, description="Request correlation ID for tracing"
    )


class ExecutionValidator:
    """Validates orders before placement including fractionability checks."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager for asset metadata.

        Args:
            alpaca_manager: AlpacaManager instance for asset info access

        """
        self.alpaca_manager = alpaca_manager

    def validate_order(
        self,
        symbol: str,
        quantity: Decimal,
        *,
        correlation_id: str | None = None,
        auto_adjust: bool = True,
    ) -> OrderValidationResult:
        """Validate order before placement.

        Args:
            symbol: Asset symbol
            quantity: Order quantity (must be positive)
            correlation_id: Optional correlation ID for tracing
            auto_adjust: Whether to auto-adjust non-fractionable quantities

        Returns:
            OrderValidationResult with validation outcome

        Raises:
            ExecutionValidationError: If validation encounters an unexpected error

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        # Validate quantity is positive (early validation)
        if quantity <= 0:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Invalid quantity {quantity} for {symbol} (must be positive)",
                error_code="INVALID_QUANTITY",
                correlation_id=correlation_id,
            )

        # Get asset info
        asset_info = self.alpaca_manager.get_asset_info(symbol)
        if asset_info is None:
            logger.warning(f"{log_prefix} Could not get asset info for {symbol}, allowing order")
            return OrderValidationResult(is_valid=True, correlation_id=correlation_id)

        # Check if asset is tradable
        if not asset_info.tradable:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Asset {symbol} is not tradable",
                error_code="NOT_TRADABLE",
                correlation_id=correlation_id,
            )

        # Check fractionability
        if not asset_info.fractionable:
            return self._validate_non_fractionable_order(
                symbol,
                quantity,
                correlation_id,
                auto_adjust=auto_adjust,
            )

        # Asset is fractionable, quantity already validated above
        return OrderValidationResult(is_valid=True, correlation_id=correlation_id)

    def _validate_non_fractionable_order(
        self,
        symbol: str,
        quantity: Decimal,
        correlation_id: str | None,
        *,
        auto_adjust: bool,
    ) -> OrderValidationResult:
        """Validate order for non-fractionable asset.

        Args:
            symbol: Asset symbol
            quantity: Order quantity (already validated as positive)
            correlation_id: Optional correlation ID for tracing
            auto_adjust: Whether to auto-adjust quantities

        Returns:
            OrderValidationResult with validation outcome

        Note:
            Uses default Decimal context for rounding (precision=28 digits).
            For whole share rounding with ROUND_DOWN, default context is sufficient.

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        # Check if quantity is already a whole number
        if quantity == quantity.to_integral_value():
            logger.debug(
                f"{log_prefix} Non-fractionable {symbol}: quantity {quantity} is already whole"
            )
            return OrderValidationResult(is_valid=True, correlation_id=correlation_id)

        # Quantity is fractional for non-fractionable asset
        if not auto_adjust:
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Asset {symbol} is not fractionable but quantity {quantity} is fractional",
                error_code="40310000",  # Alpaca error code for non-fractionable
                correlation_id=correlation_id,
            )

        # Auto-adjust by rounding down to whole shares
        # Uses default Decimal context (precision=28, rounding inherited)
        adjusted_quantity = quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)

        # Check if rounding resulted in zero quantity
        if adjusted_quantity <= 0:
            logger.warning(
                f"{log_prefix} ❌ Non-fractionable {symbol}: quantity {quantity} rounds to zero, rejecting order"
            )
            return OrderValidationResult(
                is_valid=False,
                error_message=f"Non-fractionable asset {symbol} quantity {quantity} rounds to zero",
                error_code="ZERO_QUANTITY_AFTER_ROUNDING",
                correlation_id=correlation_id,
            )

        # Successfully adjusted
        warning_msg = (
            f"Non-fractionable {symbol}: adjusted quantity {quantity} → {adjusted_quantity} shares"
        )
        logger.info(f"{log_prefix} 🔄 {warning_msg}")

        return OrderValidationResult(
            is_valid=True,
            adjusted_quantity=adjusted_quantity,
            warnings=(warning_msg,),  # Use tuple for immutable Pydantic model
            correlation_id=correlation_id,
        )
