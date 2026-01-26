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
from the_alchemiser.shared.options.utils.beta_calculations import (
    calculate_rolling_beta,
    calculate_rolling_correlation,
)

from .sector_mapper import SectorExposure

if TYPE_CHECKING:
    from the_alchemiser.shared.options.adapters.historical_data_service import (
        HistoricalDataService,
    )

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
        historical_data_service: HistoricalDataService | None = None,
    ) -> None:
        """Initialize exposure calculator.

        Args:
            historical_data_service: Optional service for fetching historical data
                for rolling beta/correlation calculations. If not provided, will
                fall back to static betas from HEDGE_ETFS.

        """
        self._hedge_etfs = HEDGE_ETFS
        self._historical_data_service = historical_data_service

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

    def _calculate_rolling_metrics(
        self,
        sector_exposures: dict[str, SectorExposure],
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Calculate rolling beta and correlation to SPY and QQQ.

        Args:
            sector_exposures: Exposure by sector ETF

        Returns:
            Tuple of (beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq)

        """
        # If historical data service not available, fall back to static betas
        if self._historical_data_service is None:
            logger.info("Historical data service not available, using static betas")
            # Return static values from first sector (or defaults)
            return (
                Decimal("1.0"),  # beta_to_spy
                Decimal("1.15"),  # beta_to_qqq (typical)
                Decimal("0.0"),  # correlation_spy (unknown)
                Decimal("0.0"),  # correlation_qqq (unknown)
            )

        try:
            # Calculate portfolio weighted returns
            # For simplicity, we'll use the largest sector as proxy
            # In production, this should weight returns by sector exposure
            largest_sector = max(
                sector_exposures.items(),
                key=lambda x: x[1].total_value,
                default=("QQQ", SectorExposure(total_value=Decimal("0"), position_count=0)),
            )[0]

            logger.info("Fetching historical returns", largest_sector=largest_sector)

            # Fetch returns for portfolio proxy and benchmarks
            portfolio_returns = self._historical_data_service.get_daily_returns(
                largest_sector, days=90
            )
            spy_returns = self._historical_data_service.get_daily_returns("SPY", days=90)
            qqq_returns = self._historical_data_service.get_daily_returns("QQQ", days=90)

            # Calculate betas (60-day window)
            beta_to_spy = calculate_rolling_beta(portfolio_returns, spy_returns, window=60)
            beta_to_qqq = calculate_rolling_beta(portfolio_returns, qqq_returns, window=60)

            # Calculate correlations (90-day window)
            correlation_spy = calculate_rolling_correlation(
                portfolio_returns, spy_returns, window=90
            )
            correlation_qqq = calculate_rolling_correlation(
                portfolio_returns, qqq_returns, window=90
            )

            logger.info(
                "Calculated rolling metrics",
                beta_to_spy=str(beta_to_spy),
                beta_to_qqq=str(beta_to_qqq),
                correlation_spy=str(correlation_spy),
                correlation_qqq=str(correlation_qqq),
            )

            return beta_to_spy, beta_to_qqq, correlation_spy, correlation_qqq

        except Exception as e:
            logger.warning(
                "Failed to calculate rolling metrics, falling back to static betas",
                error=str(e),
            )
            # Fall back to static betas on error
            return (
                Decimal("1.0"),  # beta_to_spy
                Decimal("1.15"),  # beta_to_qqq (typical)
                Decimal("0.0"),  # correlation_spy (unknown)
                Decimal("0.0"),  # correlation_qqq (unknown)
            )

