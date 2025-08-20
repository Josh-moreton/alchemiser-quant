"""Tests for Confidence value object."""

from decimal import Decimal

import pytest

from the_alchemiser.domain.strategies.value_objects.confidence import Confidence


class TestConfidence:
    """Test cases for Confidence value object."""

    def test_valid_confidence_creation(self) -> None:
        """Test creating valid confidence values."""
        # Test boundary values
        low_confidence = Confidence(Decimal("0.0"))
        assert low_confidence.value == Decimal("0.0")
        assert low_confidence.is_low
        assert not low_confidence.is_high

        mid_confidence = Confidence(Decimal("0.5"))
        assert mid_confidence.value == Decimal("0.5")
        assert not mid_confidence.is_low
        assert not mid_confidence.is_high

        high_confidence = Confidence(Decimal("1.0"))
        assert high_confidence.value == Decimal("1.0")
        assert not high_confidence.is_low
        assert high_confidence.is_high

    def test_confidence_properties(self) -> None:
        """Test confidence level properties."""
        # Test is_high boundary (>= 0.7)
        high_boundary = Confidence(Decimal("0.7"))
        assert high_boundary.is_high
        assert not high_boundary.is_low

        just_under_high = Confidence(Decimal("0.69"))
        assert not just_under_high.is_high

        # Test is_low boundary (<= 0.3)
        low_boundary = Confidence(Decimal("0.3"))
        assert low_boundary.is_low
        assert not low_boundary.is_high

        just_over_low = Confidence(Decimal("0.31"))
        assert not just_over_low.is_low

    def test_invalid_confidence_values(self) -> None:
        """Test that invalid confidence values raise errors."""
        # Test negative values
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Confidence(Decimal("-0.1"))

        # Test values over 1.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Confidence(Decimal("1.1"))

        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Confidence(Decimal("2.0"))

    def test_confidence_immutability(self) -> None:
        """Test that Confidence objects are immutable."""
        confidence = Confidence(Decimal("0.8"))

        # Should not be able to modify the value
        with pytest.raises(AttributeError):
            confidence.value = Decimal("0.5")  # type: ignore

    def test_confidence_equality(self) -> None:
        """Test confidence equality comparison."""
        conf1 = Confidence(Decimal("0.8"))
        conf2 = Confidence(Decimal("0.8"))
        conf3 = Confidence(Decimal("0.7"))

        assert conf1 == conf2
        assert conf1 != conf3

    def test_confidence_from_different_decimal_representations(self) -> None:
        """Test that different decimal representations work correctly."""
        conf1 = Confidence(Decimal("0.80"))
        conf2 = Confidence(Decimal("0.8"))
        conf3 = Confidence(Decimal("8") / Decimal("10"))

        assert conf1 == conf2 == conf3
        assert conf1.value == conf2.value == conf3.value
