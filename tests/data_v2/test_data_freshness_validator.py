"""Business Unit: data | Status: current.

Tests for data freshness validation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from the_alchemiser.data_v2.data_freshness_validator import DataFreshnessValidator
from the_alchemiser.data_v2.market_data_store import SymbolMetadata
from the_alchemiser.shared.errors.exceptions import DataProviderError


class TestDataFreshnessValidator:
    """Test suite for DataFreshnessValidator."""

    def test_fresh_data_passes_validation(self) -> None:
        """Test that fresh data passes validation."""
        # Arrange
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        metadata = SymbolMetadata(
            symbol="SPY",
            last_bar_date=yesterday,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )

        store = Mock()
        store.list_symbols.return_value = ["SPY"]
        store.get_metadata.return_value = metadata

        validator = DataFreshnessValidator(market_data_store=store, max_staleness_days=2)

        # Act
        is_fresh, stale_symbols = validator.validate_data_freshness()

        # Assert
        assert is_fresh is True
        assert len(stale_symbols) == 0

    def test_stale_data_detected(self) -> None:
        """Test that stale data is detected."""
        # Arrange - data from 5 days ago
        five_days_ago = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%d")
        metadata = SymbolMetadata(
            symbol="AAPL",
            last_bar_date=five_days_ago,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )

        store = Mock()
        store.list_symbols.return_value = ["AAPL"]
        store.get_metadata.return_value = metadata

        validator = DataFreshnessValidator(market_data_store=store, max_staleness_days=2)

        # Act
        is_fresh, stale_symbols = validator.validate_data_freshness()

        # Assert
        assert is_fresh is False
        assert "AAPL" in stale_symbols
        assert stale_symbols["AAPL"] == five_days_ago

    def test_missing_metadata_detected(self) -> None:
        """Test that missing metadata is detected."""
        # Arrange
        store = Mock()
        store.list_symbols.return_value = ["TSLA"]
        store.get_metadata.return_value = None  # Missing metadata

        validator = DataFreshnessValidator(market_data_store=store, max_staleness_days=2)

        # Act
        is_fresh, stale_symbols = validator.validate_data_freshness()

        # Assert
        assert is_fresh is False
        assert len(stale_symbols) == 0  # Missing metadata doesn't appear in stale_symbols

    def test_raise_on_stale_throws_error(self) -> None:
        """Test that raise_on_stale parameter raises DataProviderError."""
        # Arrange
        five_days_ago = (datetime.now(UTC) - timedelta(days=5)).strftime("%Y-%m-%d")
        metadata = SymbolMetadata(
            symbol="NVDA",
            last_bar_date=five_days_ago,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )

        store = Mock()
        store.list_symbols.return_value = ["NVDA"]
        store.get_metadata.return_value = metadata

        validator = DataFreshnessValidator(market_data_store=store, max_staleness_days=2)

        # Act & Assert
        with pytest.raises(DataProviderError, match="Stale market data detected"):
            validator.validate_data_freshness(raise_on_stale=True)

    def test_weekend_date_calculation(self) -> None:
        """Test that expected date calculation accounts for weekends."""
        # Arrange
        store = Mock()
        store.list_symbols.return_value = []

        validator = DataFreshnessValidator(market_data_store=store)

        # Act
        expected_date = validator._calculate_expected_date()

        # Assert
        today = datetime.now(UTC).date()
        weekday = today.weekday()

        if weekday == 5:  # Saturday
            assert expected_date == today - timedelta(days=1)  # Friday
        elif weekday == 6:  # Sunday
            assert expected_date == today - timedelta(days=2)  # Friday
        else:  # Weekday
            assert expected_date == today - timedelta(days=1)  # Yesterday

    def test_custom_symbol_list(self) -> None:
        """Test validation with custom symbol list instead of all symbols."""
        # Arrange
        yesterday = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        metadata = SymbolMetadata(
            symbol="MSFT",
            last_bar_date=yesterday,
            row_count=1000,
            updated_at=datetime.now(UTC).isoformat(),
        )

        store = Mock()
        store.get_metadata.return_value = metadata
        # list_symbols should NOT be called when explicit symbols provided

        validator = DataFreshnessValidator(market_data_store=store, max_staleness_days=2)

        # Act
        is_fresh, stale_symbols = validator.validate_data_freshness(symbols=["MSFT"])

        # Assert
        assert is_fresh is True
        store.list_symbols.assert_not_called()  # Should not call list_symbols
        store.get_metadata.assert_called_once_with("MSFT")
