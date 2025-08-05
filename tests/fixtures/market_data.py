"""
Market data fixtures for comprehensive testing scenarios.

This module provides realistic market data for different market conditions:
- Normal market conditions
- High volatility periods
- Market crashes and recoveries
- Gap events and missing data
- Low volume periods
"""

from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def normal_market_conditions() -> pd.DataFrame:
    """Standard market data with typical volatility."""
    return generate_market_data(
        symbols=["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        volatility="normal",
    )


@pytest.fixture
def high_volatility_conditions() -> pd.DataFrame:
    """Market data with elevated volatility."""
    return generate_market_data(
        symbols=["SPY", "QQQ", "AAPL", "TSLA", "NVDA"],
        start_date="2020-02-01",
        end_date="2020-05-31",
        volatility="high",
    )


@pytest.fixture
def gap_up_scenario() -> pd.DataFrame:
    """Market data with overnight gaps."""
    base_data = normal_market_conditions()
    return inject_price_gaps(base_data, gap_sizes=[0.05, 0.10, -0.03])


@pytest.fixture
def missing_data_scenario() -> pd.DataFrame:
    """Market data with random missing bars."""
    base_data = normal_market_conditions()
    return randomly_remove_bars(base_data, removal_rate=0.02)


@pytest.fixture
def flash_crash_scenario() -> pd.DataFrame:
    """Market data simulating a flash crash event."""
    return create_flash_crash_scenario(
        base_symbol="SPY", crash_magnitude=-0.20, recovery_days=5  # 20% drop
    )


@pytest.fixture
def low_volume_scenario() -> pd.DataFrame:
    """Market data with unusually low volume."""
    base_data = normal_market_conditions()
    base_data["volume"] = base_data["volume"] * 0.1  # 10% of normal volume
    return base_data


@pytest.fixture
def trending_market() -> pd.DataFrame:
    """Market data with strong upward trend."""
    return generate_trending_market(
        symbols=["SPY", "QQQ"],
        trend_direction="up",
        trend_strength=0.0008,  # 0.08% daily drift
        duration_days=252,
    )


@pytest.fixture
def sideways_market() -> pd.DataFrame:
    """Market data with sideways movement (high chop)."""
    return generate_sideways_market(
        symbols=["SPY", "QQQ"], volatility=0.015, duration_days=126  # 1.5% daily volatility
    )


def generate_market_data(
    symbols: list[str], start_date: str, end_date: str, volatility: str = "normal"
) -> pd.DataFrame:
    """Generate realistic market data for given parameters."""
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    date_range = date_range[date_range.dayofweek < 5]  # Remove weekends

    volatility_map = {
        "low": 0.008,  # 0.8% daily
        "normal": 0.015,  # 1.5% daily
        "high": 0.035,  # 3.5% daily
        "extreme": 0.065,  # 6.5% daily
    }

    daily_vol = volatility_map.get(volatility, 0.015)

    data = []
    for symbol in symbols:
        base_price = get_symbol_base_price(symbol)
        current_price = base_price

        for date in date_range:
            # Generate realistic intraday movement
            daily_return = np.random.normal(0, daily_vol)

            # Add some autocorrelation for realism
            if len(data) > 0 and data[-1]["symbol"] == symbol:
                prev_return = (data[-1]["close"] - data[-1]["open"]) / data[-1]["open"]
                daily_return += 0.1 * prev_return  # 10% autocorrelation

            open_price = current_price
            close_price = open_price * (1 + daily_return)

            # Generate realistic OHLC with proper relationships
            intraday_high = max(open_price, close_price) * (
                1 + abs(np.random.normal(0, daily_vol * 0.3))
            )
            intraday_low = min(open_price, close_price) * (
                1 - abs(np.random.normal(0, daily_vol * 0.3))
            )

            # Generate volume with some randomness
            base_volume = get_symbol_base_volume(symbol)
            volume_multiplier = np.random.lognormal(0, 0.5)  # Log-normal for realistic distribution
            volume = int(base_volume * volume_multiplier)

            bar = {
                "timestamp": date,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(intraday_high, 2),
                "low": round(intraday_low, 2),
                "close": round(close_price, 2),
                "volume": volume,
            }
            data.append(bar)
            current_price = close_price

    return pd.DataFrame(data)


def inject_price_gaps(data: pd.DataFrame, gap_sizes: list[float]) -> pd.DataFrame:
    """Inject overnight price gaps into market data."""
    modified_data = data.copy()

    for symbol in data["symbol"].unique():
        symbol_data = modified_data[modified_data["symbol"] == symbol].copy()

        # Randomly select dates for gaps
        gap_indices = np.random.choice(
            range(1, len(symbol_data)),
            size=min(len(gap_sizes), len(symbol_data) - 1),
            replace=False,
        )

        for i, gap_size in enumerate(gap_sizes):
            if i < len(gap_indices):
                idx = symbol_data.index[gap_indices[i]]
                gap_multiplier = 1 + gap_size

                # Apply gap to open, high, low, close
                symbol_data.loc[idx, "open"] *= gap_multiplier
                symbol_data.loc[idx, "high"] *= gap_multiplier
                symbol_data.loc[idx, "low"] *= gap_multiplier
                symbol_data.loc[idx, "close"] *= gap_multiplier

                # Increase volume on gap days
                symbol_data.loc[idx, "volume"] *= 2

        # Update the main dataframe
        modified_data.update(symbol_data)

    return modified_data


def randomly_remove_bars(data: pd.DataFrame, removal_rate: float = 0.02) -> pd.DataFrame:
    """Randomly remove bars to simulate missing data."""
    total_rows = len(data)
    rows_to_remove = int(total_rows * removal_rate)

    indices_to_remove = np.random.choice(data.index, size=rows_to_remove, replace=False)
    return data.drop(indices_to_remove).reset_index(drop=True)


def create_flash_crash_scenario(
    base_symbol: str = "SPY", crash_magnitude: float = -0.20, recovery_days: int = 5
) -> pd.DataFrame:
    """Create a flash crash scenario for testing."""
    # Start with normal data
    normal_data = generate_market_data([base_symbol], "2024-01-01", "2024-01-31", "normal")

    # Find middle point for crash
    crash_day_idx = len(normal_data) // 2

    # Apply crash
    crash_multiplier = 1 + crash_magnitude
    normal_data.loc[crash_day_idx, "low"] *= crash_multiplier
    normal_data.loc[crash_day_idx, "close"] *= 1 + crash_magnitude * 0.5  # Partial recovery
    normal_data.loc[crash_day_idx, "volume"] *= 10  # Massive volume spike

    # Apply gradual recovery over next few days
    recovery_per_day = abs(crash_magnitude) / recovery_days
    for i in range(1, recovery_days + 1):
        if crash_day_idx + i < len(normal_data):
            recovery_factor = 1 + (recovery_per_day * 0.5)  # Partial daily recovery
            normal_data.loc[crash_day_idx + i, "open"] *= recovery_factor
            normal_data.loc[crash_day_idx + i, "close"] *= recovery_factor
            normal_data.loc[crash_day_idx + i, "volume"] *= (
                2 - i / recovery_days
            )  # Declining volume

    return normal_data


def generate_trending_market(
    symbols: list[str],
    trend_direction: str = "up",
    trend_strength: float = 0.0008,
    duration_days: int = 252,
) -> pd.DataFrame:
    """Generate market data with strong trend."""
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=duration_days)

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    date_range = date_range[date_range.dayofweek < 5]  # Remove weekends

    trend_multiplier = 1 if trend_direction == "up" else -1
    daily_drift = trend_strength * trend_multiplier

    data = []
    for symbol in symbols:
        base_price = get_symbol_base_price(symbol)
        current_price = base_price

        for i, date in enumerate(date_range):
            # Add trend component
            trend_component = daily_drift * (1 + i * 0.001)  # Slightly accelerating trend
            daily_return = trend_component + np.random.normal(
                0, 0.012
            )  # Lower vol for trending market

            open_price = current_price
            close_price = open_price * (1 + daily_return)

            # Generate OHLC
            if daily_return > 0:  # Up day
                high_price = close_price * (1 + abs(np.random.normal(0, 0.005)))
                low_price = open_price * (1 - abs(np.random.normal(0, 0.003)))
            else:  # Down day
                high_price = open_price * (1 + abs(np.random.normal(0, 0.003)))
                low_price = close_price * (1 - abs(np.random.normal(0, 0.005)))

            volume = get_symbol_base_volume(symbol) * np.random.lognormal(0, 0.3)

            bar = {
                "timestamp": date,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": int(volume),
            }
            data.append(bar)
            current_price = close_price

    return pd.DataFrame(data)


def generate_sideways_market(
    symbols: list[str], volatility: float = 0.015, duration_days: int = 126
) -> pd.DataFrame:
    """Generate choppy, sideways market data."""
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=duration_days)

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    date_range = date_range[date_range.dayofweek < 5]  # Remove weekends

    data = []
    for symbol in symbols:
        base_price = get_symbol_base_price(symbol)
        current_price = base_price

        for _i, date in enumerate(date_range):
            # Mean reversion component - pull price back to base
            reversion_strength = 0.02
            reversion_component = (base_price - current_price) / current_price * reversion_strength

            # Random component
            random_component = np.random.normal(0, volatility)

            daily_return = reversion_component + random_component

            open_price = current_price
            close_price = open_price * (1 + daily_return)

            # Higher intraday volatility for choppy markets
            intraday_range = volatility * 1.5
            high_price = max(open_price, close_price) * (
                1 + abs(np.random.normal(0, intraday_range))
            )
            low_price = min(open_price, close_price) * (
                1 - abs(np.random.normal(0, intraday_range))
            )

            volume = get_symbol_base_volume(symbol) * np.random.lognormal(0, 0.4)

            bar = {
                "timestamp": date,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": int(volume),
            }
            data.append(bar)
            current_price = close_price

    return pd.DataFrame(data)


def get_symbol_base_price(symbol: str) -> float:
    """Get realistic base price for symbol."""
    price_map = {
        "SPY": 450.0,
        "QQQ": 380.0,
        "AAPL": 175.0,
        "MSFT": 380.0,
        "NVDA": 800.0,
        "TSLA": 250.0,
        "GOOGL": 140.0,
        "AMZN": 145.0,
        "META": 350.0,
    }
    return price_map.get(symbol, 100.0)


def get_symbol_base_volume(symbol: str) -> int:
    """Get realistic base volume for symbol."""
    volume_map = {
        "SPY": 50_000_000,
        "QQQ": 35_000_000,
        "AAPL": 45_000_000,
        "MSFT": 25_000_000,
        "NVDA": 40_000_000,
        "TSLA": 60_000_000,
        "GOOGL": 20_000_000,
        "AMZN": 25_000_000,
        "META": 15_000_000,
    }
    return volume_map.get(symbol, 1_000_000)


# Portfolio state fixtures
@pytest.fixture
def sample_portfolio_states() -> dict[str, dict[str, Any]]:
    """Collection of different portfolio states for testing."""
    return {
        "balanced_portfolio": {
            "portfolio_value": Decimal("100000.00"),
            "cash": Decimal("10000.00"),
            "positions": {
                "SPY": {"shares": 100, "avg_price": 450.0, "market_value": Decimal("45000.00")},
                "QQQ": {"shares": 50, "avg_price": 380.0, "market_value": Decimal("19000.00")},
                "AAPL": {"shares": 100, "avg_price": 175.0, "market_value": Decimal("17500.00")},
                "NVDA": {"shares": 10, "avg_price": 800.0, "market_value": Decimal("8000.00")},
            },
            "allocations": {"SPY": 0.45, "QQQ": 0.19, "AAPL": 0.175, "NVDA": 0.08, "CASH": 0.10},
            "timestamp": pd.Timestamp.now(),
        },
        "concentrated_portfolio": {
            "portfolio_value": Decimal("50000.00"),
            "cash": Decimal("5000.00"),
            "positions": {
                "NVDA": {"shares": 50, "avg_price": 800.0, "market_value": Decimal("40000.00")},
                "TSLA": {"shares": 20, "avg_price": 250.0, "market_value": Decimal("5000.00")},
            },
            "allocations": {"NVDA": 0.80, "TSLA": 0.10, "CASH": 0.10},
            "timestamp": pd.Timestamp.now(),
        },
        "cash_heavy_portfolio": {
            "portfolio_value": Decimal("75000.00"),
            "cash": Decimal("60000.00"),
            "positions": {
                "SPY": {"shares": 33, "avg_price": 450.0, "market_value": Decimal("15000.00")},
            },
            "allocations": {"SPY": 0.20, "CASH": 0.80},
            "timestamp": pd.Timestamp.now(),
        },
    }
