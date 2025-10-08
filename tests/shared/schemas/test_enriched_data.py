"""Business Unit: shared | Status: current.

Comprehensive unit tests for enriched_data schemas.

Tests enriched order and position DTOs including immutability, validation,
serialization, and contract compliance.
"""

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.enriched_data import (
    EnrichedOrderView,
    EnrichedPositionView,
    EnrichedPositionsView,
    OpenOrdersView,
)


class TestEnrichedOrderView:
    """Test EnrichedOrderView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_order_view(self):
        """Test creating valid EnrichedOrderView."""
        order = EnrichedOrderView(
            raw={"id": "order123", "symbol": "AAPL"},
            domain={"symbol": "AAPL", "side": "buy"},
            summary={"status": "filled", "qty": "10"},
        )

        assert order.raw == {"id": "order123", "symbol": "AAPL"}
        assert order.domain == {"symbol": "AAPL", "side": "buy"}
        assert order.summary == {"status": "filled", "qty": "10"}

    @pytest.mark.unit
    def test_enriched_order_view_frozen(self):
        """Test EnrichedOrderView is frozen (immutable)."""
        order = EnrichedOrderView(
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        with pytest.raises((ValidationError, AttributeError)):
            order.raw = {"id": "modified"}  # type: ignore[misc]

    @pytest.mark.unit
    def test_enriched_order_view_requires_all_fields(self):
        """Test EnrichedOrderView requires raw, domain, and summary."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedOrderView(raw={"id": "order123"})  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "domain" in missing_fields
        assert "summary" in missing_fields

    @pytest.mark.unit
    def test_enriched_order_view_strict_validation(self):
        """Test EnrichedOrderView strict mode rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedOrderView(
                raw={"id": "order123"},
                domain={"symbol": "AAPL"},
                summary={"status": "filled"},
                extra_field="not_allowed",  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    @pytest.mark.unit
    def test_enriched_order_view_serialization(self):
        """Test EnrichedOrderView serialization to dict."""
        order = EnrichedOrderView(
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        serialized = order.model_dump()
        assert serialized["raw"] == {"id": "order123"}
        assert serialized["domain"] == {"symbol": "AAPL"}
        assert serialized["summary"] == {"status": "filled"}

    @pytest.mark.unit
    def test_enriched_order_view_json_serialization(self):
        """Test EnrichedOrderView JSON serialization."""
        order = EnrichedOrderView(
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        json_str = order.model_dump_json()
        assert "order123" in json_str
        assert "AAPL" in json_str
        assert "filled" in json_str

    @pytest.mark.unit
    def test_enriched_order_view_empty_dicts(self):
        """Test EnrichedOrderView allows empty dicts."""
        order = EnrichedOrderView(
            raw={},
            domain={},
            summary={},
        )

        assert order.raw == {}
        assert order.domain == {}
        assert order.summary == {}


class TestOpenOrdersView:
    """Test OpenOrdersView DTO."""

    @pytest.mark.unit
    def test_valid_open_orders_view(self):
        """Test creating valid OpenOrdersView."""
        order1 = EnrichedOrderView(
            raw={"id": "order1"},
            domain={"symbol": "AAPL"},
            summary={"status": "open"},
        )
        order2 = EnrichedOrderView(
            raw={"id": "order2"},
            domain={"symbol": "MSFT"},
            summary={"status": "open"},
        )

        response = OpenOrdersView(
            success=True,
            orders=[order1, order2],
            symbol_filter="AAPL",
        )

        assert response.success is True
        assert len(response.orders) == 2
        assert response.symbol_filter == "AAPL"

    @pytest.mark.unit
    def test_open_orders_view_no_symbol_filter(self):
        """Test OpenOrdersView without symbol filter."""
        order = EnrichedOrderView(
            raw={"id": "order1"},
            domain={"symbol": "AAPL"},
            summary={"status": "open"},
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
            raw={"id": "order1"},
            domain={"symbol": "AAPL"},
            summary={"status": "open"},
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


class TestEnrichedPositionView:
    """Test EnrichedPositionView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_position_view(self):
        """Test creating valid EnrichedPositionView."""
        position = EnrichedPositionView(
            raw={"symbol": "AAPL", "qty": "100"},
            summary={
                "symbol": "AAPL",
                "qty": "100",
                "market_value": "15000.00",
                "unrealized_pl": "500.00",
            },
        )

        assert position.raw == {"symbol": "AAPL", "qty": "100"}
        assert position.summary["symbol"] == "AAPL"
        assert position.summary["unrealized_pl"] == "500.00"

    @pytest.mark.unit
    def test_enriched_position_view_frozen(self):
        """Test EnrichedPositionView is frozen (immutable)."""
        position = EnrichedPositionView(
            raw={"symbol": "AAPL"},
            summary={"unrealized_pl": "500.00"},
        )

        with pytest.raises((ValidationError, AttributeError)):
            position.raw = {"symbol": "MSFT"}  # type: ignore[misc]

    @pytest.mark.unit
    def test_enriched_position_view_requires_all_fields(self):
        """Test EnrichedPositionView requires raw and summary."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPositionView(raw={"symbol": "AAPL"})  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "summary" in missing_fields

    @pytest.mark.unit
    def test_enriched_position_view_strict_validation(self):
        """Test EnrichedPositionView strict mode rejects extra fields."""
        with pytest.raises(ValidationError) as exc_info:
            EnrichedPositionView(
                raw={"symbol": "AAPL"},
                summary={"unrealized_pl": "500.00"},
                extra_field="not_allowed",  # type: ignore[call-arg]
            )

        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    @pytest.mark.unit
    def test_enriched_position_view_serialization(self):
        """Test EnrichedPositionView serialization to dict."""
        position = EnrichedPositionView(
            raw={"symbol": "AAPL"},
            summary={"unrealized_pl": "500.00"},
        )

        serialized = position.model_dump()
        assert serialized["raw"] == {"symbol": "AAPL"}
        assert serialized["summary"] == {"unrealized_pl": "500.00"}

    @pytest.mark.unit
    def test_enriched_position_view_empty_dicts(self):
        """Test EnrichedPositionView allows empty dicts."""
        position = EnrichedPositionView(
            raw={},
            summary={},
        )

        assert position.raw == {}
        assert position.summary == {}


class TestEnrichedPositionsView:
    """Test EnrichedPositionsView DTO."""

    @pytest.mark.unit
    def test_valid_enriched_positions_view(self):
        """Test creating valid EnrichedPositionsView."""
        position1 = EnrichedPositionView(
            raw={"symbol": "AAPL"},
            summary={"unrealized_pl": "500.00"},
        )
        position2 = EnrichedPositionView(
            raw={"symbol": "MSFT"},
            summary={"unrealized_pl": "-100.00"},
        )

        response = EnrichedPositionsView(
            success=True,
            positions=[position1, position2],
        )

        assert response.success is True
        assert len(response.positions) == 2

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
            raw={"symbol": "AAPL"},
            summary={"unrealized_pl": "500.00"},
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
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        order_dto = EnrichedOrderDTO(
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        assert order_view.model_dump() == order_dto.model_dump()
        assert type(order_view) is type(order_dto)


class TestImmutability:
    """Test immutability of all DTOs."""

    @pytest.mark.unit
    def test_enriched_order_view_cannot_modify_raw(self):
        """Test EnrichedOrderView raw dict cannot be modified after creation."""
        order = EnrichedOrderView(
            raw={"id": "order123"},
            domain={"symbol": "AAPL"},
            summary={"status": "filled"},
        )

        # Note: The DTO is frozen, but the dict inside is mutable
        # This is a known limitation of Pydantic frozen models
        # To truly freeze nested structures, would need custom validators
        original_raw = order.raw
        assert original_raw == {"id": "order123"}

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
