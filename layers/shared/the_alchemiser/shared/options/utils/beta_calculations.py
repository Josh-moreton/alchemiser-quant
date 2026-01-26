"""Business Unit: shared | Status: current.

Beta and correlation calculation utilities for options hedging.

Provides statistical calculations for:
- Rolling beta (covariance/variance)
- Rolling correlation
"""

from __future__ import annotations

from decimal import Decimal

from ...logging import get_logger

logger = get_logger(__name__)


def calculate_rolling_beta(
    portfolio_returns: list[Decimal],
    benchmark_returns: list[Decimal],
    window: int = 60,
) -> Decimal:
    """Calculate rolling beta using covariance/variance.

    Beta measures the sensitivity of portfolio returns to benchmark returns.
    Formula: beta = covariance(portfolio, benchmark) / variance(benchmark)

    Args:
        portfolio_returns: List of portfolio daily returns
        benchmark_returns: List of benchmark daily returns (must align with portfolio)
        window: Number of days to use for calculation (default: 60)

    Returns:
        Beta value (Decimal). Returns 1.0 if insufficient data or variance is zero.

    """
    # Validate inputs
    if len(portfolio_returns) < window or len(benchmark_returns) < window:
        logger.warning(
            "Insufficient returns for beta calculation",
            portfolio_count=len(portfolio_returns),
            benchmark_count=len(benchmark_returns),
            required_window=window,
        )
        return Decimal("1.0")

    if len(portfolio_returns) != len(benchmark_returns):
        logger.warning(
            "Mismatched return lengths",
            portfolio_count=len(portfolio_returns),
            benchmark_count=len(benchmark_returns),
        )
        # Use the shorter length
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        portfolio_returns = portfolio_returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]

    # Take the most recent 'window' days
    portfolio_window = portfolio_returns[-window:]
    benchmark_window = benchmark_returns[-window:]

    # Calculate means
    portfolio_mean = sum(portfolio_window) / Decimal(str(window))
    benchmark_mean = sum(benchmark_window) / Decimal(str(window))

    # Calculate covariance
    covariance = Decimal("0")
    for i in range(window):
        portfolio_dev = portfolio_window[i] - portfolio_mean
        benchmark_dev = benchmark_window[i] - benchmark_mean
        covariance += portfolio_dev * benchmark_dev
    covariance /= Decimal(str(window))

    # Calculate benchmark variance
    variance = Decimal("0")
    for i in range(window):
        benchmark_dev = benchmark_window[i] - benchmark_mean
        variance += benchmark_dev * benchmark_dev
    variance /= Decimal(str(window))

    # Calculate beta
    if variance == 0:
        logger.warning(
            "Zero variance in benchmark returns, defaulting to beta=1.0",
            window=window,
        )
        return Decimal("1.0")

    beta = covariance / variance

    logger.debug(
        "Calculated rolling beta",
        beta=str(beta),
        window=window,
        covariance=str(covariance),
        variance=str(variance),
    )

    return beta


def calculate_rolling_correlation(
    portfolio_returns: list[Decimal],
    benchmark_returns: list[Decimal],
    window: int = 90,
) -> Decimal:
    """Calculate rolling correlation coefficient.

    Correlation measures the linear relationship between portfolio and benchmark returns.
    Formula: correlation = covariance / (std_dev_portfolio * std_dev_benchmark)
    Range: -1 (perfect negative) to +1 (perfect positive)

    Args:
        portfolio_returns: List of portfolio daily returns
        benchmark_returns: List of benchmark daily returns (must align with portfolio)
        window: Number of days to use for calculation (default: 90)

    Returns:
        Correlation coefficient (Decimal). Returns 0.0 if insufficient data or zero variance.

    """
    # Validate inputs
    if len(portfolio_returns) < window or len(benchmark_returns) < window:
        logger.warning(
            "Insufficient returns for correlation calculation",
            portfolio_count=len(portfolio_returns),
            benchmark_count=len(benchmark_returns),
            required_window=window,
        )
        return Decimal("0.0")

    if len(portfolio_returns) != len(benchmark_returns):
        logger.warning(
            "Mismatched return lengths",
            portfolio_count=len(portfolio_returns),
            benchmark_count=len(benchmark_returns),
        )
        # Use the shorter length
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        portfolio_returns = portfolio_returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]

    # Take the most recent 'window' days
    portfolio_window = portfolio_returns[-window:]
    benchmark_window = benchmark_returns[-window:]

    # Calculate means
    portfolio_mean = sum(portfolio_window) / Decimal(str(window))
    benchmark_mean = sum(benchmark_window) / Decimal(str(window))

    # Calculate covariance
    covariance = Decimal("0")
    for i in range(window):
        portfolio_dev = portfolio_window[i] - portfolio_mean
        benchmark_dev = benchmark_window[i] - benchmark_mean
        covariance += portfolio_dev * benchmark_dev
    covariance /= Decimal(str(window))

    # Calculate portfolio standard deviation
    portfolio_variance = Decimal("0")
    for i in range(window):
        portfolio_dev = portfolio_window[i] - portfolio_mean
        portfolio_variance += portfolio_dev * portfolio_dev
    portfolio_variance /= Decimal(str(window))
    portfolio_std = portfolio_variance.sqrt() if portfolio_variance > 0 else Decimal("0")

    # Calculate benchmark standard deviation
    benchmark_variance = Decimal("0")
    for i in range(window):
        benchmark_dev = benchmark_window[i] - benchmark_mean
        benchmark_variance += benchmark_dev * benchmark_dev
    benchmark_variance /= Decimal(str(window))
    benchmark_std = benchmark_variance.sqrt() if benchmark_variance > 0 else Decimal("0")

    # Calculate correlation
    if portfolio_std == 0 or benchmark_std == 0:
        logger.warning(
            "Zero standard deviation, cannot calculate correlation",
            window=window,
            portfolio_std=str(portfolio_std),
            benchmark_std=str(benchmark_std),
        )
        return Decimal("0.0")

    correlation = covariance / (portfolio_std * benchmark_std)

    logger.debug(
        "Calculated rolling correlation",
        correlation=str(correlation),
        window=window,
        covariance=str(covariance),
        portfolio_std=str(portfolio_std),
        benchmark_std=str(benchmark_std),
    )

    return correlation
