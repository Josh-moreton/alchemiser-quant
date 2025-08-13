"""Test the PositionDelta value object."""

from decimal import Decimal

import pytest

from the_alchemiser.domain.portfolio.position.position_delta import PositionDelta


class TestPositionDelta:
    """Test cases for PositionDelta value object."""

    def test_position_delta_creation_no_change(self):
        """Test PositionDelta creation for no change scenario."""
        delta = PositionDelta(
            symbol="AAPL",
            current_qty=Decimal("100.0"),
            target_qty=Decimal("100.0"),
            delta=Decimal("0.0"),
            action="no_change",
            quantity=Decimal("0.0"),
            message="No rebalancing needed for AAPL: 100.0 ≈ 100.0"
        )

        assert delta.symbol == "AAPL"
        assert delta.current_qty == Decimal("100.0")
        assert delta.target_qty == Decimal("100.0")
        assert delta.delta == Decimal("0.0")
        assert delta.action == "no_change"
        assert delta.quantity == Decimal("0.0")
        assert "No rebalancing needed" in delta.message

    def test_position_delta_creation_sell_excess(self):
        """Test PositionDelta creation for sell excess scenario."""
        delta = PositionDelta(
            symbol="MSFT",
            current_qty=Decimal("150.0"),
            target_qty=Decimal("100.0"),
            delta=Decimal("-50.0"),
            action="sell_excess",
            quantity=Decimal("50.0"),
            message="Rebalancing MSFT: selling 50.0 shares"
        )

        assert delta.symbol == "MSFT"
        assert delta.current_qty == Decimal("150.0")
        assert delta.target_qty == Decimal("100.0")
        assert delta.delta == Decimal("-50.0")
        assert delta.action == "sell_excess"
        assert delta.quantity == Decimal("50.0")
        assert "selling" in delta.message

    def test_position_delta_creation_buy_more(self):
        """Test PositionDelta creation for buy more scenario."""
        delta = PositionDelta(
            symbol="GOOGL",
            current_qty=Decimal("50.0"),
            target_qty=Decimal("100.0"),
            delta=Decimal("50.0"),
            action="buy_more",
            quantity=Decimal("50.0"),
            message="Rebalancing GOOGL: buying 50.0 shares"
        )

        assert delta.symbol == "GOOGL"
        assert delta.current_qty == Decimal("50.0")
        assert delta.target_qty == Decimal("100.0")
        assert delta.delta == Decimal("50.0")
        assert delta.action == "buy_more"
        assert delta.quantity == Decimal("50.0")
        assert "buying" in delta.message

    def test_needs_action_property(self):
        """Test needs_action property."""
        # No change scenario
        no_change_delta = PositionDelta(
            symbol="AAPL", current_qty=Decimal("100"), target_qty=Decimal("100"),
            delta=Decimal("0"), action="no_change", quantity=Decimal("0"), message=""
        )
        assert not no_change_delta.needs_action

        # Sell scenario
        sell_delta = PositionDelta(
            symbol="MSFT", current_qty=Decimal("150"), target_qty=Decimal("100"),
            delta=Decimal("-50"), action="sell_excess", quantity=Decimal("50"), message=""
        )
        assert sell_delta.needs_action

        # Buy scenario
        buy_delta = PositionDelta(
            symbol="GOOGL", current_qty=Decimal("50"), target_qty=Decimal("100"),
            delta=Decimal("50"), action="buy_more", quantity=Decimal("50"), message=""
        )
        assert buy_delta.needs_action

    def test_is_buy_property(self):
        """Test is_buy property."""
        buy_delta = PositionDelta(
            symbol="GOOGL", current_qty=Decimal("50"), target_qty=Decimal("100"),
            delta=Decimal("50"), action="buy_more", quantity=Decimal("50"), message=""
        )
        assert buy_delta.is_buy

        sell_delta = PositionDelta(
            symbol="MSFT", current_qty=Decimal("150"), target_qty=Decimal("100"),
            delta=Decimal("-50"), action="sell_excess", quantity=Decimal("50"), message=""
        )
        assert not sell_delta.is_buy

    def test_is_sell_property(self):
        """Test is_sell property."""
        sell_delta = PositionDelta(
            symbol="MSFT", current_qty=Decimal("150"), target_qty=Decimal("100"),
            delta=Decimal("-50"), action="sell_excess", quantity=Decimal("50"), message=""
        )
        assert sell_delta.is_sell

        buy_delta = PositionDelta(
            symbol="GOOGL", current_qty=Decimal("50"), target_qty=Decimal("100"),
            delta=Decimal("50"), action="buy_more", quantity=Decimal("50"), message=""
        )
        assert not buy_delta.is_sell

    def test_quantity_abs_property(self):
        """Test quantity_abs property."""
        # Positive quantity
        buy_delta = PositionDelta(
            symbol="GOOGL", current_qty=Decimal("50"), target_qty=Decimal("100"),
            delta=Decimal("50"), action="buy_more", quantity=Decimal("50"), message=""
        )
        assert buy_delta.quantity_abs == Decimal("50")

        # Already positive quantity for sell
        sell_delta = PositionDelta(
            symbol="MSFT", current_qty=Decimal("150"), target_qty=Decimal("100"),
            delta=Decimal("-50"), action="sell_excess", quantity=Decimal("50"), message=""
        )
        assert sell_delta.quantity_abs == Decimal("50")

    def test_string_representation(self):
        """Test string representation."""
        delta = PositionDelta(
            symbol="AAPL",
            current_qty=Decimal("100.0"),
            target_qty=Decimal("150.0"),
            delta=Decimal("50.0"),
            action="buy_more",
            quantity=Decimal("50.0"),
            message="Need to buy 50 more shares"
        )

        assert str(delta) == "Need to buy 50 more shares"

    def test_immutability(self):
        """Test that PositionDelta is immutable."""
        delta = PositionDelta(
            symbol="AAPL", current_qty=Decimal("100"), target_qty=Decimal("150"),
            delta=Decimal("50"), action="buy_more", quantity=Decimal("50"), message=""
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            delta.symbol = "MSFT"
