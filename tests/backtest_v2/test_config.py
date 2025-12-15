"""Business Unit: backtest | Status: current.

Unit tests for BacktestConfig.

Tests configuration validation and defaults.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from the_alchemiser.backtest_v2.core.config import (
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_SLIPPAGE_BPS,
    BacktestConfig,
)


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    @pytest.fixture
    def valid_strategy_path(self, tmp_path: Path) -> Path:
        """Create a valid strategy file."""
        strategy_file = tmp_path / "test_strategy.clj"
        strategy_file.write_text("(defsymphony \"Test\" {})")
        return strategy_file

    @pytest.fixture
    def valid_data_dir(self, tmp_path: Path) -> Path:
        """Create a valid data directory."""
        data_dir = tmp_path / "historical"
        data_dir.mkdir()
        return data_dir

    def test_valid_config(self, valid_strategy_path: Path, valid_data_dir: Path) -> None:
        """Test creating valid config."""
        config = BacktestConfig(
            strategy_path=valid_strategy_path,
            start_date=datetime(2023, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 1, tzinfo=UTC),
            initial_capital=Decimal("100000"),
            data_dir=valid_data_dir,
        )

        assert config.strategy_path == valid_strategy_path
        assert config.initial_capital == Decimal("100000")
        assert config.benchmark_symbol == "SPY"

    def test_default_values(self, valid_strategy_path: Path, valid_data_dir: Path) -> None:
        """Test default values are applied."""
        config = BacktestConfig(
            strategy_path=valid_strategy_path,
            start_date=datetime(2023, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 1, tzinfo=UTC),
            data_dir=valid_data_dir,
        )

        assert config.initial_capital == DEFAULT_INITIAL_CAPITAL
        assert config.slippage_bps == DEFAULT_SLIPPAGE_BPS
        assert config.rebalance_frequency == "daily"

    def test_start_after_end_raises(
        self, valid_strategy_path: Path, valid_data_dir: Path
    ) -> None:
        """Test that start >= end raises ValueError."""
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            BacktestConfig(
                strategy_path=valid_strategy_path,
                start_date=datetime(2024, 1, 1, tzinfo=UTC),
                end_date=datetime(2023, 1, 1, tzinfo=UTC),
                data_dir=valid_data_dir,
            )

    def test_naive_start_date_raises(
        self, valid_strategy_path: Path, valid_data_dir: Path
    ) -> None:
        """Test that naive start_date raises ValueError."""
        with pytest.raises(ValueError, match="timezone-aware"):
            BacktestConfig(
                strategy_path=valid_strategy_path,
                start_date=datetime(2023, 1, 1),  # No timezone
                end_date=datetime(2024, 1, 1, tzinfo=UTC),
                data_dir=valid_data_dir,
            )

    def test_naive_end_date_raises(
        self, valid_strategy_path: Path, valid_data_dir: Path
    ) -> None:
        """Test that naive end_date raises ValueError."""
        with pytest.raises(ValueError, match="timezone-aware"):
            BacktestConfig(
                strategy_path=valid_strategy_path,
                start_date=datetime(2023, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 1),  # No timezone
                data_dir=valid_data_dir,
            )

    def test_negative_capital_raises(
        self, valid_strategy_path: Path, valid_data_dir: Path
    ) -> None:
        """Test that negative capital raises ValueError."""
        with pytest.raises(ValueError, match="initial_capital must be positive"):
            BacktestConfig(
                strategy_path=valid_strategy_path,
                start_date=datetime(2023, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 1, tzinfo=UTC),
                initial_capital=Decimal("-100"),
                data_dir=valid_data_dir,
            )

    def test_missing_strategy_raises(self, valid_data_dir: Path) -> None:
        """Test that missing strategy file raises ValueError."""
        with pytest.raises(ValueError, match="Strategy file not found"):
            BacktestConfig(
                strategy_path=Path("/nonexistent/strategy.clj"),
                start_date=datetime(2023, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 1, tzinfo=UTC),
                data_dir=valid_data_dir,
            )

    def test_missing_data_dir_raises(self, valid_strategy_path: Path) -> None:
        """Test that missing data directory raises ValueError."""
        with pytest.raises(ValueError, match="Data directory not found"):
            BacktestConfig(
                strategy_path=valid_strategy_path,
                start_date=datetime(2023, 1, 1, tzinfo=UTC),
                end_date=datetime(2024, 1, 1, tzinfo=UTC),
                data_dir=Path("/nonexistent/data"),
            )

    def test_from_dict(self, valid_strategy_path: Path, valid_data_dir: Path) -> None:
        """Test creating config from dictionary."""
        data = {
            "strategy_path": str(valid_strategy_path),
            "start_date": datetime(2023, 1, 1, tzinfo=UTC),
            "end_date": datetime(2024, 1, 1, tzinfo=UTC),
            "initial_capital": 50000,
            "data_dir": str(valid_data_dir),
            "slippage_bps": 10,
        }

        config = BacktestConfig.from_dict(data)

        assert config.initial_capital == Decimal("50000")
        assert config.slippage_bps == Decimal("10")

    def test_frozen(self, valid_strategy_path: Path, valid_data_dir: Path) -> None:
        """Test that config is immutable (frozen)."""
        config = BacktestConfig(
            strategy_path=valid_strategy_path,
            start_date=datetime(2023, 1, 1, tzinfo=UTC),
            end_date=datetime(2024, 1, 1, tzinfo=UTC),
            data_dir=valid_data_dir,
        )

        with pytest.raises(AttributeError):
            config.initial_capital = Decimal("999999")  # type: ignore
