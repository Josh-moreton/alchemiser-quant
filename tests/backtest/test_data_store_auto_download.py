"""Business Unit: scripts | Status: current.

Unit tests for data store auto-download functionality.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to path dynamically
project_root = Path(__file__).resolve().parents[2]
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from scripts.backtest.models.market_data import DailyBar
from scripts.backtest.storage.data_store import DataStore
from the_alchemiser.shared.types.exceptions import DataUnavailableError


@pytest.fixture
def temp_data_store(tmp_path: Path) -> DataStore:
    """Create a temporary data store for testing."""
    return DataStore(base_path=str(tmp_path / "test_data"))


@pytest.fixture
def mock_provider():
    """Create a mock data provider."""
    return Mock()


@pytest.fixture
def sample_bars() -> list[DailyBar]:
    """Create sample daily bars for testing."""
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(5):
        bar = DailyBar(
            date=base_date.replace(day=i + 1),
            open=Decimal("100") + Decimal(i),
            high=Decimal("105") + Decimal(i),
            low=Decimal("95") + Decimal(i),
            close=Decimal("102") + Decimal(i),
            volume=1000000 + (i * 10000),
            adjusted_close=Decimal("102") + Decimal(i),
        )
        bars.append(bar)
    return bars


def test_load_bars_with_missing_data_no_provider_raises_error(
    temp_data_store: DataStore,
) -> None:
    """Test that loading bars without provider and missing data raises DataUnavailableError."""
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    # No data provider configured
    with pytest.raises(DataUnavailableError) as exc_info:
        temp_data_store.load_bars("TEST", start_date, end_date)

    assert "TEST" in str(exc_info.value)
    assert "2024" in str(exc_info.value)
    assert exc_info.value.symbol == "TEST"
    assert exc_info.value.required_start_date == start_date.isoformat()
    assert exc_info.value.required_end_date == end_date.isoformat()


def test_load_bars_auto_downloads_missing_data(
    temp_data_store: DataStore, mock_provider, sample_bars: list[DailyBar]
) -> None:
    """Test that loading bars with missing data auto-downloads from provider."""
    # Configure mock provider
    mock_provider.fetch_daily_bars.return_value = sample_bars
    temp_data_store.data_provider = mock_provider

    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    # Load bars (should auto-download)
    bars = temp_data_store.load_bars("TEST", start_date, end_date)

    # Verify provider was called
    mock_provider.fetch_daily_bars.assert_called_once_with("TEST", start_date, end_date)

    # Verify bars were returned
    assert len(bars) == 5
    assert bars[0].symbol is None or bars[0].date == sample_bars[0].date


def test_load_bars_auto_download_empty_data_raises_error(
    temp_data_store: DataStore, mock_provider
) -> None:
    """Test that auto-download with no data from provider raises DataUnavailableError."""
    # Configure mock provider to return empty list
    mock_provider.fetch_daily_bars.return_value = []
    temp_data_store.data_provider = mock_provider

    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    with pytest.raises(DataUnavailableError) as exc_info:
        temp_data_store.load_bars("TEST", start_date, end_date)

    assert "TEST" in str(exc_info.value)
    assert "no data available from provider" in str(exc_info.value)
    assert exc_info.value.symbol == "TEST"


def test_load_bars_auto_download_provider_error_raises_data_unavailable(
    temp_data_store: DataStore, mock_provider
) -> None:
    """Test that provider errors are wrapped in DataUnavailableError."""
    # Configure mock provider to raise an error
    mock_provider.fetch_daily_bars.side_effect = Exception("API rate limit exceeded")
    temp_data_store.data_provider = mock_provider

    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    with pytest.raises(DataUnavailableError) as exc_info:
        temp_data_store.load_bars("TEST", start_date, end_date)

    assert "TEST" in str(exc_info.value)
    assert "Failed to download data" in str(exc_info.value)
    assert "API rate limit exceeded" in str(exc_info.value)


def test_load_bars_uses_cached_data_if_available(
    temp_data_store: DataStore, mock_provider, sample_bars: list[DailyBar]
) -> None:
    """Test that load_bars uses cached data and doesn't download if files exist."""
    # Configure provider
    temp_data_store.data_provider = mock_provider

    # Save bars first to create cache
    temp_data_store.save_bars("TEST", sample_bars)

    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    # Load bars (should use cache, not call provider)
    bars = temp_data_store.load_bars("TEST", start_date, end_date)

    # Verify provider was NOT called
    mock_provider.fetch_daily_bars.assert_not_called()

    # Verify bars were loaded from cache
    assert len(bars) == 5


def test_load_bars_downloads_only_missing_years(
    temp_data_store: DataStore, mock_provider
) -> None:
    """Test that only missing year data is downloaded."""
    # Create sample bars for 2023
    bars_2023 = [
        DailyBar(
            date=datetime(2023, 12, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("95"),
            close=Decimal("102"),
            volume=1000000,
            adjusted_close=Decimal("102"),
        )
    ]
    
    # Create sample bars for 2024
    bars_2024 = [
        DailyBar(
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("95"),
            close=Decimal("102"),
            volume=1000000,
            adjusted_close=Decimal("102"),
        )
    ]

    # Save 2023 data (so it's cached)
    temp_data_store.save_bars("TEST", bars_2023)

    # Configure provider to return 2024 data (for missing year)
    mock_provider.fetch_daily_bars.return_value = bars_2023 + bars_2024
    temp_data_store.data_provider = mock_provider

    # Request data spanning both years
    start_date = datetime(2023, 12, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    # Load bars (should download missing 2024 data)
    bars = temp_data_store.load_bars("TEST", start_date, end_date)

    # Verify provider was called (for missing 2024 data)
    mock_provider.fetch_daily_bars.assert_called_once()

    # Verify both years' data were loaded
    assert len(bars) == 2
