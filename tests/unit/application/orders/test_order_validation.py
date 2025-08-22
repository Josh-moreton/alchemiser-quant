#!/usr/bin/env python3
"""
Tests for order validation DTO integration.

Tests the complete integration of OrderRequestDTO and ValidatedOrderDTO
into the order validation pipeline, ensuring type safety and validation.
"""

from decimal import Decimal
from datetime import datetime
import pytest
from unittest.mock import Mock

from the_alchemiser.application.orders.order_validation import (
    OrderValidator,
    OrderValidationError,
    ValidationResult,
)
from the_alchemiser.interfaces.schemas.orders import (
    OrderRequestDTO,
    ValidatedOrderDTO,
)
from the_alchemiser.application.mapping.orders import (
    dict_to_order_request_dto,
    order_request_to_validated_dto,
)


class TestOrderValidationDTOIntegration:
    """Test cases for DTO-based order validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = OrderValidator()

    def test_valid_market_order_dto_validation(self):
        """Test validation of a valid market order using DTOs."""
        # Create a valid market order request
        order_request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day"
        )

        # Validate using OrderValidator
        validated_order = self.validator.validate_order_request(order_request)

        # Verify the validated order
        assert isinstance(validated_order, ValidatedOrderDTO)
        assert validated_order.symbol == "AAPL"
        assert validated_order.side == "buy"
        assert validated_order.quantity == Decimal("100")
        assert validated_order.order_type == "market"
        assert validated_order.time_in_force == "day"
        assert isinstance(validated_order.validation_timestamp, datetime)

    def test_valid_limit_order_dto_validation(self):
        """Test validation of a valid limit order using DTOs."""
        # Create a valid limit order request
        order_request = OrderRequestDTO(
            symbol="TSLA",
            side="sell",
            quantity=Decimal("50"),
            order_type="limit",
            limit_price=Decimal("250.50"),
            time_in_force="gtc"
        )

        # Validate using OrderValidator
        validated_order = self.validator.validate_order_request(order_request)

        # Verify the validated order
        assert isinstance(validated_order, ValidatedOrderDTO)
        assert validated_order.symbol == "TSLA"
        assert validated_order.side == "sell"
        assert validated_order.quantity == Decimal("50")
        assert validated_order.order_type == "limit"
        assert validated_order.limit_price == Decimal("250.50")
        assert validated_order.time_in_force == "gtc"
        # Estimated value should be calculated for limit orders
        assert validated_order.estimated_value == Decimal("50") * Decimal("250.50")

    def test_invalid_symbol_validation(self):
        """Test validation fails for invalid symbol."""
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            OrderRequestDTO(
                symbol="",
                side="buy",
                quantity=Decimal("100"),
                order_type="market"
            )

    def test_invalid_side_validation(self):
        """Test validation fails for invalid side."""
        # This should be caught at DTO creation level
        with pytest.raises(ValueError):
            OrderRequestDTO(
                symbol="AAPL",
                side="invalid_side",  # type: ignore
                quantity=Decimal("100"),
                order_type="market"
            )

    def test_zero_quantity_validation(self):
        """Test validation fails for zero quantity."""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("0"),
                order_type="market"
            )

    def test_negative_quantity_validation(self):
        """Test validation fails for negative quantity."""
        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("-100"),
                order_type="market"
            )

    def test_limit_order_without_price_validation(self):
        """Test validation fails for limit order without price."""
        with pytest.raises(ValueError, match="Limit price required for limit orders"):
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                order_type="limit",
                limit_price=None
            )

    def test_negative_limit_price_validation(self):
        """Test validation fails for negative limit price."""
        with pytest.raises(ValueError, match="Limit price must be greater than 0"):
            OrderRequestDTO(
                symbol="AAPL",
                side="buy",
                quantity=Decimal("100"),
                order_type="limit",
                limit_price=Decimal("-50.00")
            )

    def test_dict_to_dto_conversion(self):
        """Test conversion from dictionary to OrderRequestDTO."""
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "time_in_force": "day"
        }

        order_request = dict_to_order_request_dto(order_data)

        assert isinstance(order_request, OrderRequestDTO)
        assert order_request.symbol == "AAPL"
        assert order_request.side == "buy"
        assert order_request.quantity == Decimal("100")
        assert order_request.order_type == "market"
        assert order_request.time_in_force == "day"

    def test_dict_missing_required_field(self):
        """Test conversion fails when required fields are missing."""
        order_data = {
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
            # Missing symbol
        }

        with pytest.raises(ValueError, match="Missing required field: symbol"):
            dict_to_order_request_dto(order_data)

    def test_order_structure_validation_success(self):
        """Test order structure validation with valid data."""
        order_data = {
            "symbol": "MSFT",
            "side": "sell",
            "quantity": 75,
            "order_type": "limit",
            "limit_price": 300.0,
            "time_in_force": "day"
        }

        result = self.validator.validate_order_structure(order_data)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.validated_order is not None
        assert result.validated_order.symbol == "MSFT"

    def test_order_structure_validation_failure(self):
        """Test order structure validation with invalid data."""
        order_data = {
            "symbol": "",  # Invalid symbol
            "side": "buy",
            "quantity": 100,
            "order_type": "market"
        }

        result = self.validator.validate_order_structure(order_data)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.validated_order is None

    def test_business_rules_validation(self):
        """Test business rules validation for order value limits."""
        # Create order that exceeds maximum order value
        large_order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("1000"),
            order_type="limit",
            limit_price=Decimal("100.00")  # $100,000 order
        )

        # This should trigger business rule validation error
        with pytest.raises(OrderValidationError, match="Order value.*exceeds maximum"):
            self.validator.validate_order_request(large_order)

    def test_fractional_quantity_detection(self):
        """Test detection of fractional quantities."""
        fractional_order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10.5"),
            order_type="market"
        )

        validated_order = self.validator.validate_order_request(fractional_order)

        assert validated_order.is_fractional is True

    def test_whole_quantity_detection(self):
        """Test detection of whole quantities."""
        whole_order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("10"),
            order_type="market"
        )

        validated_order = self.validator.validate_order_request(whole_order)

        assert validated_order.is_fractional is False

    def test_risk_score_calculation(self):
        """Test risk score calculation for limit orders."""
        limit_order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="limit",
            limit_price=Decimal("150.00")  # $15,000 order
        )

        validated_order = self.validator.validate_order_request(limit_order)

        # Risk score should be calculated based on order value
        assert validated_order.risk_score is not None
        assert isinstance(validated_order.risk_score, Decimal)
        assert Decimal("0") <= validated_order.risk_score <= Decimal("1")

    def test_market_order_no_estimated_value(self):
        """Test market order without estimated value calculation."""
        market_order = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market"
        )

        validated_order = self.validator.validate_order_request(market_order)

        # Market orders don't have estimated value without current price
        assert validated_order.estimated_value is None
        assert validated_order.risk_score is None

    def test_validation_timestamp_set(self):
        """Test that validation timestamp is set during validation."""
        from datetime import timezone
        
        order_request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market"
        )

        before_validation = datetime.now(timezone.utc)
        validated_order = self.validator.validate_order_request(order_request)
        after_validation = datetime.now(timezone.utc)

        # Validation timestamp should be between before and after
        assert before_validation <= validated_order.validation_timestamp <= after_validation