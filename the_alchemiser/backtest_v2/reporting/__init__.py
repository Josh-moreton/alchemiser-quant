"""Business Unit: backtest | Status: current.

Backtest reporting module.

Provides HTML and PDF report generation with charts and tables for backtest results.
Supports both single BacktestResult and PortfolioBacktestResult.
"""

from the_alchemiser.backtest_v2.reporting.charts import (
    create_drawdown_chart,
    create_equity_chart,
    create_monthly_returns_heatmap,
    create_rolling_sharpe_chart,
)
from the_alchemiser.backtest_v2.reporting.html_report import (
    generate_html_report,
    generate_portfolio_html_report,
    generate_report,
)
from the_alchemiser.backtest_v2.reporting.pdf_report import generate_pdf_report

__all__ = [
    "create_drawdown_chart",
    "create_equity_chart",
    "create_monthly_returns_heatmap",
    "create_rolling_sharpe_chart",
    "generate_html_report",
    "generate_pdf_report",
    "generate_portfolio_html_report",
    "generate_report",
]
