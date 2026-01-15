"""Business Unit: hedge_evaluator | Status: current.

Sector mapper for aggregating positions by hedge ETF.

Maps individual equity positions to their corresponding sector ETFs
and aggregates exposure for efficient hedging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import HEDGE_ETFS, get_hedge_etf

logger = get_logger(__name__)


@dataclass
class SectorExposure:
    """Aggregated exposure for a single sector ETF."""

    etf_symbol: str
    total_value: Decimal = Decimal("0")
    position_count: int = 0
    tickers: list[str] = field(default_factory=list)


class SectorMapper:
    """Maps portfolio positions to sector ETF exposures.

    Aggregates individual equity positions by their hedge ETF
    for more efficient hedging via liquid index options.
    """

    def __init__(self) -> None:
        """Initialize sector mapper."""
        self._hedge_etfs = HEDGE_ETFS

    def map_positions_to_sectors(
        self,
        positions: dict[str, Decimal],
    ) -> dict[str, SectorExposure]:
        """Map portfolio positions to sector ETF exposures.

        Args:
            positions: Dict of ticker -> position value (in dollars)

        Returns:
            Dict of sector ETF symbol -> SectorExposure

        Example:
            >>> mapper = SectorMapper()
            >>> positions = {"AAPL": Decimal("10000"), "MSFT": Decimal("8000")}
            >>> exposures = mapper.map_positions_to_sectors(positions)
            >>> exposures["QQQ"].total_value
            Decimal('18000')

        """
        sector_exposures: dict[str, SectorExposure] = {}

        for ticker, value in positions.items():
            # Skip if value is zero or negative
            if value <= 0:
                continue

            # Map ticker to hedge ETF
            hedge_etf = get_hedge_etf(ticker)

            # Initialize sector exposure if not exists
            if hedge_etf not in sector_exposures:
                sector_exposures[hedge_etf] = SectorExposure(etf_symbol=hedge_etf)

            # Accumulate exposure
            sector_exposures[hedge_etf].total_value += value
            sector_exposures[hedge_etf].position_count += 1
            sector_exposures[hedge_etf].tickers.append(ticker)

        logger.info(
            "Mapped positions to sectors",
            total_positions=len(positions),
            sectors_with_exposure=len(sector_exposures),
            sector_breakdown={
                etf: str(exp.total_value) for etf, exp in sector_exposures.items()
            },
        )

        return sector_exposures

    def get_primary_hedge_underlying(
        self,
        sector_exposures: dict[str, SectorExposure],
    ) -> str:
        """Determine the primary hedge underlying based on exposure.

        Returns the sector ETF with the highest exposure, with
        preference for QQQ for tech-heavy portfolios.

        Args:
            sector_exposures: Sector exposure breakdown from map_positions_to_sectors

        Returns:
            Primary hedge ETF symbol (defaults to QQQ if empty)

        """
        if not sector_exposures:
            return "QQQ"  # Default for tech-heavy portfolios

        # Find sector with highest exposure
        max_exposure = Decimal("0")
        primary_etf = "QQQ"

        for etf, exposure in sector_exposures.items():
            if exposure.total_value > max_exposure:
                max_exposure = exposure.total_value
                primary_etf = etf

        # For tech-heavy portfolios, prefer QQQ if it's within 20% of max
        if "QQQ" in sector_exposures:
            qqq_exposure = sector_exposures["QQQ"].total_value
            if qqq_exposure >= max_exposure * Decimal("0.8"):
                primary_etf = "QQQ"

        logger.info(
            "Determined primary hedge underlying",
            primary_etf=primary_etf,
            max_exposure=str(max_exposure),
        )

        return primary_etf

    def aggregate_for_single_hedge(
        self,
        sector_exposures: dict[str, SectorExposure],
    ) -> tuple[str, Decimal]:
        """Aggregate all exposures for a single hedge underlying.

        For simplicity, aggregates all sector exposures into a single
        hedge on the primary underlying (usually QQQ for tech portfolios).

        Args:
            sector_exposures: Sector exposure breakdown

        Returns:
            Tuple of (hedge_etf, total_exposure_value)

        """
        primary_etf = self.get_primary_hedge_underlying(sector_exposures)

        # Sum all exposures (we're hedging the whole portfolio)
        total_exposure: Decimal = sum(
            (exp.total_value for exp in sector_exposures.values()),
            Decimal("0"),
        )

        return primary_etf, total_exposure
