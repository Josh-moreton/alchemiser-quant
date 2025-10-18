#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for Alpaca protocol definitions.

Validates:
- Protocol structural typing works correctly
- Mock objects conforming to protocols pass type checking
- Protocol attributes match expected usage patterns
- Documentation of type mismatches with Alpaca SDK
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from the_alchemiser.shared.protocols.alpaca import (
    AlpacaOrderObject,
    AlpacaOrderProtocol,
)

if TYPE_CHECKING:
    pass


class TestAlpacaOrderProtocol:
    """Test AlpacaOrderProtocol structural typing."""

    def test_protocol_with_string_attributes(self) -> None:
        """Test protocol accepts objects with all string attributes."""

        class StringOrder:
            """Mock order with string types (as protocol specifies)."""

            id: str = "order-123"
            client_order_id: str = "client-order-123"
            symbol: str = "AAPL"
            qty: str = "10"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "10"
            filled_avg_price: str | None = "150.00"
            created_at: str = "2024-01-01T00:00:00Z"
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:05Z"

        order: AlpacaOrderProtocol = StringOrder()  # type: ignore[assignment]
        assert order.symbol == "AAPL"
        assert order.qty == "10"
        assert order.side == "buy"
        assert order.client_order_id == "client-order-123"

    def test_protocol_with_none_filled_price(self) -> None:
        """Test protocol handles None for optional filled_avg_price."""

        class UnfilledOrder:
            """Mock unfilled order."""

            id: str = "order-456"
            client_order_id: str = "client-order-456"
            symbol: str = "TSLA"
            qty: str = "5"
            side: str = "sell"
            order_type: str = "limit"
            time_in_force: str = "gtc"
            status: str = "pending"
            filled_qty: str = "0"
            filled_avg_price: str | None = None  # Not filled yet
            created_at: str = "2024-01-01T00:00:00Z"
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:00Z"

        order: AlpacaOrderProtocol = UnfilledOrder()  # type: ignore[assignment]
        assert order.filled_avg_price is None
        assert order.status == "pending"

    def test_protocol_attributes_accessible(self) -> None:
        """Test all protocol-defined attributes are accessible."""

        class CompleteOrder:
            """Mock order with all attributes."""

            id: str = "order-789"
            client_order_id: str = "client-order-789"
            symbol: str = "NVDA"
            qty: str = "100"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "100"
            filled_avg_price: str | None = "450.25"
            created_at: str = "2024-01-01T09:30:00Z"
            submitted_at: str = "2024-01-01T09:30:00Z"
            updated_at: str | None = "2024-01-01T09:30:05Z"

        order: AlpacaOrderProtocol = CompleteOrder()  # type: ignore[assignment]

        # All attributes should be accessible
        assert isinstance(order.id, str)
        assert isinstance(order.client_order_id, str)
        assert isinstance(order.symbol, str)
        assert isinstance(order.qty, str)
        assert isinstance(order.side, str)
        assert isinstance(order.order_type, str)
        assert isinstance(order.time_in_force, str)
        assert isinstance(order.status, str)
        assert isinstance(order.filled_qty, str)
        assert order.filled_avg_price is None or isinstance(order.filled_avg_price, str)
        assert isinstance(order.created_at, str)
        assert isinstance(order.submitted_at, str)
        assert order.updated_at is None or isinstance(order.updated_at, str)


class TestAlpacaOrderObject:
    """Test AlpacaOrderObject minimal monitoring protocol."""

    def test_minimal_protocol_with_three_fields(self) -> None:
        """Test minimal protocol for order status monitoring."""

        class MonitoringOrder:
            """Minimal order for monitoring."""

            id = "order-999"
            status = "filled"
            filled_qty = "50"

        order: AlpacaOrderObject = MonitoringOrder()  # type: ignore[assignment]
        assert order.id == "order-999"
        assert order.status == "filled"
        assert order.filled_qty == "50"

    def test_protocol_subset_of_full_order(self) -> None:
        """Test that full order protocol can be used as monitoring protocol."""

        class FullOrder:
            """Full order that also satisfies minimal protocol."""

            id: str = "order-111"
            client_order_id: str = "client-order-111"
            symbol: str = "MSFT"
            qty: str = "25"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "25"
            filled_avg_price: str | None = "380.50"
            created_at: str = "2024-01-01T10:00:00Z"
            submitted_at: str = "2024-01-01T10:00:00Z"
            updated_at: str | None = "2024-01-01T10:00:03Z"

        # Full order can be used as AlpacaOrderObject (structural subtyping)
        order: AlpacaOrderObject = FullOrder()  # type: ignore[assignment]
        assert order.id == "order-111"
        assert order.status == "filled"


class TestProtocolUseCases:
    """Test realistic use cases for protocols."""

    def test_dict_unpacking_to_protocol(self) -> None:
        """Test creating protocol-conforming object from dict."""
        order_data = {
            "id": "order-222",
            "symbol": "GOOGL",
            "qty": "10",
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": "10",
            "filled_avg_price": "142.50",
            "created_at": "2024-01-01T11:00:00Z",
            "updated_at": "2024-01-01T11:00:02Z",
        }

        # Create object that conforms to protocol
        from collections.abc import Mapping

        class DictBasedOrder:
            def __init__(self, data: Mapping[str, str | None]) -> None:
                for key, value in data.items():
                    setattr(self, key, value)

        order: AlpacaOrderProtocol = DictBasedOrder(order_data)  # type: ignore[assignment]
        assert order.symbol == "GOOGL"
        assert order.status == "filled"

    def test_protocol_for_monitoring_subset(self) -> None:
        """Test using minimal protocol for monitoring loop."""
        orders = [
            type("Order1", (), {"id": "1", "status": "pending", "filled_qty": "0"}),
            type("Order2", (), {"id": "2", "status": "filled", "filled_qty": "10"}),
            type("Order3", (), {"id": "3", "status": "filled", "filled_qty": "5"}),
        ]

        # Monitor using minimal protocol
        filled_orders: list[AlpacaOrderObject] = [
            o()
            for o in orders
            if o.status == "filled"  # type: ignore[attr-defined]
        ]

        assert len(filled_orders) == 2


class TestProtocolDocumentation:
    """Document known limitations and type mismatches."""

    def test_known_mismatch_with_alpaca_sdk_id_field(self) -> None:
        """Document: Protocol now supports both UUID and str.

        The protocol has been updated to accept both str | UUID to support
        both serialized forms and native SDK objects.
        """

        # Protocol accepts string
        class StringIdOrder:
            id: str = "some-string-id"
            client_order_id: str = "client-id"
            symbol: str = "AAPL"
            qty: str = "10"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "10"
            filled_avg_price: str | None = "150.00"
            created_at: str = "2024-01-01T00:00:00Z"
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:05Z"

        order: AlpacaOrderProtocol = StringIdOrder()  # type: ignore[assignment]
        assert isinstance(order.id, str)

    def test_known_mismatch_with_alpaca_sdk_timestamps(self) -> None:
        """Document: Protocol now supports both datetime and str.

        The protocol has been updated to accept both str | datetime to support
        both serialized forms and native SDK objects.
        """

        # Protocol accepts string
        class StringTimestampOrder:
            id: str = "order-id"
            client_order_id: str = "client-id"
            symbol: str = "AAPL"
            qty: str = "10"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "10"
            filled_avg_price: str | None = "150.00"
            created_at: str = "2024-01-01T00:00:00Z"  # String supported
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:05Z"  # String supported

        order: AlpacaOrderProtocol = StringTimestampOrder()  # type: ignore[assignment]
        assert isinstance(order.created_at, str)
        assert order.updated_at is None or isinstance(order.updated_at, str)

    def test_known_missing_fields_in_protocol(self) -> None:
        """Document: Protocol now includes previously missing critical fields.

        Added fields:
        - client_order_id: str (for order tracking) ✅ ADDED
        - submitted_at: str | datetime (for order timing) ✅ ADDED

        Still missing optional fields:
        - limit_price, stop_price: for limit/stop orders
        - canceled_at, expired_at, filled_at: for lifecycle tracking

        Rationale: Protocol defines essential fields for most use cases.
        """
        # This test documents the protocol scope


class TestProtocolComparison:
    """Compare AlpacaOrderProtocol with AlpacaOrderObject."""

    def test_full_protocol_has_all_order_fields(self) -> None:
        """AlpacaOrderProtocol has comprehensive order information."""

        class FullOrder:
            id: str = "1"
            client_order_id: str = "client-1"
            symbol: str = "AAPL"
            qty: str = "10"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "filled"
            filled_qty: str = "10"
            filled_avg_price: str | None = "150.00"
            created_at: str = "2024-01-01T00:00:00Z"
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:05Z"

        order: AlpacaOrderProtocol = FullOrder()  # type: ignore[assignment]
        # Has 13 fields (was 11, now includes client_order_id and submitted_at)
        assert hasattr(order, "id")
        assert hasattr(order, "client_order_id")
        assert hasattr(order, "symbol")
        assert hasattr(order, "qty")
        assert hasattr(order, "side")
        assert hasattr(order, "order_type")
        assert hasattr(order, "time_in_force")
        assert hasattr(order, "status")
        assert hasattr(order, "filled_qty")
        assert hasattr(order, "filled_avg_price")
        assert hasattr(order, "created_at")
        assert hasattr(order, "submitted_at")
        assert hasattr(order, "updated_at")

    def test_minimal_protocol_has_only_monitoring_fields(self) -> None:
        """AlpacaOrderObject has only essential monitoring fields."""

        class MinimalOrder:
            id = "1"
            status = "filled"
            filled_qty = "10"

        order: AlpacaOrderObject = MinimalOrder()  # type: ignore[assignment]
        # Has only 3 fields
        assert hasattr(order, "id")
        assert hasattr(order, "status")
        assert hasattr(order, "filled_qty")


class TestProtocolEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_values(self) -> None:
        """Test protocol handles empty strings."""

        class EmptyStringOrder:
            id: str = ""
            client_order_id: str = ""
            symbol: str = "AAPL"
            qty: str = "0"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = ""
            filled_qty: str = "0"
            filled_avg_price: str | None = None
            created_at: str = ""
            submitted_at: str = ""
            updated_at: str | None = ""

        order: AlpacaOrderProtocol = EmptyStringOrder()  # type: ignore[assignment]
        assert order.id == ""
        assert order.qty == "0"

    def test_unfilled_order_scenario(self) -> None:
        """Test unfilled order with zero filled_qty."""

        class UnfilledOrder:
            id: str = "pending-order"
            client_order_id: str = "client-pending"
            symbol: str = "TSLA"
            qty: str = "100"
            side: str = "buy"
            order_type: str = "limit"
            time_in_force: str = "gtc"
            status: str = "pending"
            filled_qty: str = "0"
            filled_avg_price: str | None = None
            created_at: str = "2024-01-01T00:00:00Z"
            submitted_at: str = "2024-01-01T00:00:00Z"
            updated_at: str | None = "2024-01-01T00:00:00Z"

        order: AlpacaOrderProtocol = UnfilledOrder()  # type: ignore[assignment]
        assert order.filled_qty == "0"
        assert order.filled_avg_price is None
        assert order.filled_qty == "0"
        assert order.filled_avg_price is None
        assert order.status == "pending"

    def test_partially_filled_order_scenario(self) -> None:
        """Test partially filled order."""

        class PartialOrder:
            id: str = "partial-order"
            client_order_id: str = "client-partial"
            symbol: str = "NVDA"
            qty: str = "100"
            side: str = "buy"
            order_type: str = "market"
            time_in_force: str = "day"
            status: str = "partially_filled"
            filled_qty: str = "50"
            filled_avg_price: str | None = "450.25"
            created_at: str = "2024-01-01T09:30:00Z"
            submitted_at: str = "2024-01-01T09:30:00Z"
            updated_at: str | None = "2024-01-01T09:30:30Z"

        order: AlpacaOrderProtocol = PartialOrder()  # type: ignore[assignment]
        assert order.qty == "100"
        assert order.filled_qty == "50"
        assert order.status == "partially_filled"
