"""Tests for order mapping functions."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from the_alchemiser.application.mapping.orders import (
    order_request_dto_to_domain_order_params,
    domain_order_to_execution_result_dto,
)
from the_alchemiser.interfaces.schemas.orders import OrderRequestDTO, OrderExecutionResultDTO
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_status import OrderStatus
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.shared_kernel.value_objects.money import Money


class TestOrderRequestDTOToDomainOrderParams:
    """Test conversion from OrderRequestDTO to domain order parameters."""

    def test_market_order_conversion(self) -> None:
        """Test converting market order DTO to domain parameters."""
        dto = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            time_in_force="day",
        )

        params = order_request_dto_to_domain_order_params(dto)

        assert isinstance(params["id"], OrderId)
        assert params["symbol"] == Symbol("AAPL")
        assert params["quantity"] == Quantity(Decimal("100"))
        assert params["status"] == OrderStatus.NEW
        assert params["order_type"] == "MARKET"
        assert params["limit_price"] is None
        assert params["side"] == "buy"
        assert params["time_in_force"] == "day"
        assert params["client_order_id"] is None

    def test_limit_order_conversion(self) -> None:
        """Test converting limit order DTO to domain parameters."""
        dto = OrderRequestDTO(
            symbol="TSLA",
            side="sell",
            quantity=Decimal("50"),
            order_type="limit",
            time_in_force="gtc",
            limit_price=Decimal("250.75"),
            client_order_id="TEST123",
        )

        params = order_request_dto_to_domain_order_params(dto)

        assert isinstance(params["id"], OrderId)
        assert params["symbol"] == Symbol("TSLA")
        assert params["quantity"] == Quantity(Decimal("50"))
        assert params["status"] == OrderStatus.NEW
        assert params["order_type"] == "LIMIT"
        assert params["limit_price"] == Money(Decimal("250.75"), "USD")
        assert params["side"] == "sell"
        assert params["time_in_force"] == "gtc"
        assert params["client_order_id"] == "TEST123"

    def test_symbol_case_handling(self) -> None:
        """Test that symbol is properly handled regardless of case."""
        dto = OrderRequestDTO(
            symbol="spy",  # lowercase
            side="buy",
            quantity=Decimal("10"),
            order_type="market",
        )

        params = order_request_dto_to_domain_order_params(dto)

        # Symbol value object should normalize to uppercase
        assert params["symbol"] == Symbol("SPY")

    def test_decimal_precision_preservation(self) -> None:
        """Test that Decimal precision is preserved through mapping."""
        dto = OrderRequestDTO(
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100.000000"),
            order_type="limit",
            limit_price=Decimal("150.2500"),
        )

        params = order_request_dto_to_domain_order_params(dto)

        # Quantities should be preserved as Decimal
        assert params["quantity"].value == Decimal("100.000000")
        assert isinstance(params["limit_price"], Money)
        assert params["limit_price"].amount == Decimal("150.25")  # Money normalizes to 2 decimal places


class TestDomainOrderToExecutionResultDTO:
    """Test conversion from domain Order to OrderExecutionResultDTO."""

    def test_new_order_conversion(self) -> None:
        """Test converting new order to execution result DTO."""
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("AAPL"),
            quantity=Quantity(Decimal("100")),
            status=OrderStatus.NEW,
            order_type="MARKET",
        )

        result = domain_order_to_execution_result_dto(order)

        assert isinstance(result, OrderExecutionResultDTO)
        assert result.order_id == str(order.id.value)
        assert result.status == "accepted"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert result.submitted_at == order.created_at
        assert result.completed_at is None

    def test_filled_order_conversion(self) -> None:
        """Test converting filled order to execution result DTO."""
        order_id = OrderId.generate()
        limit_price = Money(Decimal("150.00"), "USD")
        created_time = datetime.now(UTC)
        
        order = Order(
            id=order_id,
            symbol=Symbol("AAPL"),
            quantity=Quantity(Decimal("100")),
            status=OrderStatus.FILLED,
            order_type="LIMIT",
            limit_price=limit_price,
            filled_quantity=Quantity(Decimal("100")),
            created_at=created_time,
        )

        result = domain_order_to_execution_result_dto(order)

        assert result.order_id == str(order_id.value)
        assert result.status == "filled"
        assert result.filled_qty == Decimal("100")
        assert result.avg_fill_price == Decimal("150.00")
        assert result.submitted_at == created_time
        assert result.completed_at == created_time  # Simplified completion time

    def test_partially_filled_order_conversion(self) -> None:
        """Test converting partially filled order to execution result DTO."""
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("TSLA"),
            quantity=Quantity(Decimal("100")),
            status=OrderStatus.PARTIALLY_FILLED,
            order_type="LIMIT",
            limit_price=Money(Decimal("250.50"), "USD"),
            filled_quantity=Quantity(Decimal("50")),
        )

        result = domain_order_to_execution_result_dto(order)

        assert result.status == "partially_filled"
        assert result.filled_qty == Decimal("50")
        assert result.avg_fill_price == Decimal("250.50")
        assert result.completed_at is None  # Not completed yet

    def test_cancelled_order_conversion(self) -> None:
        """Test converting cancelled order to execution result DTO."""
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("SPY"),
            quantity=Quantity(Decimal("200")),
            status=OrderStatus.CANCELLED,
            order_type="MARKET",
        )

        result = domain_order_to_execution_result_dto(order)

        assert result.status == "canceled"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert result.completed_at == order.created_at

    def test_rejected_order_conversion(self) -> None:
        """Test converting rejected order to execution result DTO."""
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("GME"),
            quantity=Quantity(Decimal("10")),
            status=OrderStatus.REJECTED,
            order_type="LIMIT",
            limit_price=Money(Decimal("100.00"), "USD"),
        )

        result = domain_order_to_execution_result_dto(order)

        assert result.status == "rejected"
        assert result.filled_qty == Decimal("0")
        assert result.avg_fill_price is None
        assert result.completed_at == order.created_at

    def test_invalid_status_raises_error(self) -> None:
        """Test that invalid order status raises error."""
        # Create an order with an invalid status (this would be a programming error)
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("AAPL"),
            quantity=Quantity(Decimal("100")),
            status="INVALID_STATUS",  # type: ignore[arg-type]
            order_type="MARKET",
        )

        with pytest.raises(ValueError, match="Cannot map order status"):
            domain_order_to_execution_result_dto(order)

    def test_decimal_precision_in_result(self) -> None:
        """Test that Decimal precision is maintained in result DTO."""
        order = Order(
            id=OrderId.generate(),
            symbol=Symbol("AAPL"),
            quantity=Quantity(Decimal("100")),
            status=OrderStatus.FILLED,
            order_type="LIMIT",
            limit_price=Money(Decimal("150.2575"), "USD"),  # Will be normalized to 150.26
            filled_quantity=Quantity(Decimal("100")),
        )

        result = domain_order_to_execution_result_dto(order)

        # Check that we maintain proper Decimal types and precision
        assert isinstance(result.filled_qty, Decimal)
        assert isinstance(result.avg_fill_price, Decimal)
        assert result.avg_fill_price == Decimal("150.26")  # Money normalized to 2 decimal places