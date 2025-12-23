"""Business Unit: data | Status: current.

Tests for data quality validation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pandas as pd

from the_alchemiser.data_v2.data_quality_validator import (
    DataQualityValidator,
    ValidationDiscrepancy,
)
from the_alchemiser.data_v2.market_data_store import MarketDataStore


class TestDataQualityValidator:
    """Test suite for DataQualityValidator."""

    def test_validate_symbol_no_data_in_s3(self) -> None:
        """Test validation when symbol has no data in S3."""
        # Arrange
        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = None

        validator = DataQualityValidator(market_data_store=store)

        # Act
        passed, discrepancies = validator.validate_symbol("AAPL")

        # Assert
        assert passed is False
        assert len(discrepancies) == 0

    def test_validate_symbol_matching_data(self) -> None:
        """Test validation when Alpaca and yfinance data match."""
        # Arrange
        today = datetime.now(UTC)

        # Mock S3 data
        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(market_data_store=store)

        # Mock yfinance data (matching values)
        yf_df = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [152.0],
                "Low": [149.0],
                "Close": [151.0],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([today]),
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert
            assert passed is True
            assert len(discrepancies) == 0

    def test_validate_symbol_price_discrepancy(self) -> None:
        """Test validation detects price discrepancies."""
        # Arrange
        today = datetime.now(UTC)

        # Mock S3 data
        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(
            market_data_store=store, price_tolerance_pct=Decimal("0.5")
        )

        # Mock yfinance data (close price differs by 2%)
        yf_df = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [152.0],
                "Low": [149.0],
                "Close": [154.0],  # 2% difference
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([today]),
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert
            assert passed is False
            assert len(discrepancies) == 1
            assert discrepancies[0].symbol == "AAPL"
            assert discrepancies[0].field == "close"
            assert discrepancies[0].alpaca_value == Decimal("151.0")
            assert discrepancies[0].yfinance_value == Decimal("154.0")

    def test_validate_symbol_volume_discrepancy(self) -> None:
        """Test validation detects volume discrepancies."""
        # Arrange
        today = datetime.now(UTC)

        # Mock S3 data
        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(
            market_data_store=store, volume_tolerance_pct=Decimal("5.0")
        )

        # Mock yfinance data (volume differs by 10%)
        yf_df = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [152.0],
                "Low": [149.0],
                "Close": [151.0],
                "Volume": [1100000],  # 10% difference
            },
            index=pd.DatetimeIndex([today]),
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert
            assert passed is False
            assert len(discrepancies) == 1
            assert discrepancies[0].field == "volume"

    def test_validate_all_symbols(self) -> None:
        """Test validation of all symbols in S3."""
        # Arrange
        store = Mock(spec=MarketDataStore)
        store.list_symbols.return_value = ["AAPL", "MSFT"]

        today = datetime.now(UTC)

        # Mock S3 data for both symbols
        df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )
        store.read_symbol_data.return_value = df

        validator = DataQualityValidator(market_data_store=store)

        # Mock yfinance data (matching)
        yf_df = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [152.0],
                "Low": [149.0],
                "Close": [151.0],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([today]),
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            result = validator.validate_all_symbols(lookback_days=5)

            # Assert
            assert result.symbols_checked == 2
            assert result.symbols_passed == 2
            assert result.symbols_failed == 0
            assert len(result.discrepancies) == 0

    def test_generate_report_csv(self) -> None:
        """Test CSV report generation."""
        # Arrange
        store = Mock(spec=MarketDataStore)
        validator = DataQualityValidator(market_data_store=store)

        from the_alchemiser.data_v2.data_quality_validator import ValidationResult

        discrepancies = [
            ValidationDiscrepancy(
                symbol="AAPL",
                date="2024-01-01",
                field="close",
                alpaca_value=Decimal("150.0"),
                yfinance_value=Decimal("152.0"),
                diff_pct=Decimal("1.33"),
            )
        ]

        result = ValidationResult(
            symbols_checked=1,
            symbols_passed=0,
            symbols_failed=1,
            discrepancies=discrepancies,
            validation_date="2024-01-01",
        )

        # Act
        report_path = validator.generate_report_csv(result)

        # Assert
        assert report_path.exists()
        assert report_path.suffix == ".csv"

        # Check CSV content
        content = report_path.read_text()
        assert "AAPL" in content
        assert "close" in content
        assert "150.0" in content
        assert "152.0" in content

        # Cleanup
        report_path.unlink()

    def test_upload_report_to_s3(self) -> None:
        """Test uploading validation report to S3."""
        # Arrange
        mock_s3_client = MagicMock()
        store = Mock(spec=MarketDataStore)
        store.bucket_name = "test-bucket"
        store.s3_client = mock_s3_client

        validator = DataQualityValidator(market_data_store=store)

        # Create a temp report file
        import tempfile

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        temp_file.write("Symbol,Date,Field,Alpaca Value,YFinance Value,Diff %\n")
        temp_file.write("AAPL,2024-01-01,close,150.0,152.0,1.33\n")
        temp_file.close()

        from pathlib import Path

        report_path = Path(temp_file.name)

        # Act
        s3_key = validator.upload_report_to_s3(
            report_path=report_path,
            validation_date="2024-01-01",
        )

        # Assert
        assert s3_key == "data-quality-reports/2024-01-01_validation_report.csv"
        mock_s3_client.put_object.assert_called_once()

        # Cleanup
        report_path.unlink()

    def test_validate_symbol_yfinance_empty_response(self) -> None:
        """Test validation when yfinance returns empty data for symbol."""
        # Arrange
        today = datetime.now(UTC)

        # Mock S3 data
        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(market_data_store=store)

        # Mock yfinance returning empty DataFrame
        yf_df = pd.DataFrame(
            {
                "Open": [],
                "High": [],
                "Low": [],
                "Close": [],
                "Volume": [],
            }
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert
            assert passed is False
            assert len(discrepancies) == 0

    def test_validate_symbol_missing_timestamp_column(self) -> None:
        """Test validation when S3 data is missing timestamp column."""
        # Arrange
        # Mock S3 data without timestamp column
        alpaca_df = pd.DataFrame(
            {
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(market_data_store=store)

        # Act
        passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

        # Assert
        assert passed is False
        assert len(discrepancies) == 0

    def test_validate_symbol_both_zero_values(self) -> None:
        """Test validation correctly handles case where both sources report zero."""
        # Arrange
        today = datetime.now(UTC)

        # Mock S3 data with zero values
        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [0.0],
                "high": [0.0],
                "low": [0.0],
                "close": [0.0],
                "volume": [0],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(market_data_store=store)

        # Mock yfinance data also with zero values (legitimate scenario)
        yf_df = pd.DataFrame(
            {
                "Open": [0.0],
                "High": [0.0],
                "Low": [0.0],
                "Close": [0.0],
                "Volume": [0],
            },
            index=pd.DatetimeIndex([today]),
        )

        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.history.return_value = yf_df

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert - should pass because both zeros are legitimate match
            assert passed is True
            assert len(discrepancies) == 0

    def test_validate_symbol_yfinance_network_error(self) -> None:
        """Test validation handles yfinance network errors gracefully."""
        # Arrange
        today = datetime.now(UTC)

        alpaca_df = pd.DataFrame(
            {
                "timestamp": [today],
                "open": [150.0],
                "high": [152.0],
                "low": [149.0],
                "close": [151.0],
                "volume": [1000000],
            }
        )

        store = Mock(spec=MarketDataStore)
        store.read_symbol_data.return_value = alpaca_df

        validator = DataQualityValidator(market_data_store=store)

        # Mock yfinance raising OSError (network error)
        with patch("the_alchemiser.data_v2.data_quality_validator.yf.Ticker") as mock_ticker:
            mock_ticker.side_effect = OSError("Network error connecting to yfinance")

            # Act
            passed, discrepancies = validator.validate_symbol("AAPL", lookback_days=5)

            # Assert - should return False but not raise exception
            assert passed is False
            assert len(discrepancies) == 0
