"""Business Unit: shared | Status: current.

Comprehensive unit tests for enriched_data schemas.

Tests enriched order and position DTOs including immutability, validation,
serialization, and contract compliance.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.enriched_data import (
    DomainOrderData,
    EnrichedOrderView,
    EnrichedPositionsView,
    EnrichedPositionView,
    OpenOrdersView,
    OrderSummaryData,
    PositionSummaryData,
    RawOrderData,
    RawPositionData,
)


class TestEnrichedOrderView:
    """Test EnrichedOrderView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_order_view(self):
        """Test creating valid EnrichedOrderView."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        assert order.raw.id == "order123"
        assert order.raw.symbol == "AAPL"
        assert order.domain.symbol == "AAPL"
        assert order.domain.side == "buy"
        assert order.summary.status == "filled"
        assert order.summary.qty == Decimal("10")
        assert order.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_order_view_frozen(self):
        """Test EnrichedOrderView is frozen (immutable)."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        with pytest.raises((ValidationError, AttributeError)):
            order.raw = RawOrderData(id="modified", symbol="MSFT")  # type: ignore[misc]

    @pytest.mark.unit
    def test_enriched_order_view_requires_all_fields(self):
        """Test EnrichedOrderView requires raw, domain, and summary."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedOrderView(raw=RawOrderData(id="order123", symbol="AAPL"))  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "domain" in missing_fields
        assert "summary" in missing_fields

    @pytest.mark.unit
    def test_enriched_order_view_strict_validation(self):
        """Test EnrichedOrderView strict mode rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedOrderView(
                raw=RawOrderData(id="order123", symbol="AAPL"),
                domain=DomainOrderData(symbol="AAPL", side="buy"),
                summary=OrderSummaryData(status="filled", qty=Decimal("10")),
                extra_field="not_allowed",  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    @pytest.mark.unit
    def test_enriched_order_view_serialization(self):
        """Test EnrichedOrderView serialization to dict."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        serialized = order.model_dump()
        assert serialized["schema_version"] == "1.0"
        assert serialized["raw"]["id"] == "order123"
        assert serialized["domain"]["symbol"] == "AAPL"
        assert serialized["summary"]["status"] == "filled"

    @pytest.mark.unit
    def test_enriched_order_view_json_serialization(self):
        """Test EnrichedOrderView JSON serialization."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        json_str = order.model_dump_json()
        assert "order123" in json_str
        assert "AAPL" in json_str
        assert "filled" in json_str
        assert "1.0" in json_str

    @pytest.mark.unit
    def test_enriched_order_view_decimal_precision(self):
        """Test EnrichedOrderView maintains Decimal precision."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10.123456")),
        )

        assert isinstance(order.summary.qty, Decimal)
        assert order.summary.qty == Decimal("10.123456")


class TestOpenOrdersView:
    """Test OpenOrdersView DTO."""

    @pytest.mark.unit
    def test_valid_open_orders_view(self):
        """Test creating valid OpenOrdersView."""
        order1 = EnrichedOrderView(
            raw=RawOrderData(id="order1", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="open", qty=Decimal("10")),
        )
        order2 = EnrichedOrderView(
            raw=RawOrderData(id="order2", symbol="MSFT"),
            domain=DomainOrderData(symbol="MSFT", side="sell"),
            summary=OrderSummaryData(status="open", qty=Decimal("5")),
        )

        response = OpenOrdersView(
            success=True,
            orders=[order1, order2],
            symbol_filter="AAPL",
        )

        assert response.success is True
        assert len(response.orders) == 2
        assert response.symbol_filter == "AAPL"
        assert response.schema_version == "1.0"

    @pytest.mark.unit
    def test_open_orders_view_no_symbol_filter(self):
        """Test OpenOrdersView without symbol filter."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order1", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="open", qty=Decimal("10")),
        )

        response = OpenOrdersView(
            success=True,
            orders=[order],
        )

        assert response.symbol_filter is None

    @pytest.mark.unit
    def test_open_orders_view_empty_orders_list(self):
        """Test OpenOrdersView with empty orders list."""
        response = OpenOrdersView(
            success=True,
            orders=[],
        )

        assert len(response.orders) == 0
        assert response.success is True

    @pytest.mark.unit
    def test_open_orders_view_frozen(self):
        """Test OpenOrdersView is frozen (immutable)."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order1", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="open", qty=Decimal("10")),
        )

        response = OpenOrdersView(
            success=True,
            orders=[order],
        )

        with pytest.raises((ValidationError, AttributeError)):
            response.success = False  # type: ignore[misc]

    @pytest.mark.unit
    def test_open_orders_view_inherits_from_result(self):
        """Test OpenOrdersView inherits success/error from Result."""
        response = OpenOrdersView(
            success=False,
            error="API error",
            orders=[],
        )

        assert response.success is False
        assert response.error == "API error"
        assert response.is_success is False

    @pytest.mark.unit
    def test_open_orders_view_requires_success_field(self):
        """Test OpenOrdersView requires success field from Result."""
        with pytest.raises(ValidationError) as exc_info:
            OpenOrdersView(orders=[])  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "success" in missing_fields

    @pytest.mark.unit
    def test_open_orders_view_symbol_filter_max_length(self):
        """Test OpenOrdersView symbol_filter respects max_length constraint."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order1", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="open", qty=Decimal("10")),
        )

        # Valid length
        response = OpenOrdersView(
            success=True,
            orders=[order],
            symbol_filter="AAPL",
        )
        assert response.symbol_filter == "AAPL"

        # Too long - should fail
        with pytest.raises(ValidationError):
            OpenOrdersView(
                success=True,
                orders=[order],
                symbol_filter="VERYLONGSYMBOL",  # More than 10 chars
            )


class TestEnrichedPositionView:
    """Test EnrichedPositionView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_position_view(self):
        """Test creating valid EnrichedPositionView."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )

        assert position.raw.symbol == "AAPL"
        assert position.raw.qty == Decimal("100")
        assert position.summary.symbol == "AAPL"
        assert position.summary.unrealized_pl == Decimal("500.00")
        assert position.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_position_view_frozen(self):
        """Test EnrichedPositionView is frozen (immutable)."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )

        with pytest.raises((ValidationError, AttributeError)):
            position.raw = RawPositionData(symbol="MSFT", qty=Decimal("50"))  # type: ignore[misc]

    @pytest.mark.unit
    def test_enriched_position_view_requires_all_fields(self):
        """Test EnrichedPositionView requires raw and summary."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPositionView(raw=RawPositionData(symbol="AAPL", qty=Decimal("100")))  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "summary" in missing_fields

    @pytest.mark.unit
    def test_enriched_position_view_strict_validation(self):
        """Test EnrichedPositionView strict mode rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPositionView(
                raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
                summary=PositionSummaryData(
                    symbol="AAPL",
                    qty=Decimal("100"),
                    market_value=Decimal("15000.00"),
                    unrealized_pl=Decimal("500.00"),
                ),
                extra_field="not_allowed",  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    @pytest.mark.unit
    def test_enriched_position_view_serialization(self):
        """Test EnrichedPositionView serialization to dict."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )

        serialized = position.model_dump()
        assert serialized["schema_version"] == "1.0"
        assert serialized["raw"]["symbol"] == "AAPL"
        assert serialized["summary"]["unrealized_pl"] == Decimal("500.00")

    @pytest.mark.unit
    def test_enriched_position_view_decimal_precision(self):
        """Test EnrichedPositionView maintains Decimal precision for financial values."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100.5")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100.5"),
                market_value=Decimal("15075.25"),
                unrealized_pl=Decimal("537.83"),
            ),
        )

        assert isinstance(position.summary.market_value, Decimal)
        assert isinstance(position.summary.unrealized_pl, Decimal)
        assert position.summary.market_value == Decimal("15075.25")
        assert position.summary.unrealized_pl == Decimal("537.83")


class TestEnrichedPositionsView:
    """Test EnrichedPositionsView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_positions_view(self):
        """Test creating valid EnrichedPositionsView."""
        position1 = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )
        position2 = EnrichedPositionView(
            raw=RawPositionData(symbol="MSFT", qty=Decimal("50")),
            summary=PositionSummaryData(
                symbol="MSFT",
                qty=Decimal("50"),
                market_value=Decimal("20000.00"),
                unrealized_pl=Decimal("-100.00"),
            ),
        )

        response = EnrichedPositionsView(
            success=True,
            positions=[position1, position2],
        )

        assert response.success is True
        assert len(response.positions) == 2
        assert response.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_positions_view_empty_list(self):
        """Test EnrichedPositionsView with empty positions list."""
        response = EnrichedPositionsView(
            success=True,
            positions=[],
        )

        assert len(response.positions) == 0
        assert response.success is True

    @pytest.mark.unit
    def test_enriched_positions_view_frozen(self):
        """Test EnrichedPositionsView is frozen (immutable)."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )

        response = EnrichedPositionsView(
            success=True,
            positions=[position],
        )

        with pytest.raises((ValidationError, AttributeError)):
            response.success = False  # type: ignore[misc]

    @pytest.mark.unit
    def test_enriched_positions_view_inherits_from_result(self):
        """Test EnrichedPositionsView inherits success/error from Result."""
        response = EnrichedPositionsView(
            success=False,
            error="Market closed",
            positions=[],
        )

        assert response.success is False
        assert response.error == "Market closed"
        assert response.is_success is False


class TestBackwardCompatibilityAliases:
    """Test backward compatibility aliases."""

    @pytest.mark.unit
    def test_enriched_order_dto_alias_exists(self):
        """Test EnrichedOrderDTO alias exists."""
        from the_alchemiser.shared.schemas.enriched_data import EnrichedOrderDTO

        assert EnrichedOrderDTO is EnrichedOrderView

    @pytest.mark.unit
    def test_open_orders_dto_alias_exists(self):
        """Test OpenOrdersDTO alias exists."""
        from the_alchemiser.shared.schemas.enriched_data import OpenOrdersDTO

        assert OpenOrdersDTO is OpenOrdersView

    @pytest.mark.unit
    def test_enriched_position_dto_alias_exists(self):
        """Test EnrichedPositionDTO alias exists."""
        from the_alchemiser.shared.schemas.enriched_data import EnrichedPositionDTO

        assert EnrichedPositionDTO is EnrichedPositionView

    @pytest.mark.unit
    def test_enriched_positions_dto_alias_exists(self):
        """Test EnrichedPositionsDTO alias exists."""
        from the_alchemiser.shared.schemas.enriched_data import EnrichedPositionsDTO

        assert EnrichedPositionsDTO is EnrichedPositionsView

    @pytest.mark.unit
    def test_alias_creates_same_instance(self):
        """Test that alias creates equivalent instance."""
        from the_alchemiser.shared.schemas.enriched_data import (
            EnrichedOrderDTO,
            EnrichedOrderView,
        )

        order_view = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        order_dto = EnrichedOrderDTO(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        assert order_view.model_dump() == order_dto.model_dump()
        assert type(order_view) is type(order_dto)


class TestImmutability:
    """Test immutability of all DTOs."""

    @pytest.mark.unit
    def test_all_dtos_have_frozen_config(self):
        """Test all DTOs have frozen=True in model_config."""
        assert EnrichedOrderView.model_config["frozen"] is True
        assert OpenOrdersView.model_config["frozen"] is True
        assert EnrichedPositionView.model_config["frozen"] is True
        assert EnrichedPositionsView.model_config["frozen"] is True

    @pytest.mark.unit
    def test_all_dtos_have_strict_config(self):
        """Test all DTOs have strict=True in model_config."""
        assert EnrichedOrderView.model_config["strict"] is True
        assert OpenOrdersView.model_config["strict"] is True
        assert EnrichedPositionView.model_config["strict"] is True
        assert EnrichedPositionsView.model_config["strict"] is True

    @pytest.mark.unit
    def test_all_dtos_have_validate_assignment_config(self):
        """Test all DTOs have validate_assignment=True in model_config."""
        assert EnrichedOrderView.model_config["validate_assignment"] is True
        assert OpenOrdersView.model_config["validate_assignment"] is True
        assert EnrichedPositionView.model_config["validate_assignment"] is True
        assert EnrichedPositionsView.model_config["validate_assignment"] is True


class TestSchemaVersioning:
    """Test schema versioning for all DTOs."""

    @pytest.mark.unit
    def test_enriched_order_view_has_schema_version(self):
        """Test EnrichedOrderView includes schema_version."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        assert hasattr(order, "schema_version")
        assert order.schema_version == "1.0"

    @pytest.mark.unit
    def test_open_orders_view_has_schema_version(self):
        """Test OpenOrdersView includes schema_version."""
        response = OpenOrdersView(success=True, orders=[])

        assert hasattr(response, "schema_version")
        assert response.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_position_view_has_schema_version(self):
        """Test EnrichedPositionView includes schema_version."""
        position = EnrichedPositionView(
            raw=RawPositionData(symbol="AAPL", qty=Decimal("100")),
            summary=PositionSummaryData(
                symbol="AAPL",
                qty=Decimal("100"),
                market_value=Decimal("15000.00"),
                unrealized_pl=Decimal("500.00"),
            ),
        )

        assert hasattr(position, "schema_version")
        assert position.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_positions_view_has_schema_version(self):
        """Test EnrichedPositionsView includes schema_version."""
        response = EnrichedPositionsView(success=True, positions=[])

        assert hasattr(response, "schema_version")
        assert response.schema_version == "1.0"

    @pytest.mark.unit
    def test_schema_version_serialized(self):
        """Test schema_version is included in serialized output."""
        order = EnrichedOrderView(
            raw=RawOrderData(id="order123", symbol="AAPL"),
            domain=DomainOrderData(symbol="AAPL", side="buy"),
            summary=OrderSummaryData(status="filled", qty=Decimal("10")),
        )

        serialized = order.model_dump()
        assert "schema_version" in serialized
        assert serialized["schema_version"] == "1.0"

        json_str = order.model_dump_json()
        assert '"schema_version":"1.0"' in json_str or '"schema_version": "1.0"' in json_str
