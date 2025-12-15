"""Business Unit: backtest | Status: current.

Unit tests for BacktestMarketDataAdapter.

Tests point-in-time data access and look-ahead bias protection.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from the_alchemiser.backtest_v2.adapters.historical_market_data import (
    BacktestMarketDataAdapter,
    LookAheadBiasError,
)
from the_alchemiser.shared.value_objects.symbol import Symbol


class TestBacktestMarketDataAdapter:
    """Tests for BacktestMarketDataAdapter."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample OHLCV data."""
        dates = pd.date_range("2024-01-01", "2024-01-10", tz="UTC")
        return pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(10)],
                "High": [105.0 + i for i in range(10)],
                "Low": [95.0 + i for i in range(10)],
                "Close": [102.0 + i for i in range(10)],
                "Volume": [1000000 + i * 10000 for i in range(10)],
            },
            index=dates,
        )

    @pytest.fixture
    def mock_adapter(self, sample_data: pd.DataFrame, tmp_path: Path) -> BacktestMarketDataAdapter:
        """Create adapter with mocked data."""
        # Create mock data directory structure
        spy_dir = tmp_path / "SPY" / "2024"
        spy_dir.mkdir(parents=True)
        sample_data.to_parquet(spy_dir / "daily.parquet")

        adapter = BacktestMarketDataAdapter(
            data_dir=tmp_path,
            as_of=datetime(2024, 1, 10, tzinfo=UTC),
        )
        return adapter

    def test_initialization_requires_timezone_aware_date(self, tmp_path: Path) -> None:
        """Test that as_of must be timezone-aware."""
        with pytest.raises(ValueError, match="timezone-aware"):
            BacktestMarketDataAdapter(
                data_dir=tmp_path,
                as_of=datetime(2024, 1, 1),  # No timezone
            )

    def test_get_bars_filters_by_as_of(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that get_bars only returns data up to as_of date."""
        # Set as_of to middle of data range
        mock_adapter.set_as_of(datetime(2024, 1, 5, tzinfo=UTC))

        bars = mock_adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")

        # Should only have bars up to 2024-01-05
        assert len(bars) == 5
        assert all(bar.timestamp <= datetime(2024, 1, 5, tzinfo=UTC) for bar in bars)

    def test_get_bars_returns_chronological_order(
        self, mock_adapter: BacktestMarketDataAdapter
    ) -> None:
        """Test that bars are returned in chronological order."""
        bars = mock_adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")

        timestamps = [bar.timestamp for bar in bars]
        assert timestamps == sorted(timestamps)

    def test_get_bars_respects_period(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that period parameter limits number of bars."""
        bars = mock_adapter.get_bars(Symbol("SPY"), period="5D", timeframe="1Day")

        assert len(bars) <= 5

    def test_get_bars_returns_bar_models(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that get_bars returns proper BarModel objects."""
        bars = mock_adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")

        assert len(bars) > 0
        bar = bars[0]
        assert isinstance(bar.open, Decimal)
        assert isinstance(bar.high, Decimal)
        assert isinstance(bar.low, Decimal)
        assert isinstance(bar.close, Decimal)
        assert isinstance(bar.volume, int)

    def test_get_close_price_on_date_raises_for_future_date(
        self, mock_adapter: BacktestMarketDataAdapter
    ) -> None:
        """Test that requesting future data raises LookAheadBiasError."""
        mock_adapter.set_as_of(datetime(2024, 1, 5, tzinfo=UTC))

        with pytest.raises(LookAheadBiasError) as exc_info:
            mock_adapter.get_close_price_on_date("SPY", datetime(2024, 1, 8, tzinfo=UTC))

        assert exc_info.value.as_of == datetime(2024, 1, 5, tzinfo=UTC)

    def test_get_close_price_on_date_returns_price_for_valid_date(
        self, mock_adapter: BacktestMarketDataAdapter
    ) -> None:
        """Test that get_close_price_on_date returns price for historical date."""
        mock_adapter.set_as_of(datetime(2024, 1, 10, tzinfo=UTC))

        price = mock_adapter.get_close_price_on_date("SPY", datetime(2024, 1, 5, tzinfo=UTC))

        assert price is not None
        assert isinstance(price, float)

    def test_get_mid_price_returns_close(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that get_mid_price returns the close price."""
        mid = mock_adapter.get_mid_price(Symbol("SPY"))

        assert mid is not None
        assert isinstance(mid, float)

    def test_get_latest_quote_returns_simulated_quote(
        self, mock_adapter: BacktestMarketDataAdapter
    ) -> None:
        """Test that get_latest_quote returns a simulated quote."""
        quote = mock_adapter.get_latest_quote(Symbol("SPY"))

        assert quote is not None
        assert quote.bid_price < quote.ask_price
        assert quote.symbol == "SPY"

    def test_set_as_of_updates_filter(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that set_as_of updates the data filter."""
        # Initially at 2024-01-10
        bars_full = mock_adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")

        # Move to 2024-01-05
        mock_adapter.set_as_of(datetime(2024, 1, 5, tzinfo=UTC))
        bars_filtered = mock_adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")

        assert len(bars_filtered) < len(bars_full)

    def test_get_available_symbols(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that get_available_symbols returns list of symbols."""
        symbols = mock_adapter.get_available_symbols()

        assert "SPY" in symbols

    def test_get_date_range(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that get_date_range returns date range for symbol."""
        date_range = mock_adapter.get_date_range("SPY")

        assert date_range is not None
        start, end = date_range
        assert start < end

    def test_parse_period_years(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test period parsing for years."""
        assert mock_adapter._parse_period("1Y") == 252
        assert mock_adapter._parse_period("2Y") == 504

    def test_parse_period_months(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test period parsing for months."""
        assert mock_adapter._parse_period("1M") == 21
        assert mock_adapter._parse_period("6M") == 126

    def test_parse_period_days(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test period parsing for days."""
        assert mock_adapter._parse_period("30D") == 30
        assert mock_adapter._parse_period("90D") == 90

    def test_parse_period_invalid(self, mock_adapter: BacktestMarketDataAdapter) -> None:
        """Test that invalid period raises ValueError."""
        with pytest.raises(ValueError, match="Invalid period"):
            mock_adapter._parse_period("invalid")
