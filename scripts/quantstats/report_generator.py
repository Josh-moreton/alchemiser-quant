"""Business Unit: scripts | Status: current.

QuantStats tearsheet report generation wrapper.

Generates professional HTML tearsheet reports with benchmark comparison
using the QuantStats library.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import quantstats as qs

logger = logging.getLogger(__name__)

# Default configuration
RISK_FREE_RATE = 0.05  # 5% annual
TRADING_DAYS_PER_YEAR = 252


@dataclass
class ReportResult:
    """Result of report generation."""

    success: bool
    html_content: str | None
    error_message: str | None
    report_name: str
    data_points: int


class ReportGenerator:
    """Generates QuantStats tearsheet reports.

    Wraps the QuantStats library to produce HTML tearsheet reports
    with optional benchmark comparison.
    """

    def __init__(
        self,
        risk_free_rate: float = RISK_FREE_RATE,
        periods_per_year: int = TRADING_DAYS_PER_YEAR,
    ) -> None:
        """Initialize the report generator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino
            periods_per_year: Trading periods per year (252 for daily)

        """
        self._rf = risk_free_rate
        self._periods = periods_per_year
        logger.info(f"ReportGenerator initialized (rf={risk_free_rate})")

    def generate_tearsheet(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series | None = None,
        title: str = "Portfolio Performance",
        output_path: Path | str | None = None,
    ) -> ReportResult:
        """Generate a QuantStats HTML tearsheet.

        Args:
            returns: Daily returns series (decimals, e.g., 0.01 = 1%)
            benchmark_returns: Optional benchmark returns for comparison
            title: Report title
            output_path: Optional file path to save report

        Returns:
            ReportResult with success status and HTML content

        """
        report_name = title.replace(" ", "_").lower()

        # Validate input
        if returns.empty:
            return ReportResult(
                success=False,
                html_content=None,
                error_message="Cannot generate tearsheet from empty returns series",
                report_name=report_name,
                data_points=0,
            )

        if len(returns) < 5:
            return ReportResult(
                success=False,
                html_content=None,
                error_message=f"Returns series too short ({len(returns)} points, need >= 5)",
                report_name=report_name,
                data_points=len(returns),
            )

        # Ensure timezone-naive index (QuantStats requirement)
        returns = self._ensure_tz_naive(returns)
        if benchmark_returns is not None:
            benchmark_returns = self._ensure_tz_naive(benchmark_returns)

        logger.info(
            f"Generating tearsheet '{title}' with {len(returns)} data points, "
            f"benchmark: {benchmark_returns is not None}"
        )

        try:
            # Generate HTML to string buffer
            output = io.StringIO()

            if benchmark_returns is not None and not benchmark_returns.empty:
                qs.reports.html(
                    returns,
                    benchmark=benchmark_returns,
                    output=output,
                    title=title,
                    rf=self._rf,
                    periods_per_year=self._periods,
                )
            else:
                # No benchmark - generate without comparison
                qs.reports.html(
                    returns,
                    output=output,
                    title=title,
                    rf=self._rf,
                    periods_per_year=self._periods,
                )

            html_content = output.getvalue()
            output.close()

            # Optionally save to file
            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(html_content, encoding="utf-8")
                logger.info(f"Tearsheet saved to {path}")

            return ReportResult(
                success=True,
                html_content=html_content,
                error_message=None,
                report_name=report_name,
                data_points=len(returns),
            )

        except Exception as e:
            logger.error(f"Failed to generate tearsheet '{title}': {e}")
            return ReportResult(
                success=False,
                html_content=None,
                error_message=str(e),
                report_name=report_name,
                data_points=len(returns),
            )

    def generate_strategy_report(
        self,
        returns: pd.Series,
        strategy_name: str,
        benchmark_returns: pd.Series | None = None,
        output_path: Path | str | None = None,
    ) -> ReportResult:
        """Generate tearsheet for a specific strategy.

        Args:
            returns: Strategy daily returns
            strategy_name: Name of the strategy
            benchmark_returns: Optional SPY benchmark returns
            output_path: Optional file path to save report

        Returns:
            ReportResult with success status and HTML content

        """
        title = f"{strategy_name} Strategy Performance"
        return self.generate_tearsheet(
            returns=returns,
            benchmark_returns=benchmark_returns,
            title=title,
            output_path=output_path,
        )

    def generate_portfolio_report(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series | None = None,
        output_path: Path | str | None = None,
    ) -> ReportResult:
        """Generate tearsheet for the combined portfolio.

        Args:
            returns: Portfolio daily returns
            benchmark_returns: Optional SPY benchmark returns
            output_path: Optional file path to save report

        Returns:
            ReportResult with success status and HTML content

        """
        title = "Alchemiser Portfolio Performance"
        return self.generate_tearsheet(
            returns=returns,
            benchmark_returns=benchmark_returns,
            title=title,
            output_path=output_path,
        )

    def get_metrics_snapshot(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series | None = None,
    ) -> dict[str, float]:
        """Get key metrics without generating full report.

        Useful for logging or quick performance checks.

        Args:
            returns: Daily returns series
            benchmark_returns: Optional benchmark for comparison

        Returns:
            Dictionary of key performance metrics

        """
        if returns.empty or len(returns) < 2:
            return {}

        returns = self._ensure_tz_naive(returns)

        try:
            # Get QuantStats metrics
            metrics = qs.stats.metrics(
                returns,
                benchmark=benchmark_returns,
                rf=self._rf,
                display=False,
            )

            # Convert to dict with float values
            result: dict[str, float] = {}
            if isinstance(metrics, pd.DataFrame):
                for idx in metrics.index:
                    val = metrics.loc[idx, "Strategy"]
                    if pd.notna(val):
                        try:
                            result[str(idx)] = float(val)
                        except (ValueError, TypeError):
                            pass

            return result

        except Exception as e:
            logger.error(f"Failed to get metrics snapshot: {e}")
            return {}

    def _ensure_tz_naive(self, series: pd.Series) -> pd.Series:
        """Ensure series has timezone-naive datetime index.

        Args:
            series: Series with datetime index

        Returns:
            Series with timezone-naive index

        """
        if series.index.tz is not None:
            series = series.copy()
            series.index = series.index.tz_localize(None)
        return series


def generate_tearsheet_html(
    returns: pd.Series,
    benchmark_returns: pd.Series | None = None,
    title: str = "Portfolio Performance",
) -> str | None:
    """Convenience function to generate tearsheet HTML.

    Args:
        returns: Daily returns series
        benchmark_returns: Optional benchmark returns
        title: Report title

    Returns:
        HTML content string or None on failure

    """
    generator = ReportGenerator()
    result = generator.generate_tearsheet(
        returns=returns,
        benchmark_returns=benchmark_returns,
        title=title,
    )
    return result.html_content if result.success else None
