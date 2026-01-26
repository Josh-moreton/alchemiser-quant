"""Business Unit: shared | Status: current.

Utility functions for options hedging module.

Provides shared utilities for:
- Market data access and price fetching
- Rolling beta and correlation calculations
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from ..logging import get_logger
from .constants import DEFAULT_ETF_PRICE_FALLBACK, DEFAULT_ETF_PRICES

if TYPE_CHECKING:
    from ..config.container import ApplicationContainer

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


def get_underlying_price(container: ApplicationContainer, symbol: str) -> Decimal:
    """Get current price of underlying ETF.

    Attempts to fetch real-time price via AlpacaManager.
    Falls back to DEFAULT_ETF_PRICES on API failure or invalid data.

    Args:
        container: Application DI container for accessing AlpacaManager
        symbol: ETF symbol (QQQ, SPY, XLK, etc.)

    Returns:
        Current price from market data or fallback estimate

    Note:
        - Uses mid price (bid + ask) / 2 for fair value
        - Validates that prices are positive before using
        - Timeout protection via AlpacaManager's error handling
        - Logs price source for observability

    Examples:
        >>> container = ApplicationContainer.create_for_environment("production")
        >>> price = get_underlying_price(container, "QQQ")
        >>> print(price)  # Decimal('485.50') from live market data

    """
    try:
        # Attempt to get real-time quote via AlpacaManager
        alpaca_manager = container.infrastructure.alpaca_manager()
        quote = alpaca_manager.get_latest_quote(symbol)

        # Validate quote has valid positive prices
        # Note: QuoteModel fields are non-optional, but we check None explicitly
        # for safety. We also require positive prices to ensure valid mid-price calc.
        if quote is not None and quote.bid_price > 0 and quote.ask_price > 0:
            # Use mid price for fair value
            # Explicit Decimal type ensures proper arithmetic
            mid_price: Decimal = (quote.bid_price + quote.ask_price) / Decimal("2")
            logger.info(
                "Using real-time ETF price",
                symbol=symbol,
                price=str(mid_price),
                bid=str(quote.bid_price),
                ask=str(quote.ask_price),
                price_source="live_market_data",
            )
            return mid_price
    except Exception as e:
        logger.warning(
            "Failed to fetch real-time ETF price, using fallback",
            symbol=symbol,
            error=str(e),
            price_source="fallback",
        )

    # Fallback to hardcoded prices
    fallback_price = DEFAULT_ETF_PRICES.get(symbol, DEFAULT_ETF_PRICE_FALLBACK)
    logger.info(
        "Using fallback ETF price",
        symbol=symbol,
        price=str(fallback_price),
        price_source="fallback",
    )
    return fallback_price
