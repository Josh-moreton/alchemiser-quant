"""Business Unit: hedge_evaluator | Status: current.

Portfolio exposure calculator for hedge sizing.

Calculates beta-adjusted portfolio exposure metrics used
to determine appropriate hedge sizing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import HEDGE_ETFS
from the_alchemiser.shared.options.utils import (
    calculate_rolling_beta,
    calculate_rolling_correlation,
)

from .sector_mapper import SectorExposure

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

logger = get_logger(__name__)


@dataclass(frozen=True)
class PortfolioExposure:
    """Portfolio exposure metrics for hedge sizing.

    Captures the key exposure metrics needed to determine
    appropriate hedge sizing and instrument selection.
    """

    nav: Decimal  # Net Asset Value (total portfolio value)
    gross_long_exposure: Decimal  # Sum of long position values
    gross_short_exposure: Decimal  # Sum of short position values (absolute)
    net_exposure: Decimal  # Long - Short
    net_exposure_ratio: Decimal  # Net / NAV (e.g., 2.0 = 2x levered long)
    beta_dollars: Decimal  # Beta-adjusted exposure in dollars
    equivalent_qqq_shares: int  # Beta dollars / QQQ price
    primary_hedge_underlying: str  # QQQ, SPY, etc.
    beta_to_spy: Decimal  # 60-day rolling beta to SPY
    beta_to_qqq: Decimal  # 60-day rolling beta to QQQ
    correlation_spy: Decimal  # 90-day correlation to SPY
    correlation_qqq: Decimal  # 90-day correlation to QQQ


class ExposureCalculator:
    """Calculates portfolio exposure metrics for hedge sizing.

    Takes portfolio positions and calculates beta-adjusted
    exposure to determine hedge sizing requirements.
    """

    def __init__(
        self,
        container: ApplicationContainer | None = None,
    ) -> None:
        """Initialize exposure calculator.

        Args:
            container: Optional DI container for accessing AlpacaManager
                for historical data. If not provided, will fall back to
                static betas from HEDGE_ETFS.

        """
        self._hedge_etfs = HEDGE_ETFS
        self._container = container

    def calculate_exposure(
        self,
        nav: Decimal,
        sector_exposures: dict[str, SectorExposure],
        primary_underlying: str,
        underlying_price: Decimal,
    ) -> PortfolioExposure:
        """Calculate portfolio exposure metrics.

        Args:
            nav: Portfolio NAV (total equity value)
            sector_exposures: Exposure by sector ETF from SectorMapper
            primary_underlying: Primary hedge underlying (QQQ, SPY)
            underlying_price: Current price of primary underlying

        Returns:
            PortfolioExposure with all metrics calculated

        """
        # Calculate gross exposures
        gross_long: Decimal = sum(
            (exp.total_value for exp in sector_exposures.values()),
            Decimal("0"),
        )
        gross_short = Decimal("0")  # Placeholder - add short detection if needed

        net_exposure = gross_long - gross_short
        net_exposure_ratio = net_exposure / nav if nav > 0 else Decimal("1")

        # Calculate beta-adjusted exposure
        beta_dollars = self._calculate_beta_dollars(sector_exposures, primary_underlying)

        # Calculate equivalent shares of primary underlying
        equivalent_shares = 0
        if underlying_price > 0:
            equivalent_shares = int(beta_dollars / underlying_price)

        # Calculate rolling betas and correlations
        beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq = (
            self._calculate_rolling_metrics(sector_exposures)
        )

        exposure = PortfolioExposure(
            nav=nav,
            gross_long_exposure=gross_long,
            gross_short_exposure=gross_short,
            net_exposure=net_exposure,
            net_exposure_ratio=net_exposure_ratio,
            beta_dollars=beta_dollars,
            equivalent_qqq_shares=equivalent_shares,
            primary_hedge_underlying=primary_underlying,
            beta_to_spy=beta_to_spy,
            beta_to_qqq=beta_to_qqq,
            correlation_spy=correlation_spy,
            correlation_qqq=correlation_qqq,
        )

        logger.info(
            "Calculated portfolio exposure",
            nav=str(nav),
            net_exposure_ratio=str(net_exposure_ratio),
            beta_dollars=str(beta_dollars),
            equivalent_shares=equivalent_shares,
            primary_underlying=primary_underlying,
        )

        return exposure

    def _calculate_beta_dollars(
        self,
        sector_exposures: dict[str, SectorExposure],
        primary_underlying: str,
    ) -> Decimal:
        """Calculate beta-adjusted dollar exposure.

        Adjusts sector exposures by their beta relative to the
        primary hedge underlying (usually SPY or QQQ).

        Args:
            sector_exposures: Exposure by sector ETF
            primary_underlying: Primary hedge ETF (QQQ, SPY)

        Returns:
            Total beta-adjusted dollar exposure

        """
        # Get beta of primary underlying to SPY (for normalization)
        primary_beta = self._get_etf_beta(primary_underlying)

        beta_dollars = Decimal("0")

        for etf, exposure in sector_exposures.items():
            # Get this sector's beta to SPY
            sector_beta = self._get_etf_beta(etf)

            # Adjust beta relative to primary underlying
            # If primary is QQQ (beta 1.15), and sector is XLF (beta 1.05),
            # relative beta = 1.05 / 1.15 = 0.91
            relative_beta = sector_beta / primary_beta if primary_beta > 0 else Decimal("1")

            # Add beta-adjusted exposure
            beta_dollars += exposure.total_value * relative_beta

        return beta_dollars

    def _get_etf_beta(self, etf_symbol: str) -> Decimal:
        """Get ETF beta to SPY.

        Args:
            etf_symbol: ETF symbol

        Returns:
            Beta value (defaults to 1.0 for unknown ETFs)

        """
        if etf_symbol in self._hedge_etfs:
            beta: Decimal = self._hedge_etfs[etf_symbol].beta_to_spy
            return beta
        # Default beta for unmapped ETFs
        return Decimal("1.0")

    # Constants for rolling metrics calculation
    # We need ~90 trading days for correlation. Since calendar days != trading days
    # (~252 trading days per year), we fetch 130 calendar days to reliably get 90+ trading days.
    _CALENDAR_DAYS_TO_FETCH = 130
    _MIN_TRADING_DAYS_REQUIRED = 90  # For 90-day correlation window
    _BETA_WINDOW = 60
    _CORRELATION_WINDOW = 90

    def _calculate_rolling_metrics(
        self,
        sector_exposures: dict[str, SectorExposure],
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Calculate rolling beta and correlation to SPY and QQQ.

        Orchestrates the rolling metrics calculation by:
        1. Fetching benchmark returns (SPY, QQQ)
        2. Building weighted portfolio returns from sector exposures
        3. Computing rolling beta (60-day) and correlation (90-day) statistics

        Args:
            sector_exposures: Exposure by sector ETF

        Returns:
            Tuple of (beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq)

        """
        # If container not available, fall back to static betas
        if self._container is None:
            logger.info("Container not available, using static betas")
            return self._static_fallback_metrics()

        try:
            # Calculate total portfolio value for weighting
            total_value = sum((exp.total_value for exp in sector_exposures.values()), Decimal("0"))

            if total_value == 0:
                logger.warning("Zero total portfolio value, cannot calculate rolling metrics")
                return self._static_fallback_metrics()

            # Fetch benchmark returns
            spy_returns, qqq_returns = self._get_benchmark_returns()
            if spy_returns is None or qqq_returns is None:
                return self._static_fallback_metrics()

            # Build weighted portfolio returns
            portfolio_returns = self._build_weighted_portfolio_returns(
                sector_exposures, total_value
            )
            if not portfolio_returns:
                return self._static_fallback_metrics()

            # Compute rolling statistics
            return self._compute_rolling_stats(portfolio_returns, spy_returns, qqq_returns)

        except Exception as e:
            logger.warning(
                "Failed to calculate rolling metrics, falling back to static betas",
                error=str(e),
            )
            return self._static_fallback_metrics()

    def _static_fallback_metrics(
        self,
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Return static fallback values for rolling metrics.

        Returns:
            Tuple of (beta_to_spy=1.0, beta_to_qqq=1.15, correlation_spy=0.0, correlation_qqq=0.0)

        """
        return (
            Decimal("1.0"),  # beta_to_spy
            Decimal("1.15"),  # beta_to_qqq (typical)
            Decimal("0.0"),  # correlation_spy (unknown)
            Decimal("0.0"),  # correlation_qqq (unknown)
        )

    def _fetch_daily_returns(self, symbol: str) -> list[Decimal]:
        """Fetch daily returns for a symbol using AlpacaManager.

        Args:
            symbol: Stock symbol (e.g., SPY, QQQ)

        Returns:
            List of daily returns as Decimals

        Raises:
            Exception: If AlpacaManager call fails

        """
        from datetime import UTC, datetime, timedelta

        if self._container is None:
            return []

        alpaca = self._container.infrastructure.alpaca_manager()

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=self._CALENDAR_DAYS_TO_FETCH)

        bars = alpaca.get_historical_bars(
            symbol,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            "1Day",
        )

        # Calculate returns from bars (uses SDK field names: open, high, low, close)
        returns: list[Decimal] = []
        for i in range(1, len(bars)):
            prev_close = Decimal(str(bars[i - 1]["close"]))
            curr_close = Decimal(str(bars[i]["close"]))
            if prev_close > 0:
                returns.append((curr_close - prev_close) / prev_close)

        logger.debug(
            "Fetched daily returns",
            symbol=symbol,
            bar_count=len(bars),
            return_count=len(returns),
        )

        return returns

    def _get_benchmark_returns(
        self,
    ) -> tuple[list[Decimal] | None, list[Decimal] | None]:
        """Fetch daily returns for SPY and QQQ benchmarks.

        Fetches enough calendar days to ensure we have sufficient trading days
        for both 60-day beta and 90-day correlation calculations.

        Returns:
            Tuple of (spy_returns, qqq_returns), or (None, None) if insufficient data

        """
        if self._container is None:
            return None, None

        logger.info("Fetching benchmark returns")
        try:
            spy_returns = self._fetch_daily_returns("SPY")
            qqq_returns = self._fetch_daily_returns("QQQ")
        except Exception as e:
            logger.error(
                "Failed to fetch benchmark returns",
                error=str(e),
            )
            return None, None

        if (
            len(spy_returns) < self._MIN_TRADING_DAYS_REQUIRED
            or len(qqq_returns) < self._MIN_TRADING_DAYS_REQUIRED
        ):
            logger.warning(
                "Insufficient benchmark returns",
                spy_count=len(spy_returns),
                qqq_count=len(qqq_returns),
                required=self._MIN_TRADING_DAYS_REQUIRED,
            )
            return None, None

        return spy_returns, qqq_returns

    def _build_weighted_portfolio_returns(
        self,
        sector_exposures: dict[str, SectorExposure],
        total_value: Decimal,
    ) -> list[Decimal]:
        """Build weighted portfolio returns from sector ETF exposures.

        Args:
            sector_exposures: Exposure by sector ETF
            total_value: Total portfolio value for weight calculation

        Returns:
            List of weighted portfolio daily returns

        """
        if self._container is None:
            return []

        portfolio_returns: list[Decimal] = []

        for sector_symbol, exposure in sector_exposures.items():
            weight = exposure.total_value / total_value

            logger.debug(
                "Fetching sector returns",
                sector=sector_symbol,
                weight=str(weight),
            )

            try:
                sector_returns = self._fetch_daily_returns(sector_symbol)

                # Initialize portfolio returns list if empty
                if not portfolio_returns:
                    portfolio_returns = [Decimal("0")] * len(sector_returns)

                # Add weighted sector returns to portfolio
                for i, ret in enumerate(sector_returns):
                    if i < len(portfolio_returns):
                        portfolio_returns[i] += ret * weight

            except Exception as sector_error:
                logger.warning(
                    "Failed to fetch sector returns, skipping",
                    sector=sector_symbol,
                    error=str(sector_error),
                )
                continue

        if not portfolio_returns:
            logger.warning("No sector returns available for portfolio calculation")

        return portfolio_returns

    def _compute_rolling_stats(
        self,
        portfolio_returns: list[Decimal],
        spy_returns: list[Decimal],
        qqq_returns: list[Decimal],
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Compute rolling beta and correlation metrics for the portfolio.

        Args:
            portfolio_returns: Weighted portfolio daily returns
            spy_returns: SPY benchmark daily returns
            qqq_returns: QQQ benchmark daily returns

        Returns:
            Tuple of (beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq)

        """
        # Calculate betas (60-day window)
        beta_to_spy = calculate_rolling_beta(
            portfolio_returns, spy_returns, window=self._BETA_WINDOW
        )
        beta_to_qqq = calculate_rolling_beta(
            portfolio_returns, qqq_returns, window=self._BETA_WINDOW
        )

        # Calculate correlations (90-day window)
        correlation_spy = calculate_rolling_correlation(
            portfolio_returns, spy_returns, window=self._CORRELATION_WINDOW
        )
        correlation_qqq = calculate_rolling_correlation(
            portfolio_returns, qqq_returns, window=self._CORRELATION_WINDOW
        )

        logger.info(
            "Calculated rolling metrics",
            beta_to_spy=str(beta_to_spy),
            beta_to_qqq=str(beta_to_qqq),
            correlation_spy=str(correlation_spy),
            correlation_qqq=str(correlation_qqq),
        )

        return beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq
