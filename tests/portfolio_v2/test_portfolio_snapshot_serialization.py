"""Business Unit: portfolio | Status: current

Test portfolio snapshot serialization and deserialization.

Tests the serialization (to_dict) and deserialization (from_dict) methods
for PortfolioSnapshot to ensure proper conversion between Decimal and string.
"""

import pytest
from decimal import Decimal

from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot


class TestPortfolioSnapshotSerialization:
    """Test PortfolioSnapshot serialization to dictionary."""

    def test_to_dict_converts_decimals_to_strings(self):
        """Test that to_dict converts all Decimal values to strings."""
        snapshot = PortfolioSnapshot(
            positions={"AAPL": Decimal("100"), "MSFT": Decimal("50.5")},
            prices={"AAPL": Decimal("150.00"), "MSFT": Decimal("300.25")},
            cash=Decimal("5000.00"),
            total_value=Decimal("25012.50"),
        )

        data = snapshot.to_dict()

        # Check that all values are strings
        assert data["positions"] == {"AAPL": "100", "MSFT": "50.5"}
        assert data["prices"] == {"AAPL": "150.00", "MSFT": "300.25"}
        assert data["cash"] == "5000.00"
        assert data["total_value"] == "25012.50"

    def test_to_dict_with_empty_positions(self):
        """Test to_dict with empty positions."""
        snapshot = PortfolioSnapshot(
            positions={},
            prices={},
            cash=Decimal("10000.00"),
            total_value=Decimal("10000.00"),
        )

        data = snapshot.to_dict()

        assert data["positions"] == {}
        assert data["prices"] == {}
        assert data["cash"] == "10000.00"
        assert data["total_value"] == "10000.00"

    def test_to_dict_preserves_precision(self):
        """Test that to_dict preserves Decimal precision."""
        snapshot = PortfolioSnapshot(
            positions={"BTC": Decimal("0.123456789")},
            prices={"BTC": Decimal("45678.123456")},
            cash=Decimal("1234.56789"),
            total_value=Decimal("6879.073203658884"),
        )

        data = snapshot.to_dict()

        assert data["positions"]["BTC"] == "0.123456789"
        assert data["prices"]["BTC"] == "45678.123456"
        assert data["cash"] == "1234.56789"
        # Verify precision is maintained
        assert "0.123456789" in data["positions"]["BTC"]


class TestPortfolioSnapshotDeserialization:
    """Test PortfolioSnapshot deserialization from dictionary."""

    def test_from_dict_converts_strings_to_decimals(self):
        """Test that from_dict converts all string values to Decimals."""
        data = {
            "positions": {"AAPL": "100", "MSFT": "50.5"},
            "prices": {"AAPL": "150.00", "MSFT": "300.25"},
            "cash": "5000.00",
            "total_value": "25012.50",
        }

        snapshot = PortfolioSnapshot.from_dict(data)

        # Check that all values are Decimals
        assert snapshot.positions == {"AAPL": Decimal("100"), "MSFT": Decimal("50.5")}
        assert snapshot.prices == {"AAPL": Decimal("150.00"), "MSFT": Decimal("300.25")}
        assert snapshot.cash == Decimal("5000.00")
        assert snapshot.total_value == Decimal("25012.50")

    def test_from_dict_with_decimal_values(self):
        """Test from_dict when values are already Decimals."""
        data = {
            "positions": {"AAPL": Decimal("100")},
            "prices": {"AAPL": Decimal("150.00")},
            "cash": Decimal("5000.00"),
            "total_value": Decimal("20000.00"),
        }

        snapshot = PortfolioSnapshot.from_dict(data)

        assert snapshot.positions == {"AAPL": Decimal("100")}
        assert snapshot.prices == {"AAPL": Decimal("150.00")}
        assert snapshot.cash == Decimal("5000.00")
        assert snapshot.total_value == Decimal("20000.00")

    def test_from_dict_with_empty_positions(self):
        """Test from_dict with empty positions."""
        data = {
            "positions": {},
            "prices": {},
            "cash": "10000.00",
            "total_value": "10000.00",
        }

        snapshot = PortfolioSnapshot.from_dict(data)

        assert snapshot.positions == {}
        assert snapshot.prices == {}
        assert snapshot.cash == Decimal("10000.00")
        assert snapshot.total_value == Decimal("10000.00")

    def test_from_dict_validates_data(self):
        """Test that from_dict validates data through __post_init__."""
        # Missing price for position
        data = {
            "positions": {"AAPL": "100"},
            "prices": {},
            "cash": "5000.00",
            "total_value": "20000.00",
        }

        with pytest.raises(ValueError, match="Missing prices for positions"):
            PortfolioSnapshot.from_dict(data)

    def test_from_dict_invalid_cash_value(self):
        """Test from_dict with invalid cash value."""
        data = {
            "positions": {},
            "prices": {},
            "cash": "invalid",
            "total_value": "10000.00",
        }

        with pytest.raises(ValueError, match="Invalid cash value"):
            PortfolioSnapshot.from_dict(data)

    def test_from_dict_invalid_total_value(self):
        """Test from_dict with invalid total_value."""
        data = {
            "positions": {},
            "prices": {},
            "cash": "10000.00",
            "total_value": "not_a_number",
        }

        with pytest.raises(ValueError, match="Invalid total_value"):
            PortfolioSnapshot.from_dict(data)

    def test_from_dict_invalid_position_value(self):
        """Test from_dict with invalid position value."""
        data = {
            "positions": {"AAPL": "invalid_quantity"},
            "prices": {"AAPL": "150.00"},
            "cash": "5000.00",
            "total_value": "20000.00",
        }

        with pytest.raises(ValueError, match="Invalid decimal value"):
            PortfolioSnapshot.from_dict(data)

    def test_from_dict_does_not_modify_original(self):
        """Test that from_dict does not modify the original dictionary."""
        data = {
            "positions": {"AAPL": "100"},
            "prices": {"AAPL": "150.00"},
            "cash": "5000.00",
            "total_value": "20000.00",
        }
        original_data = data.copy()

        PortfolioSnapshot.from_dict(data)

        # Original data should be unchanged
        assert data == original_data
        assert isinstance(data["cash"], str)


class TestPortfolioSnapshotRoundTrip:
    """Test round-trip serialization and deserialization."""

    def test_round_trip_preserves_data(self):
        """Test that to_dict -> from_dict round trip preserves data."""
        original = PortfolioSnapshot(
            positions={"AAPL": Decimal("100"), "MSFT": Decimal("50.5")},
            prices={"AAPL": Decimal("150.00"), "MSFT": Decimal("300.25")},
            cash=Decimal("5000.00"),
            total_value=Decimal("25012.50"),
        )

        # Round trip
        data = original.to_dict()
        restored = PortfolioSnapshot.from_dict(data)

        # Check equality
        assert restored.positions == original.positions
        assert restored.prices == original.prices
        assert restored.cash == original.cash
        assert restored.total_value == original.total_value

    def test_round_trip_with_high_precision(self):
        """Test round trip with high precision Decimal values."""
        original = PortfolioSnapshot(
            positions={"BTC": Decimal("0.123456789012345")},
            prices={"BTC": Decimal("45678.123456789012")},
            cash=Decimal("1234.567890123456"),
            total_value=Decimal("6879.073203658884123456"),
        )

        # Round trip
        data = original.to_dict()
        restored = PortfolioSnapshot.from_dict(data)

        # Check precision is maintained
        assert restored.positions["BTC"] == original.positions["BTC"]
        assert restored.prices["BTC"] == original.prices["BTC"]
        assert restored.cash == original.cash
        assert restored.total_value == original.total_value

    def test_round_trip_with_empty_portfolio(self):
        """Test round trip with empty portfolio."""
        original = PortfolioSnapshot(
            positions={},
            prices={},
            cash=Decimal("10000.00"),
            total_value=Decimal("10000.00"),
        )

        # Round trip
        data = original.to_dict()
        restored = PortfolioSnapshot.from_dict(data)

        assert restored.positions == original.positions
        assert restored.prices == original.prices
        assert restored.cash == original.cash
        assert restored.total_value == original.total_value
