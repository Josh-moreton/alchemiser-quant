"""Business Unit: scripts | Status: current.

Unit tests for data storage layer.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

# Add project root to path dynamically
project_root = Path(__file__).resolve().parents[2]
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from scripts.backtest.models.market_data import DailyBar
from scripts.backtest.storage.data_store import DataStore


@pytest.fixture
def temp_data_store(tmp_path: Path) -> DataStore:
    """Create a temporary data store for testing."""
    return DataStore(base_path=str(tmp_path / "test_data"))


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


def test_data_store_initialization(temp_data_store: DataStore) -> None:
    """Test data store initialization creates directory."""
    assert temp_data_store.base_path.exists()


def test_save_and_load_bars(temp_data_store: DataStore, sample_bars: list[DailyBar]) -> None:
    """Test saving and loading bars."""
    symbol = "TEST"

    # Save bars
    temp_data_store.save_bars(symbol, sample_bars)

    # Load bars
    start_date = sample_bars[0].date
    end_date = sample_bars[-1].date
    loaded_bars = temp_data_store.load_bars(symbol, start_date, end_date)

    # Verify
    assert len(loaded_bars) == len(sample_bars)
    for orig, loaded in zip(sample_bars, loaded_bars, strict=False):
        assert loaded.date.date() == orig.date.date()
        assert loaded.open == orig.open
        assert loaded.close == orig.close


def test_get_metadata(temp_data_store: DataStore, sample_bars: list[DailyBar]) -> None:
    """Test getting metadata for stored data."""
    symbol = "TEST"

    # Initially no metadata
    metadata = temp_data_store.get_metadata(symbol)
    assert metadata is None

    # Save bars
    temp_data_store.save_bars(symbol, sample_bars)

    # Get metadata
    metadata = temp_data_store.get_metadata(symbol)
    assert metadata is not None
    assert metadata.symbol == symbol
    assert metadata.bar_count == len(sample_bars)
    assert metadata.start_date.date() == sample_bars[0].date.date()
    assert metadata.end_date.date() == sample_bars[-1].date.date()


def test_save_empty_bars(temp_data_store: DataStore) -> None:
    """Test saving empty bars list."""
    symbol = "EMPTY"
    temp_data_store.save_bars(symbol, [])

    # Should not create any files
    metadata = temp_data_store.get_metadata(symbol)
    assert metadata is None


def test_load_nonexistent_symbol(temp_data_store: DataStore) -> None:
    """Test loading bars for symbol that doesn't exist."""
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

    # Import here to avoid circular dependency
    from the_alchemiser.shared.types.exceptions import DataUnavailableError

    # Should raise DataUnavailableError since no data exists and no provider configured
    with pytest.raises(DataUnavailableError) as exc_info:
        temp_data_store.load_bars("NONEXISTENT", start_date, end_date)

    assert "NONEXISTENT" in str(exc_info.value)
    assert "No data provider configured" in str(exc_info.value)


def test_bars_organized_by_year(temp_data_store: DataStore) -> None:
    """Test that bars are organized by year in separate files."""
    symbol = "MULTI_YEAR"

    # Create bars spanning two years
    bars_2023 = [
        DailyBar(
            date=datetime(2023, 12, 28, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("105"),
            low=Decimal("95"),
            close=Decimal("102"),
            volume=1000000,
            adjusted_close=Decimal("102"),
        )
    ]
    bars_2024 = [
        DailyBar(
            date=datetime(2024, 1, 2, tzinfo=timezone.utc),
            open=Decimal("103"),
            high=Decimal("108"),
            low=Decimal("98"),
            close=Decimal("105"),
            volume=1100000,
            adjusted_close=Decimal("105"),
        )
    ]

    # Save bars
    temp_data_store.save_bars(symbol, bars_2023 + bars_2024)

    # Verify separate year files exist
    path_2023 = temp_data_store.base_path / symbol / "2023" / "daily.parquet"
    path_2024 = temp_data_store.base_path / symbol / "2024" / "daily.parquet"

    assert path_2023.exists()
    assert path_2024.exists()

    # Load all and verify
    loaded = temp_data_store.load_bars(
        symbol,
        datetime(2023, 12, 1, tzinfo=timezone.utc),
        datetime(2024, 1, 31, tzinfo=timezone.utc),
    )
    assert len(loaded) == 2
