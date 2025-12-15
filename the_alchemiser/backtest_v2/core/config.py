"""Business Unit: backtest | Status: current.

Backtest configuration data transfer object.

Defines immutable configuration for backtest runs including strategy path,
date range, capital, and simulation parameters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

# Default slippage and commission models (based on Alpaca)
DEFAULT_SLIPPAGE_BPS: Final[Decimal] = Decimal("5")  # 0.05% = 5 basis points
DEFAULT_COMMISSION_PER_SHARE: Final[Decimal] = Decimal("0")  # Alpaca is commission-free
DEFAULT_INITIAL_CAPITAL: Final[Decimal] = Decimal("100000")


@dataclass(frozen=True)
class BacktestConfig:
    """Immutable configuration for a backtest run.

    Defines all parameters needed to execute a backtest including strategy,
    date range, capital, and cost models.

    Attributes:
        strategy_path: Path to .clj strategy file
        start_date: Backtest start date (inclusive)
        end_date: Backtest end date (inclusive)
        initial_capital: Starting portfolio value
        data_dir: Path to historical data directory
        slippage_bps: Slippage in basis points (default: 5 = 0.05%)
        commission_per_share: Commission per share traded (default: 0)
        benchmark_symbol: Benchmark for comparison (always SPY)
        rebalance_frequency: Rebalance frequency (always 'daily')
        auto_fetch_missing: Automatically fetch missing symbol data (default: False)
        auto_fetch_lookback_days: Lookback days for auto-fetch (default: 600)

    Example:
        >>> config = BacktestConfig(
        ...     strategy_path=Path("strategies/core/main.clj"),
        ...     start_date=datetime(2023, 1, 1, tzinfo=UTC),
        ...     end_date=datetime(2024, 1, 1, tzinfo=UTC),
        ...     initial_capital=Decimal("100000"),
        ...     auto_fetch_missing=True,
        ... )

    """

    strategy_path: Path
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL
    data_dir: Path = field(default_factory=lambda: Path("data/historical"))
    slippage_bps: Decimal = DEFAULT_SLIPPAGE_BPS
    commission_per_share: Decimal = DEFAULT_COMMISSION_PER_SHARE
    benchmark_symbol: str = "SPY"
    rebalance_frequency: str = "daily"
    auto_fetch_missing: bool = False
    auto_fetch_lookback_days: int = 600

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate timezone-awareness first (before comparison)
        if self.start_date.tzinfo is None:
            raise ValueError("start_date must be timezone-aware")

        if self.end_date.tzinfo is None:
            raise ValueError("end_date must be timezone-aware")

        # Validate dates
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")

        # Validate capital
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

        # Validate strategy file exists
        if not self.strategy_path.exists():
            raise ValueError(f"Strategy file not found: {self.strategy_path}")

        # Validate data directory exists
        if not self.data_dir.exists():
            raise ValueError(f"Data directory not found: {self.data_dir}")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> BacktestConfig:
        """Create configuration from dictionary.

        Args:
            data: Dictionary with configuration values

        Returns:
            BacktestConfig instance

        """
        return cls(
            strategy_path=Path(str(data["strategy_path"])),
            start_date=data["start_date"],  # type: ignore[arg-type]
            end_date=data["end_date"],  # type: ignore[arg-type]
            initial_capital=Decimal(str(data.get("initial_capital", DEFAULT_INITIAL_CAPITAL))),
            data_dir=Path(str(data.get("data_dir", "data/historical"))),
            slippage_bps=Decimal(str(data.get("slippage_bps", DEFAULT_SLIPPAGE_BPS))),
            commission_per_share=Decimal(
                str(data.get("commission_per_share", DEFAULT_COMMISSION_PER_SHARE))
            ),
            benchmark_symbol=str(data.get("benchmark_symbol", "SPY")),
            auto_fetch_missing=bool(data.get("auto_fetch_missing", False)),
            auto_fetch_lookback_days=int(data.get("auto_fetch_lookback_days", 600)),
        )
