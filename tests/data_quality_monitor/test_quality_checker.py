"""Business Unit: data_quality_monitor | Status: current.

Tests for data quality validation logic.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pandas as pd
import pytest

from the_alchemiser.data_quality_monitor.quality_checker import (
    DataQualityChecker,
)


class TestDataQualityChecker:
    """Test suite for DataQualityChecker."""

    def test_validation_passes_for_good_data(self) -> None:
        """Test that validation passes when data matches external source."""
        # Arrange
        checker = DataQualityChecker()

        # Mock our S3 data
        our_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(5, 0, -1)
                ],
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            }
        )

        # Mock external data (same as ours)
        external_data = our_data.copy()

        # Mock methods
        checker._fetch_our_data = Mock(return_value=our_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=external_data)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("AAPL", lookback_days=5)

        # Assert
        assert result.passed is True
        assert len(result.issues) == 0
        assert result.symbol == "AAPL"
        assert result.rows_checked == 5

    def test_validation_detects_stale_data(self) -> None:
        """Test that validation detects stale data."""
        # Arrange
        checker = DataQualityChecker()

        # Mock stale S3 data (5 days old)
        our_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(10, 5, -1)
                ],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        # Mock external data (fresh)
        external_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(5, 0, -1)
                ],
                "close": [105.0, 106.0, 107.0, 108.0, 109.0],
            }
        )

        # Mock methods
        checker._fetch_our_data = Mock(return_value=our_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=external_data)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("GOOGL", lookback_days=5)

        # Assert
        assert result.passed is False
        assert any("stale" in issue.lower() for issue in result.issues)

    def test_validation_detects_missing_dates(self) -> None:
        """Test that validation detects missing trading days."""
        # Arrange
        checker = DataQualityChecker()

        # Mock our S3 data (missing recent days)
        our_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(5, 2, -1)
                ],
                "close": [100.0, 101.0, 102.0],
            }
        )

        # Mock external data (has all recent days)
        external_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(5, 0, -1)
                ],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        # Mock methods
        checker._fetch_our_data = Mock(return_value=our_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=external_data)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("MSFT", lookback_days=5)

        # Assert
        assert result.passed is False
        assert any("missing" in issue.lower() for issue in result.issues)

    def test_validation_detects_price_discrepancy(self) -> None:
        """Test that validation detects price discrepancies."""
        # Arrange
        checker = DataQualityChecker()

        # Mock our S3 data
        our_data = pd.DataFrame(
            {
                "timestamp": [datetime.now(UTC) - timedelta(days=1)],
                "close": [100.0],
            }
        )

        # Mock external data with different price (>2% diff)
        external_data = pd.DataFrame(
            {
                "timestamp": [datetime.now(UTC) - timedelta(days=1)],
                "close": [110.0],  # 10% difference
            }
        )

        # Mock methods
        checker._fetch_our_data = Mock(return_value=our_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=external_data)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("TSLA", lookback_days=1)

        # Assert
        assert result.passed is False
        assert any("mismatch" in issue.lower() for issue in result.issues)

    def test_validation_handles_missing_s3_data(self) -> None:
        """Test that validation handles missing S3 data."""
        # Arrange
        checker = DataQualityChecker()

        # Mock no S3 data
        checker._fetch_our_data = Mock(return_value=None)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("NVDA", lookback_days=5)

        # Assert
        assert result.passed is False
        assert any("no data found" in issue.lower() for issue in result.issues)
        assert result.rows_checked == 0

    def test_validation_handles_missing_external_data(self) -> None:
        """Test that validation handles missing external data."""
        # Arrange
        checker = DataQualityChecker()

        # Mock our S3 data
        our_data = pd.DataFrame(
            {
                "timestamp": [datetime.now(UTC) - timedelta(days=1)],
                "close": [100.0],
            }
        )

        # Mock no external data
        checker._fetch_our_data = Mock(return_value=our_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=None)  # type: ignore[method-assign]

        # Act
        result = checker._validate_symbol("UNKNOWN", lookback_days=5)

        # Assert
        assert result.passed is False
        assert any("no external data" in issue.lower() for issue in result.issues)

    def test_validate_multiple_symbols(self) -> None:
        """Test validation of multiple symbols."""
        # Arrange
        checker = DataQualityChecker()

        # Mock good data for all symbols
        good_data = pd.DataFrame(
            {
                "timestamp": [
                    datetime.now(UTC) - timedelta(days=i) for i in range(5, 0, -1)
                ],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
            }
        )

        checker._fetch_our_data = Mock(return_value=good_data)  # type: ignore[method-assign]
        checker._fetch_external_data = Mock(return_value=good_data)  # type: ignore[method-assign]

        # Act
        results = checker.validate_symbols(["AAPL", "GOOGL", "MSFT"], lookback_days=5)

        # Assert
        assert len(results) == 3
        assert all(r.passed for r in results.values())
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results

    def test_validate_symbols_handles_exceptions(self) -> None:
        """Test that validation handles exceptions gracefully."""
        # Arrange
        from the_alchemiser.data_quality_monitor.quality_checker import DataQualityError

        checker = DataQualityChecker()

        # Mock exception during validation
        checker._fetch_our_data = Mock(side_effect=Exception("S3 error"))  # type: ignore[method-assign]

        # Act & Assert - should raise DataQualityError
        with pytest.raises(DataQualityError) as exc_info:
            checker.validate_symbols(["ERROR"], lookback_days=5)
        
        assert "Validation failed for ERROR" in str(exc_info.value)
