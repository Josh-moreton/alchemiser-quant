"""Business Unit: backtest | Status: current.

Backtest reporting module.

Provides HTML tearsheet generation using QuantStats for professional-grade
performance reports. Supports both single BacktestResult and PortfolioBacktestResult.
"""

from pathlib import Path

from the_alchemiser.shared.reporting import (
    ExtendedMetrics,
    calculate_extended_metrics,
    generate_tearsheet,
)

__all__ = [
    "ExtendedMetrics",
    "calculate_extended_metrics",
    "generate_report",
    "generate_tearsheet",
]


def generate_report(
    result: object,
    output_path: Path | str | None,
) -> str:
    """Generate HTML tearsheet from backtest result.

    Args:
        result: BacktestResult or PortfolioBacktestResult
        output_path: Path to save HTML report

    Returns:
        HTML report as string

    """
    from pathlib import Path

    import pandas as pd

    # Extract equity curve based on result type
    if hasattr(result, "equity_curve"):
        equity_df = result.equity_curve
    else:
        raise ValueError("Result object must have equity_curve attribute")

    # Get portfolio value series
    if isinstance(equity_df, pd.DataFrame) and "portfolio_value" in equity_df.columns:
        equity = equity_df["portfolio_value"]
    elif isinstance(equity_df, pd.Series):
        equity = equity_df
    else:
        raise ValueError("Could not extract equity series from result")

    # Determine title
    if hasattr(result, "config_summary"):
        config = result.config_summary
        strategy_path = config.get("strategy_path", "Portfolio")
        if strategy_path and strategy_path != "N/A":
            title = Path(str(strategy_path)).stem
        else:
            title = "Portfolio Backtest"
    else:
        title = "Backtest Results"

    return generate_tearsheet(
        equity=equity,
        output_path=output_path,
        title=title,
    )
