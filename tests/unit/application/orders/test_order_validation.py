"""
Unit tests for order validation refactor using DTOs.

Tests cover the OrderValidator class and its methods to ensure proper
validation with OrderRequestDTO and ValidatedOrderDTO types.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from the_alchemiser.application.orders.order_validation import (
    OrderValidationError,
    OrderValidator,
    RiskLimits,
    ValidationResult,
)
from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO, ValidatedOrderDTO


class TestOrderValidator:
    """Test cases for OrderValidator using DTOs."""

    def test_validate_order_request_market_order(self) -> None:
        """Test validation of a valid market order request."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day",
        )
        
        result = validator.validate_order_request(request)
        
        assert isinstance(result, ValidatedOrderDTO)
        assert result.symbol == "AAPL"
        assert result.side == "buy"
        assert result.quantity == Decimal("100")
        assert result.order_type == "market"
        assert result.time_in_force == "day"
        assert result.limit_price is None
        assert result.is_fractional is False
        assert result.normalized_quantity == Decimal("100")
        assert isinstance(result.validation_timestamp, datetime)

    def test_validate_order_request_limit_order(self) -> None:
        """Test validation of a valid limit order request."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="TSLA",
            side="sell",
            quantity=Decimal("50"),
            order_type="limit",
            time_in_force="gtc",
            limit_price=Decimal("250.50"),
        )
        
        result = validator.validate_order_request(request)
        
        assert isinstance(result, ValidatedOrderDTO)
        assert result.symbol == "TSLA"
        assert result.side == "sell"
        assert result.quantity == Decimal("50")
        assert result.order_type == "limit"
        assert result.time_in_force == "gtc"
        assert result.limit_price == Decimal("250.50")
        assert result.estimated_value == Decimal("12525.00")  # 50 * 250.50
        assert result.risk_score is not None

    def test_validate_order_request_fractional_quantity(self) -> None:
        """Test validation with fractional quantity."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="SPY",
            side="buy",
            quantity=Decimal("10.5"),
            order_type="market",
        )
        
        result = validator.validate_order_request(request)
        
        assert result.quantity == Decimal("10.5")
        assert result.is_fractional is True

    def test_validate_order_request_high_precision_quantity_fails(self) -> None:
        """Test validation fails for quantity with too many decimal places."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100.1234567"),  # 7 decimal places - should fail
            order_type="market",
        )
        
        with pytest.raises(OrderValidationError) as exc_info:
            validator.validate_order_request(request)
        
        assert "too many decimal places" in str(exc_info.value)

    def test_validate_order_request_high_precision_limit_price_fails(self) -> None:
        """Test validation fails for limit price with too many decimal places."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="limit",
            limit_price=Decimal("150.123"),  # 3 decimal places - should fail
        )
        
        with pytest.raises(OrderValidationError) as exc_info:
            validator.validate_order_request(request)
        
        assert "too many decimal places" in str(exc_info.value)

    def test_validate_order_request_exceeds_max_value(self) -> None:
        """Test validation fails when order value exceeds risk limits."""
        risk_limits = RiskLimits(max_order_value=10000.0)  # $10k limit
        validator = OrderValidator(risk_limits=risk_limits)
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="limit",
            limit_price=Decimal("150.00"),  # Total: $15,000 - exceeds limit
        )
        
        with pytest.raises(OrderValidationError) as exc_info:
            validator.validate_order_request(request)
        
        assert "exceeds maximum" in str(exc_info.value)

    def test_validate_order_request_below_min_value(self) -> None:
        """Test validation fails when order value is below minimum."""
        risk_limits = RiskLimits(min_order_value=100.0)  # $100 minimum
        validator = OrderValidator(risk_limits=risk_limits)
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("1"),
            order_type="limit",
            limit_price=Decimal("50.00"),  # Total: $50 - below minimum
        )
        
        with pytest.raises(OrderValidationError) as exc_info:
            validator.validate_order_request(request)
        
        assert "below minimum" in str(exc_info.value)

    def test_validate_order_structure_from_dict_success(self) -> None:
        """Test successful validation from dictionary."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 25,
            "order_type": "market",
            "time_in_force": "day",
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.validated_order is not None
        assert result.validated_order.symbol == "NVDA"
        assert result.validated_order.quantity == Decimal("25")

    def test_validate_order_structure_missing_symbol_fails(self) -> None:
        """Test validation fails when symbol is missing."""
        validator = OrderValidator()
        
        order_data = {
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "symbol" in str(result.errors[0]).lower()
        assert result.validated_order is None

    def test_validate_order_structure_invalid_side_fails(self) -> None:
        """Test validation fails for invalid side."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "AAPL",
            "side": "invalid_side",
            "quantity": 100,
            "order_type": "market",
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "Invalid side" in str(result.errors[0])

    def test_validate_order_structure_zero_quantity_fails(self) -> None:
        """Test validation fails for zero quantity."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 0,
            "order_type": "market",
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_order_structure_negative_quantity_fails(self) -> None:
        """Test validation fails for negative quantity."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": -10,
            "order_type": "market",
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_order_structure_limit_without_price_fails(self) -> None:
        """Test validation fails for limit order without limit_price."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "limit",
            # Missing limit_price
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_order_structure_uppercase_normalization(self) -> None:
        """Test that uppercase inputs are properly normalized."""
        validator = OrderValidator()
        
        order_data = {
            "symbol": "aapl",  # lowercase
            "side": "BUY",     # uppercase
            "quantity": 100,
            "order_type": "MARKET",  # uppercase
            "time_in_force": "DAY",  # uppercase
        }
        
        result = validator.validate_order_structure(order_data)
        
        assert result.is_valid is True
        assert result.validated_order is not None
        assert result.validated_order.symbol == "AAPL"  # normalized to uppercase
        assert result.validated_order.side == "buy"     # normalized to lowercase
        assert result.validated_order.order_type == "market"  # normalized to lowercase

    def test_risk_score_calculation(self) -> None:
        """Test risk score calculation for limit orders."""
        risk_limits = RiskLimits(max_order_value=10000.0)
        validator = OrderValidator(risk_limits=risk_limits)
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("50"),
            order_type="limit",
            limit_price=Decimal("100.00"),  # Total: $5,000 = 0.5 risk ratio
        )
        
        result = validator.validate_order_request(request)
        
        assert result.risk_score == Decimal("0.5")
        assert result.estimated_value == Decimal("5000.00")

    def test_market_order_no_estimated_value(self) -> None:
        """Test market orders don't get estimated value (no current price)."""
        validator = OrderValidator()
        
        request = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
        )
        
        result = validator.validate_order_request(request)
        
        assert result.estimated_value is None
        assert result.risk_score is None


class TestRiskLimits:
    """Test cases for RiskLimits configuration."""

    def test_default_risk_limits(self) -> None:
        """Test default risk limits are reasonable."""
        limits = RiskLimits()
        # Avoid float equality checks; use tolerant comparisons
        assert limits.max_position_pct == pytest.approx(0.10)
        assert limits.max_portfolio_concentration == pytest.approx(0.25)
        assert limits.max_order_value == pytest.approx(50000.0)
        assert limits.min_order_value == pytest.approx(1.0)
        assert limits.max_daily_trades == 100

    def test_custom_risk_limits(self) -> None:
        """Test custom risk limits can be configured."""
        limits = RiskLimits(
            max_order_value=25000.0,
            min_order_value=10.0,
            max_daily_trades=50,
        )
        # Avoid float equality checks; use tolerant comparisons
        assert limits.max_order_value == pytest.approx(25000.0)
        assert limits.min_order_value == pytest.approx(10.0)
        assert limits.max_daily_trades == 50


class TestValidationResult:
    """Test cases for ValidationResult data structure."""

    def test_validation_result_success(self) -> None:
        """Test successful validation result."""
        validated_order = ValidatedOrderDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day",
            validation_timestamp=datetime.now(),
        )

        result = ValidationResult(
            is_valid=True,
            validated_order=validated_order,
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.validated_order is validated_order

    def test_validation_result_failure(self) -> None:
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            errors=["Missing symbol", "Invalid quantity"],
            warnings=["Order may incur fees"],
        )

        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.validated_order is None
