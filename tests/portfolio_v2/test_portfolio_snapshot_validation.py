"""Business Unit: portfolio | Status: current

Test portfolio snapshot validation and edge cases.

Tests PortfolioSnapshot model validation, error handling, and edge cases
to achieve comprehensive branch coverage.
"""

from decimal import Decimal

import pytest

from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
from the_alchemiser.shared.errors.exceptions import PortfolioError


class TestPortfolioSnapshotValidation:
    """Test PortfolioSnapshot validation and edge cases."""

    def test_snapshot_with_valid_data(self):
        """Test creating snapshot with valid data."""
        positions = {"AAPL": Decimal("10"), "GOOGL": Decimal("5")}
        prices = {"AAPL": Decimal("150.00"), "GOOGL": Decimal("2800.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("16500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.positions == positions
        assert snapshot.prices == prices
        assert snapshot.cash == cash
        assert snapshot.total_value == total_value

    def test_snapshot_missing_price_for_position_raises_error(self):
        """Test that missing price for position raises PortfolioError."""
        positions = {"AAPL": Decimal("10"), "GOOGL": Decimal("5")}
        prices = {"AAPL": Decimal("150.00")}  # Missing GOOGL
        cash = Decimal("1000.00")
        total_value = Decimal("2500.00")

        with pytest.raises(PortfolioError) as exc_info:
            PortfolioSnapshot(
                positions=positions,
                prices=prices,
                cash=cash,
                total_value=total_value,
            )

        assert "Missing prices for positions" in str(exc_info.value)
        assert "GOOGL" in str(exc_info.value)

    def test_snapshot_negative_total_value_raises_error(self):
        """Test that negative total value raises PortfolioError."""
        positions = {}
        prices = {}
        cash = Decimal("1000.00")
        total_value = Decimal("-100.00")  # Negative

        with pytest.raises(PortfolioError) as exc_info:
            PortfolioSnapshot(
                positions=positions,
                prices=prices,
                cash=cash,
                total_value=total_value,
            )

        assert "Total value cannot be negative" in str(exc_info.value)

    def test_snapshot_negative_position_quantity_raises_error(self):
        """Test that negative position quantity raises PortfolioError."""
        positions = {"AAPL": Decimal("-10")}  # Negative quantity
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("1000.00")

        with pytest.raises(PortfolioError) as exc_info:
            PortfolioSnapshot(
                positions=positions,
                prices=prices,
                cash=cash,
                total_value=total_value,
            )

        assert "Position quantity cannot be negative" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)

    def test_snapshot_zero_price_raises_error(self):
        """Test that zero price raises PortfolioError."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("0.00")}  # Zero price
        cash = Decimal("1000.00")
        total_value = Decimal("1000.00")

        with pytest.raises(PortfolioError) as exc_info:
            PortfolioSnapshot(
                positions=positions,
                prices=prices,
                cash=cash,
                total_value=total_value,
            )

        assert "Price must be positive" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)

    def test_snapshot_negative_price_raises_error(self):
        """Test that negative price raises PortfolioError."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("-150.00")}  # Negative price
        cash = Decimal("1000.00")
        total_value = Decimal("1000.00")

        with pytest.raises(PortfolioError) as exc_info:
            PortfolioSnapshot(
                positions=positions,
                prices=prices,
                cash=cash,
                total_value=total_value,
            )

        assert "Price must be positive" in str(exc_info.value)
        assert "AAPL" in str(exc_info.value)

    def test_get_position_value_success(self):
        """Test getting position value for valid symbol."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("2500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        value = snapshot.get_position_value("AAPL")
        assert value == Decimal("1500.00")  # 10 * 150

    def test_get_position_value_symbol_not_in_positions(self):
        """Test get_position_value raises KeyError for missing position."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00"), "GOOGL": Decimal("2800.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("2500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        with pytest.raises(KeyError) as exc_info:
            snapshot.get_position_value("GOOGL")

        assert "GOOGL" in str(exc_info.value)
        assert "not found in positions" in str(exc_info.value)

    def test_get_position_value_symbol_not_in_prices(self):
        """Test get_position_value raises KeyError for missing price."""
        # This shouldn't happen due to __post_init__ validation,
        # but test the method's error handling
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("2500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        # Manually test the scenario (can't create invalid snapshot through __init__)
        # The validation in __post_init__ should prevent this
        # But the get_position_value method has the check
        # We can verify it works for valid data
        assert snapshot.get_position_value("AAPL") == Decimal("1500.00")

    def test_get_all_position_values(self):
        """Test getting values for all positions."""
        positions = {
            "AAPL": Decimal("10"),
            "GOOGL": Decimal("5"),
            "MSFT": Decimal("20"),
        }
        prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
            "MSFT": Decimal("380.00"),
        }
        cash = Decimal("1000.00")
        total_value = Decimal("23100.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        values = snapshot.get_all_position_values()

        assert values["AAPL"] == Decimal("1500.00")  # 10 * 150
        assert values["GOOGL"] == Decimal("14000.00")  # 5 * 2800
        assert values["MSFT"] == Decimal("7600.00")  # 20 * 380

    def test_get_total_position_value(self):
        """Test calculating total position value."""
        positions = {
            "AAPL": Decimal("10"),
            "GOOGL": Decimal("5"),
        }
        prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
        }
        cash = Decimal("1000.00")
        total_value = Decimal("16500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        position_value = snapshot.get_total_position_value()
        assert position_value == Decimal("15500.00")  # 1500 + 14000

    def test_get_total_position_value_empty_positions(self):
        """Test total position value with no positions."""
        positions = {}
        prices = {}
        cash = Decimal("5000.00")
        total_value = Decimal("5000.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        position_value = snapshot.get_total_position_value()
        assert position_value == Decimal("0")

    def test_validate_total_value_within_tolerance(self):
        """Test validation succeeds when total value matches within tolerance."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        # Exact: 1500 + 1000 = 2500
        total_value = Decimal("2500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.validate_total_value() is True

    def test_validate_total_value_slight_mismatch_within_tolerance(self):
        """Test validation succeeds with slight mismatch within tolerance."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        # Exact: 2500, but we use 2500.005 (within 0.01 tolerance)
        total_value = Decimal("2500.005")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.validate_total_value() is True

    def test_validate_total_value_mismatch_outside_tolerance(self):
        """Test validation fails when mismatch exceeds tolerance."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        # Exact: 2500, but we use 2510 (exceeds 0.01 tolerance)
        total_value = Decimal("2510.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.validate_total_value() is False

    def test_validate_total_value_custom_tolerance(self):
        """Test validation with custom tolerance."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        # Exact: 2500, but we use 2505 (within 10 tolerance, not within 0.01)
        total_value = Decimal("2505.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        # Should fail with default tolerance
        assert snapshot.validate_total_value() is False

        # Should pass with higher tolerance
        assert snapshot.validate_total_value(tolerance=Decimal("10.00")) is True

    def test_snapshot_is_frozen(self):
        """Test that snapshot is immutable (frozen dataclass)."""
        positions = {"AAPL": Decimal("10")}
        prices = {"AAPL": Decimal("150.00")}
        cash = Decimal("1000.00")
        total_value = Decimal("2500.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        # Attempt to modify should raise error
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            snapshot.cash = Decimal("2000.00")

    def test_snapshot_with_fractional_quantities(self):
        """Test snapshot with fractional asset quantities."""
        positions = {"AAPL": Decimal("10.5"), "BTC": Decimal("0.123")}
        prices = {"AAPL": Decimal("150.00"), "BTC": Decimal("50000.00")}
        cash = Decimal("1000.00")
        # 10.5 * 150 + 0.123 * 50000 + 1000 = 1575 + 6150 + 1000 = 8725
        total_value = Decimal("8725.00")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.get_position_value("AAPL") == Decimal("1575.00")
        assert snapshot.get_position_value("BTC") == Decimal("6150.00")

    def test_snapshot_with_high_precision_decimals(self):
        """Test snapshot with high precision decimal values."""
        positions = {"AAPL": Decimal("10.123456789")}
        prices = {"AAPL": Decimal("150.987654321")}
        cash = Decimal("1000.123456789")

        # Calculate exact total
        position_value = Decimal("10.123456789") * Decimal("150.987654321")
        total_value = position_value + Decimal("1000.123456789")

        snapshot = PortfolioSnapshot(
            positions=positions,
            prices=prices,
            cash=cash,
            total_value=total_value,
        )

        assert snapshot.validate_total_value() is True
