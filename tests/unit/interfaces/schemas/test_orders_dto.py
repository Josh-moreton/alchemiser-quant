"""
Unit tests for Order DTOs.

Tests cover happy path scenarios and validation failures for all order DTOs
to ensure proper Pydantic v2 validation and type safety.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.interfaces.schemas.orders import (
    OrderExecutionResultDTO,
    OrderRequestDTO,
    ValidatedOrderDTO,
)


class TestOrderRequestDTO:
    """Test cases for OrderRequestDTO validation and normalization."""

    def test_valid_market_order_request(self) -> None:
        """Test creating a valid market order request."""
        order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day",
        )

        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.quantity == Decimal("100")
        assert order.order_type == "market"
        assert order.time_in_force == "day"
        assert order.limit_price is None
        assert order.client_order_id is None

    def test_valid_limit_order_request(self) -> None:
        """Test creating a valid limit order request."""
        order = OrderRequestDTO(
            symbol="tsla",  # Test lowercase normalization
            side="sell",
            quantity=Decimal("50"),
            order_type="limit",
            time_in_force="gtc",
            limit_price=Decimal("250.50"),
            client_order_id="my-order-123",
        )

        assert order.symbol == "TSLA"  # Should be normalized to uppercase
        assert order.side == "sell"
        assert order.quantity == Decimal("50")
        assert order.order_type == "limit"
        assert order.time_in_force == "gtc"
        assert order.limit_price == Decimal("250.50")
        assert order.client_order_id == "my-order-123"

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase and stripped."""
        order = OrderRequestDTO(
            symbol="  nvda  ",  # Test whitespace handling
            side="buy",
            quantity=Decimal("10"),
            order_type="market",
        )

        assert order.symbol == "NVDA"

    def test_empty_symbol_validation(self) -> None:
        """Test validation fails for empty symbol."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="",
                side="buy",
                quantity=Decimal("100"),
                order_type="market",
            )

        error = exc_info.value.errors()[0]
        assert "Symbol cannot be empty" in str(error["ctx"]["error"])

    def test_non_alphanumeric_symbol_validation(self) -> None:
        """Test validation fails for non-alphanumeric symbols."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL-USD",  # Contains hyphen
                side="buy",
                quantity=Decimal("100"),
                order_type="market",
            )

        error = exc_info.value.errors()[0]
        assert "Symbol must be alphanumeric" in str(error["ctx"]["error"])

    def test_invalid_quantity_zero(self) -> None:
        """Test validation fails for zero quantity."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("0"),
                order_type="market",
            )

        error = exc_info.value.errors()[0]
        assert "Quantity must be greater than 0" in str(error["ctx"]["error"])

    def test_invalid_quantity_negative(self) -> None:
        """Test validation fails for negative quantity."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("-10"),
                order_type="market",
            )

        error = exc_info.value.errors()[0]
        assert "Quantity must be greater than 0" in str(error["ctx"]["error"])

    def test_missing_limit_price_for_limit_order(self) -> None:
        """Test validation fails when limit_price is missing for limit orders."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                order_type="limit",
                # limit_price is missing
            )

        error = exc_info.value.errors()[0]
        assert "Limit price required for limit orders" in str(error["ctx"]["error"])

    def test_zero_limit_price_validation(self) -> None:
        """Test validation fails for zero limit price."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                order_type="limit",
                limit_price=Decimal("0"),
            )

        error = exc_info.value.errors()[0]
        assert "Limit price must be greater than 0" in str(error["ctx"]["error"])

    def test_negative_limit_price_validation(self) -> None:
        """Test validation fails for negative limit price."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                order_type="limit",
                limit_price=Decimal("-50.00"),
            )

        error = exc_info.value.errors()[0]
        assert "Limit price must be greater than 0" in str(error["ctx"]["error"])

    def test_market_order_with_limit_price_allowed(self) -> None:
        """Test market order can have limit_price (it's just ignored)."""
        order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            limit_price=Decimal("150.00"),  # Should be allowed for market orders
        )

        assert order.limit_price == Decimal("150.00")

    def test_immutable_order(self) -> None:
        """Test that order DTOs are immutable."""
        order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
        )

        with pytest.raises(ValidationError):
            order.symbol = "TSLA"  # Should fail due to frozen=True


class TestValidatedOrderDTO:
    """Test cases for ValidatedOrderDTO with derived fields."""

    def test_valid_validated_order(self) -> None:
        """Test creating a valid validated order with derived fields."""
        validation_time = datetime.now(UTC)

        order = ValidatedOrderDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day",
            estimated_value=Decimal("15000.00"),
            is_fractional=False,
            normalized_quantity=Decimal("100"),
            risk_score=Decimal("0.25"),
            validation_timestamp=validation_time,
        )

        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.quantity == Decimal("100")
        assert order.estimated_value == Decimal("15000.00")
        assert order.is_fractional is False
        assert order.normalized_quantity == Decimal("100")
        assert order.risk_score == Decimal("0.25")
        assert order.validation_timestamp == validation_time

    def test_validated_order_inherits_base_validation(self) -> None:
        """Test ValidatedOrderDTO inherits validation from OrderRequestDTO."""
        validation_time = datetime.now(UTC)

        with pytest.raises(ValidationError) as exc_info:
            ValidatedOrderDTO(
                symbol="",  # Empty symbol should fail
                side="buy",
                quantity=Decimal("100"),
                order_type="market",
                time_in_force="day",
                validation_timestamp=validation_time,
            )

        error = exc_info.value.errors()[0]
        assert "Symbol cannot be empty" in str(error["ctx"]["error"])


class TestOrderExecutionResultDTO:
    """Test cases for OrderExecutionResultDTO."""

    def test_valid_execution_result_filled(self) -> None:
        """Test creating a valid filled order execution result."""
        submitted_time = datetime.now(UTC)
        completed_time = submitted_time.replace(second=submitted_time.second + 5)

        result = OrderExecutionResultDTO(
            order_id="order-123",
            status="filled",
            filled_qty=Decimal("100"),
            avg_fill_price=Decimal("150.25"),
            submitted_at=submitted_time,
            completed_at=completed_time,
        )

        assert result.order_id == "order-123"
        assert result.status == "filled"
        assert result.filled_qty == Decimal("100")
        assert result.avg_fill_price == Decimal("150.25")
        assert result.submitted_at == submitted_time
        assert result.completed_at == completed_time

    def test_valid_execution_result_pending(self) -> None:
        """Test creating a valid pending order execution result."""
        submitted_time = datetime.now(UTC)

        result = OrderExecutionResultDTO(
            order_id="order-456",
            status="accepted",
            filled_qty=Decimal("0"),
            avg_fill_price=None,  # No fill price for pending order
            submitted_at=submitted_time,
            completed_at=None,  # Not completed yet
        )

        assert result.order_id == "order-456"
        assert result.status == "accepted"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert result.submitted_at == submitted_time
        assert result.completed_at is None

    def test_negative_filled_qty_validation(self) -> None:
        """Test validation fails for negative filled quantity."""
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResultDTO(
                order_id="order-123",
                status="filled",
                filled_qty=Decimal("-10"),  # Negative filled qty
                submitted_at=datetime.now(UTC),
            )

        error = exc_info.value.errors()[0]
        assert "Filled quantity cannot be negative" in str(error["ctx"]["error"])

    def test_zero_avg_fill_price_validation(self) -> None:
        """Test validation fails for zero average fill price."""
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResultDTO(
                order_id="order-123",
                status="filled",
                filled_qty=Decimal("100"),
                avg_fill_price=Decimal("0"),  # Zero price
                submitted_at=datetime.now(UTC),
            )

        error = exc_info.value.errors()[0]
        assert "Average fill price must be greater than 0" in str(error["ctx"]["error"])

    def test_negative_avg_fill_price_validation(self) -> None:
        """Test validation fails for negative average fill price."""
        with pytest.raises(ValidationError) as exc_info:
            OrderExecutionResultDTO(
                order_id="order-123",
                status="filled",
                filled_qty=Decimal("100"),
                avg_fill_price=Decimal("-150.00"),  # Negative price
                submitted_at=datetime.now(UTC),
            )

        error = exc_info.value.errors()[0]
        assert "Average fill price must be greater than 0" in str(error["ctx"]["error"])

    def test_execution_result_immutable(self) -> None:
        """Test that execution result DTOs are immutable."""
        result = OrderExecutionResultDTO(
            order_id="order-123",
            status="filled",
            filled_qty=Decimal("100"),
            submitted_at=datetime.now(UTC),
        )

        with pytest.raises(ValidationError):
            result.status = "canceled"  # Should fail due to frozen=True
