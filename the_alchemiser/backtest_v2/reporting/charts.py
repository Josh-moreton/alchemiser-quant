"""Business Unit: backtest | Status: current.

Chart generation for backtest reports.

Uses matplotlib to create visualizations of backtest results including
equity curves, drawdown charts, and monthly returns heatmaps.
"""

from __future__ import annotations

import base64
import calendar
import io
import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from the_alchemiser.backtest_v2.core.result import BacktestResult

# Import matplotlib with Agg backend for headless operation
import matplotlib
from matplotlib.ticker import FuncFormatter

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def _fig_to_base64(fig: Figure) -> str:
    """Convert matplotlib figure to base64 encoded PNG.

    Args:
        fig: Matplotlib figure

    Returns:
        Base64 encoded PNG string

    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return img_base64


def _fig_to_bytes(fig: Figure) -> bytes:
    """Convert matplotlib figure to PNG bytes.

    Args:
        fig: Matplotlib figure

    Returns:
        PNG bytes

    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    data = buf.read()
    buf.close()
    plt.close(fig)
    return data


def create_equity_chart(
    result: BacktestResult,
    *,
    as_base64: bool = True,
) -> str | bytes:
    """Create equity curve chart comparing strategy vs benchmark.

    Args:
        result: Backtest result containing equity and benchmark curves
        as_base64: If True, return base64 string; otherwise return bytes

    Returns:
        Base64 encoded PNG string or PNG bytes

    """
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot strategy equity curve
    if not result.equity_curve.empty:
        dates = result.equity_curve.index
        values = result.equity_curve["portfolio_value"].astype(float)
        ax.plot(dates, values, label="Strategy", color="#2E86AB", linewidth=2)

    # Plot benchmark curve
    if not result.benchmark_curve.empty:
        bench_dates = result.benchmark_curve.index
        bench_values = result.benchmark_curve["close"].astype(float)
        ax.plot(
            bench_dates,
            bench_values,
            label="SPY Benchmark",
            color="#A23B72",
            linewidth=1.5,
            linestyle="--",
        )

    ax.set_title("Portfolio Value Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Portfolio Value ($)", fontsize=11)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(visible=True, alpha=0.3)

    # Format y-axis with dollar signs
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"${x:,.0f}"))

    # Rotate x-axis labels
    plt.xticks(rotation=45)
    fig.tight_layout()

    if as_base64:
        return _fig_to_base64(fig)
    return _fig_to_bytes(fig)


def create_drawdown_chart(
    result: BacktestResult,
    *,
    as_base64: bool = True,
) -> str | bytes:
    """Create drawdown chart showing peak-to-trough declines.

    Args:
        result: Backtest result containing equity curve
        as_base64: If True, return base64 string; otherwise return bytes

    Returns:
        Base64 encoded PNG string or PNG bytes

    """
    fig, ax = plt.subplots(figsize=(12, 4))

    if not result.equity_curve.empty:
        values = result.equity_curve["portfolio_value"].astype(float)
        cumulative_max = values.cummax()
        drawdown = (values - cumulative_max) / cumulative_max * 100  # As percentage

        dates = result.equity_curve.index
        ax.fill_between(dates, drawdown, 0, color="#E74C3C", alpha=0.6)
        ax.plot(dates, drawdown, color="#C0392B", linewidth=1)

    ax.set_title("Drawdown", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Drawdown (%)", fontsize=11)
    ax.grid(visible=True, alpha=0.3)

    # Add horizontal line at max drawdown
    max_dd = float(result.metrics.max_drawdown) * 100
    ax.axhline(
        y=-max_dd, color="#8B0000", linestyle="--", linewidth=1, label=f"Max DD: {max_dd:.1f}%"
    )
    ax.legend(loc="lower left", fontsize=10)

    plt.xticks(rotation=45)
    fig.tight_layout()

    if as_base64:
        return _fig_to_base64(fig)
    return _fig_to_bytes(fig)


def create_monthly_returns_heatmap(
    result: BacktestResult,
    *,
    as_base64: bool = True,
) -> str | bytes:
    """Create monthly returns heatmap.

    Args:
        result: Backtest result containing equity curve
        as_base64: If True, return base64 string; otherwise return bytes

    Returns:
        Base64 encoded PNG string or PNG bytes

    """
    fig, ax = plt.subplots(figsize=(12, 6))

    if result.equity_curve.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=14)
        if as_base64:
            return _fig_to_base64(fig)
        return _fig_to_bytes(fig)

    # Calculate monthly returns
    values = result.equity_curve["portfolio_value"].astype(float)
    monthly = values.resample("ME").last()
    monthly_returns = monthly.pct_change().dropna() * 100  # As percentage

    # Create pivot table for heatmap
    if len(monthly_returns) == 0:
        ax.text(
            0.5, 0.5, "Insufficient data for monthly returns", ha="center", va="center", fontsize=14
        )
        if as_base64:
            return _fig_to_base64(fig)
        return _fig_to_bytes(fig)

    # Build monthly returns matrix
    years = sorted(set(monthly_returns.index.year))
    months = list(range(1, 13))

    data = np.full((len(years), 12), np.nan)
    for idx, val in monthly_returns.items():
        year_idx = years.index(idx.year)
        month_idx = idx.month - 1
        data[year_idx, month_idx] = val

    # Create heatmap
    cmap = matplotlib.colormaps["RdYlGn"]
    im = ax.imshow(data, cmap=cmap, aspect="auto", vmin=-10, vmax=10)

    # Set ticks
    ax.set_xticks(range(12))
    ax.set_xticklabels([calendar.month_abbr[m] for m in months])
    ax.set_yticks(range(len(years)))
    ax.set_yticklabels(years)

    # Add text annotations
    for i in range(len(years)):
        for j in range(12):
            val = data[i, j]
            if not np.isnan(val):
                color = "white" if abs(val) > 5 else "black"
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center", color=color, fontsize=9)

    ax.set_title("Monthly Returns (%)", fontsize=14, fontweight="bold")

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Return (%)", fontsize=11)

    fig.tight_layout()

    if as_base64:
        return _fig_to_base64(fig)
    return _fig_to_bytes(fig)


def create_rolling_sharpe_chart(
    result: BacktestResult,
    window: int = 63,  # ~3 months
    *,
    as_base64: bool = True,
) -> str | bytes:
    """Create rolling Sharpe ratio chart.

    Args:
        result: Backtest result containing equity curve
        window: Rolling window size in trading days (default: 63 ~3 months)
        as_base64: If True, return base64 string; otherwise return bytes

    Returns:
        Base64 encoded PNG string or PNG bytes

    """
    fig, ax = plt.subplots(figsize=(12, 4))

    if result.equity_curve.empty or len(result.equity_curve) < window:
        ax.text(
            0.5, 0.5, "Insufficient data for rolling Sharpe", ha="center", va="center", fontsize=14
        )
        if as_base64:
            return _fig_to_base64(fig)
        return _fig_to_bytes(fig)

    values = result.equity_curve["portfolio_value"].astype(float)
    daily_returns = values.pct_change().dropna()

    # Calculate rolling Sharpe (annualized)
    risk_free_daily = 0.05 / 252  # 5% annual risk-free rate
    excess_returns = daily_returns - risk_free_daily

    rolling_mean = excess_returns.rolling(window).mean()
    rolling_std = daily_returns.rolling(window).std()
    rolling_sharpe = (rolling_mean / rolling_std) * math.sqrt(252)
    rolling_sharpe = rolling_sharpe.dropna()

    if len(rolling_sharpe) > 0:
        ax.plot(rolling_sharpe.index, rolling_sharpe.values, color="#2E86AB", linewidth=1.5)
        ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.8)
        ax.axhline(y=1, color="#27AE60", linestyle="--", linewidth=1, alpha=0.7, label="Sharpe = 1")
        ax.axhline(y=2, color="#F39C12", linestyle="--", linewidth=1, alpha=0.7, label="Sharpe = 2")

    ax.set_title(f"Rolling Sharpe Ratio ({window}-day window)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Sharpe Ratio", fontsize=11)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(visible=True, alpha=0.3)

    plt.xticks(rotation=45)
    fig.tight_layout()

    if as_base64:
        return _fig_to_base64(fig)
    return _fig_to_bytes(fig)


def create_trade_distribution_chart(
    result: BacktestResult,
    *,
    as_base64: bool = True,
) -> str | bytes:
    """Create trade value distribution histogram.

    Args:
        result: Backtest result containing trades
        as_base64: If True, return base64 string; otherwise return bytes

    Returns:
        Base64 encoded PNG string or PNG bytes

    """
    fig, ax = plt.subplots(figsize=(10, 5))

    if not result.trades:
        ax.text(0.5, 0.5, "No trades to display", ha="center", va="center", fontsize=14)
        if as_base64:
            return _fig_to_base64(fig)
        return _fig_to_bytes(fig)

    # Extract trade values
    trade_values = [float(t.value) for t in result.trades]

    ax.hist(trade_values, bins=30, color="#2E86AB", edgecolor="white", alpha=0.8)
    ax.set_title("Trade Value Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Trade Value ($)", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.grid(visible=True, alpha=0.3, axis="y")

    # Add statistics
    mean_val = float(np.mean(trade_values))
    median_val = float(np.median(trade_values))
    ax.axvline(
        mean_val, color="#E74C3C", linestyle="--", linewidth=2, label=f"Mean: ${mean_val:,.0f}"
    )
    ax.axvline(
        median_val,
        color="#27AE60",
        linestyle="--",
        linewidth=2,
        label=f"Median: ${median_val:,.0f}",
    )
    ax.legend(loc="upper right", fontsize=10)

    fig.tight_layout()

    if as_base64:
        return _fig_to_base64(fig)
    return _fig_to_bytes(fig)
