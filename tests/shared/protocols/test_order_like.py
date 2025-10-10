"""Business Unit: shared | Status: current.

Tests for order_like protocols.

Validates that OrderLikeProtocol and PositionLikeProtocol are correctly
defined and that implementations can conform to them properly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from the_alchemiser.shared.protocols.order_like import (
    OrderLikeProtocol,
    PositionLikeProtocol,
)

if TYPE_CHECKING:
    pass


class MockOrder:
    """Mock implementation that conforms to OrderLikeProtocol."""

    def __init__(
        self,
        id: str | None = "order-123",
        symbol: str = "AAPL",
        qty: float | int | str | None = 100,
        side: str = "buy",
        order_type: str | None = "market",
        status: str | None = "filled",
        filled_qty: float | int | str | None = 100,
    ) -> None:
        """Initialize mock order."""
        self._id = id
        self._symbol = symbol
        self._qty = qty
        self._side = side
        self._order_type = order_type
        self._status = status
        self._filled_qty = filled_qty

    @property
    def id(self) -> str | None:
        """Order identifier."""
        return self._id

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        return self._symbol

    @property
    def qty(self) -> float | int | str | None:
        """Order quantity."""
        return self._qty

    @property
    def side(self) -> str:
        """Order side."""
        return self._side

    @property
    def order_type(self) -> str | None:
        """Order type."""
        return self._order_type

    @property
    def status(self) -> str | None:
        """Order status."""
        return self._status

    @property
    def filled_qty(self) -> float | int | str | None:
        """Filled quantity."""
        return self._filled_qty


class MockPosition:
    """Mock implementation that conforms to PositionLikeProtocol."""

    def __init__(
        self,
        symbol: str = "AAPL",
        qty: float | int | str = 100,
        market_value: float | int | str | None = 15000.0,
        avg_entry_price: float | int | str | None = 150.0,
    ) -> None:
        """Initialize mock position."""
        self._symbol = symbol
        self._qty = qty
        self._market_value = market_value
        self._avg_entry_price = avg_entry_price

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        return self._symbol

    @property
    def qty(self) -> float | int | str:
        """Position quantity."""
        return self._qty

    @property
    def market_value(self) -> float | int | str | None:
        """Current market value."""
        return self._market_value

    @property
    def avg_entry_price(self) -> float | int | str | None:
        """Average entry price."""
        return self._avg_entry_price


class IncompleteOrder:
    """Mock that doesn't fully conform to OrderLikeProtocol (missing properties)."""

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        return "AAPL"

    @property
    def qty(self) -> float:
        """Order quantity."""
        return 100.0

    # Missing: id, side, order_type, status, filled_qty


class TestOrderLikeProtocol:
    """Test suite for OrderLikeProtocol."""

    def test_runtime_checkable(self) -> None:
        """Test that OrderLikeProtocol is runtime checkable."""
        order = MockOrder()
        assert isinstance(order, OrderLikeProtocol)

    def test_conforming_implementation(self) -> None:
        """Test that conforming implementation satisfies protocol."""
        order = MockOrder(
            id="test-order-1",
            symbol="SPY",
            qty=50,
            side="sell",
            order_type="limit",
            status="pending_new",
            filled_qty=0,
        )

        assert isinstance(order, OrderLikeProtocol)
        assert order.id == "test-order-1"
        assert order.symbol == "SPY"
        assert order.qty == 50
        assert order.side == "sell"
        assert order.order_type == "limit"
        assert order.status == "pending_new"
        assert order.filled_qty == 0

    def test_non_conforming_rejected(self) -> None:
        """Test that non-conforming implementation is rejected."""
        incomplete = IncompleteOrder()
        assert not isinstance(incomplete, OrderLikeProtocol)

    def test_optional_fields_none(self) -> None:
        """Test that optional fields can be None."""
        order = MockOrder(
            id=None,
            order_type=None,
            status=None,
            filled_qty=None,
        )

        assert isinstance(order, OrderLikeProtocol)
        assert order.id is None
        assert order.order_type is None
        assert order.status is None
        assert order.filled_qty is None

    def test_quantity_as_string(self) -> None:
        """Test that quantity can be a string (Alpaca SDK format)."""
        order = MockOrder(qty="100.5", filled_qty="50.25")

        assert isinstance(order, OrderLikeProtocol)
        assert order.qty == "100.5"
        assert order.filled_qty == "50.25"

    def test_quantity_as_float(self) -> None:
        """Test that quantity can be a float."""
        order = MockOrder(qty=100.5, filled_qty=50.25)

        assert isinstance(order, OrderLikeProtocol)
        assert order.qty == 100.5
        assert order.filled_qty == 50.25

    def test_quantity_as_int(self) -> None:
        """Test that quantity can be an int."""
        order = MockOrder(qty=100, filled_qty=50)

        assert isinstance(order, OrderLikeProtocol)
        assert order.qty == 100
        assert order.filled_qty == 50

    def test_all_required_properties_accessible(self) -> None:
        """Test that all protocol properties are accessible."""
        order = MockOrder()

        # Should not raise AttributeError
        _ = order.id
        _ = order.symbol
        _ = order.qty
        _ = order.side
        _ = order.order_type
        _ = order.status
        _ = order.filled_qty

    def test_buy_side(self) -> None:
        """Test buy side value."""
        order = MockOrder(side="buy")
        assert order.side == "buy"

    def test_sell_side(self) -> None:
        """Test sell side value."""
        order = MockOrder(side="sell")
        assert order.side == "sell"


class TestPositionLikeProtocol:
    """Test suite for PositionLikeProtocol."""

    def test_runtime_checkable(self) -> None:
        """Test that PositionLikeProtocol is runtime checkable."""
        position = MockPosition()
        assert isinstance(position, PositionLikeProtocol)

    def test_conforming_implementation(self) -> None:
        """Test that conforming implementation satisfies protocol."""
        position = MockPosition(
            symbol="TSLA",
            qty=50,
            market_value=10000.0,
            avg_entry_price=200.0,
        )

        assert isinstance(position, PositionLikeProtocol)
        assert position.symbol == "TSLA"
        assert position.qty == 50
        assert position.market_value == 10000.0
        assert position.avg_entry_price == 200.0

    def test_quantity_always_present(self) -> None:
        """Test that position quantity is always present (not None)."""
        # Position qty doesn't allow None in the type hint
        position = MockPosition(qty=100)
        assert isinstance(position, PositionLikeProtocol)
        assert position.qty == 100

    def test_optional_fields_none(self) -> None:
        """Test that market_value and avg_entry_price can be None."""
        position = MockPosition(
            market_value=None,
            avg_entry_price=None,
        )

        assert isinstance(position, PositionLikeProtocol)
        assert position.market_value is None
        assert position.avg_entry_price is None

    def test_quantity_as_string(self) -> None:
        """Test that quantity can be a string (Alpaca SDK format)."""
        position = MockPosition(qty="100.5")

        assert isinstance(position, PositionLikeProtocol)
        assert position.qty == "100.5"

    def test_quantity_as_float(self) -> None:
        """Test that quantity can be a float."""
        position = MockPosition(qty=100.5)

        assert isinstance(position, PositionLikeProtocol)
        assert position.qty == 100.5

    def test_quantity_as_int(self) -> None:
        """Test that quantity can be an int."""
        position = MockPosition(qty=100)

        assert isinstance(position, PositionLikeProtocol)
        assert position.qty == 100

    def test_monetary_fields_as_string(self) -> None:
        """Test that monetary fields can be strings (Alpaca SDK format)."""
        position = MockPosition(
            market_value="15000.50",
            avg_entry_price="150.505",
        )

        assert isinstance(position, PositionLikeProtocol)
        assert position.market_value == "15000.50"
        assert position.avg_entry_price == "150.505"

    def test_all_required_properties_accessible(self) -> None:
        """Test that all protocol properties are accessible."""
        position = MockPosition()

        # Should not raise AttributeError
        _ = position.symbol
        _ = position.qty
        _ = position.market_value
        _ = position.avg_entry_price

    def test_short_position_negative_qty(self) -> None:
        """Test that short positions can have negative quantities."""
        position = MockPosition(qty=-50)

        assert isinstance(position, PositionLikeProtocol)
        assert position.qty == -50


class TestProtocolInteroperability:
    """Test how protocols work together."""

    def test_order_and_position_are_different(self) -> None:
        """Test that order and position protocols are distinct."""
        order = MockOrder()
        position = MockPosition()

        assert isinstance(order, OrderLikeProtocol)
        assert isinstance(position, PositionLikeProtocol)
        assert not isinstance(order, PositionLikeProtocol)
        assert not isinstance(position, OrderLikeProtocol)

    def test_can_use_in_generic_functions(self) -> None:
        """Test that protocols can be used in generic functions."""

        def get_symbol(obj: OrderLikeProtocol | PositionLikeProtocol) -> str:
            """Extract symbol from order or position."""
            return obj.symbol

        order = MockOrder(symbol="AAPL")
        position = MockPosition(symbol="TSLA")

        assert get_symbol(order) == "AAPL"
        assert get_symbol(position) == "TSLA"
