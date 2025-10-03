"""Business Unit: shared | Status: current.

Unit tests for data store.
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.backtest.models.market_data import HistoricalBar
from scripts.backtest.storage.data_store import DataStore


class TestDataStore:
    """Tests for DataStore class."""

    @pytest.fixture
    def temp_storage(self) -> Path:
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_bars(self) -> list[HistoricalBar]:
        """Create sample historical bars."""
        return [
            HistoricalBar(
                date=datetime(2024, 1, 1),
                symbol="AAPL",
                open_price=Decimal("150.00"),
                high_price=Decimal("152.00"),
                low_price=Decimal("149.00"),
                close_price=Decimal("151.00"),
                volume=1000000,
                adjusted_close=Decimal("151.00"),
            ),
            HistoricalBar(
                date=datetime(2024, 1, 2),
                symbol="AAPL",
                open_price=Decimal("151.00"),
                high_price=Decimal("153.00"),
                low_price=Decimal("150.00"),
                close_price=Decimal("152.00"),
                volume=1100000,
                adjusted_close=Decimal("152.00"),
            ),
        ]

    def test_save_and_load_bars(
        self, temp_storage: Path, sample_bars: list[HistoricalBar]
    ) -> None:
        """Test saving and loading bars."""
        store = DataStore(str(temp_storage))

        # Save bars
        store.save_bars("AAPL", sample_bars)

        # Load bars back
        loaded_bars = store.load_bars(
            "AAPL", datetime(2024, 1, 1), datetime(2024, 1, 2)
        )

        assert len(loaded_bars) == 2
        assert loaded_bars[0].symbol == "AAPL"
        assert loaded_bars[0].open_price == Decimal("150.00")
        assert loaded_bars[1].open_price == Decimal("151.00")

    def test_has_data(
        self, temp_storage: Path, sample_bars: list[HistoricalBar]
    ) -> None:
        """Test checking if data exists."""
        store = DataStore(str(temp_storage))

        # No data initially
        assert not store.has_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 2))

        # Save data
        store.save_bars("AAPL", sample_bars)

        # Data exists now
        assert store.has_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 2))

    def test_list_symbols(
        self, temp_storage: Path, sample_bars: list[HistoricalBar]
    ) -> None:
        """Test listing available symbols."""
        store = DataStore(str(temp_storage))

        # No symbols initially
        assert store.list_symbols() == []

        # Save data for multiple symbols
        store.save_bars("AAPL", sample_bars)
        
        googl_bars = [
            HistoricalBar(
                date=datetime(2024, 1, 1),
                symbol="GOOGL",
                open_price=Decimal("140.00"),
                high_price=Decimal("142.00"),
                low_price=Decimal("139.00"),
                close_price=Decimal("141.00"),
                volume=500000,
                adjusted_close=Decimal("141.00"),
            )
        ]
        store.save_bars("GOOGL", googl_bars)

        symbols = store.list_symbols()
        assert len(symbols) == 2
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    def test_clear_symbol(
        self, temp_storage: Path, sample_bars: list[HistoricalBar]
    ) -> None:
        """Test clearing symbol data."""
        store = DataStore(str(temp_storage))

        # Save data
        store.save_bars("AAPL", sample_bars)
        assert store.has_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 2))

        # Clear data
        store.clear_symbol("AAPL")
        assert not store.has_data("AAPL", datetime(2024, 1, 1), datetime(2024, 1, 2))
