"""Business Unit: hedge_evaluator | Status: current.

Hedge sizing calculator for options hedging.

Determines appropriate hedge sizing based on:
- VIX-adaptive premium budget
- Portfolio exposure and leverage
- Target delta and payoff objectives
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    MAX_EXISTING_HEDGE_COUNT,
    MIN_EXPOSURE_RATIO,
    MIN_NAV_THRESHOLD,
    TAIL_HEDGE_TEMPLATE,
    VIX_HIGH_THRESHOLD,
    VIX_LOW_THRESHOLD,
    get_budget_rate_for_vix,
    get_exposure_multiplier,
)

from .exposure_calculator import PortfolioExposure

logger = get_logger(__name__)


@dataclass(frozen=True)
class HedgeRecommendation:
    """Hedge sizing recommendation.

    Contains all parameters needed to execute a hedge order.
    """

    underlying_symbol: str  # QQQ, SPY, etc.
    target_delta: Decimal  # Target put delta (e.g., 0.15)
    target_dte: int  # Target days to expiry (e.g., 90)
    premium_budget: Decimal  # Dollar amount to spend on premium
    nav_pct: Decimal  # Budget as percentage of NAV
    contracts_estimated: int  # Estimated contracts (refined during execution)
    hedge_template: str  # Template name (tail_first, smoothing)
    vix_tier: str  # VIX tier used (low, mid, high)
    exposure_multiplier: Decimal  # Multiplier applied for leverage


class HedgeSizer:
    """Calculates hedge sizing based on portfolio exposure and market conditions.

    Uses VIX-adaptive budgeting to buy protection more aggressively when
    volatility is low (options are cheap) and conservatively when high.
    """

    def __init__(self) -> None:
        """Initialize hedge sizer."""
        self._template = TAIL_HEDGE_TEMPLATE

    def calculate_hedge_recommendation(
        self,
        exposure: PortfolioExposure,
        current_vix: Decimal | None = None,
        underlying_price: Decimal | None = None,
    ) -> HedgeRecommendation:
        """Calculate hedge sizing recommendation.

        Args:
            exposure: Portfolio exposure metrics from ExposureCalculator
            current_vix: Current VIX index value (defaults to 20 if None)
            underlying_price: Current price of hedge underlying (for contract estimate)

        Returns:
            HedgeRecommendation with sizing parameters

        """
        # Default VIX if not provided
        vix = current_vix if current_vix is not None else Decimal("20")

        # Get VIX-adaptive base budget rate
        base_rate = get_budget_rate_for_vix(vix)
        vix_tier = self._get_vix_tier(vix)

        # Apply exposure multiplier for leveraged portfolios
        exposure_multiplier = get_exposure_multiplier(exposure.net_exposure_ratio)

        # Calculate premium budget
        adjusted_rate = base_rate * exposure_multiplier
        premium_budget = exposure.nav * adjusted_rate
        nav_pct = adjusted_rate

        # Estimate contracts (will be refined during execution based on actual quotes)
        contracts_estimated = self._estimate_contracts(
            premium_budget=premium_budget,
            underlying_price=underlying_price,
            target_delta=self._template.target_delta,
        )

        recommendation = HedgeRecommendation(
            underlying_symbol=exposure.primary_hedge_underlying,
            target_delta=self._template.target_delta,
            target_dte=self._template.target_dte,
            premium_budget=premium_budget,
            nav_pct=nav_pct,
            contracts_estimated=contracts_estimated,
            hedge_template="tail_first",
            vix_tier=vix_tier,
            exposure_multiplier=exposure_multiplier,
        )

        logger.info(
            "Calculated hedge recommendation",
            underlying=exposure.primary_hedge_underlying,
            premium_budget=str(premium_budget),
            nav_pct=str(nav_pct),
            vix=str(vix),
            vix_tier=vix_tier,
            exposure_ratio=str(exposure.net_exposure_ratio),
            exposure_multiplier=str(exposure_multiplier),
            contracts_estimated=contracts_estimated,
        )

        return recommendation

    def _get_vix_tier(self, vix: Decimal) -> str:
        """Determine VIX tier for logging/reporting.

        Args:
            vix: Current VIX value

        Returns:
            VIX tier string (low, mid, high)

        """
        if vix < VIX_LOW_THRESHOLD:
            return "low"
        if vix < VIX_HIGH_THRESHOLD:
            return "mid"
        return "high"

    def _estimate_contracts(
        self,
        premium_budget: Decimal,
        underlying_price: Decimal | None,
        target_delta: Decimal,
    ) -> int:
        """Estimate number of contracts based on budget.

        This is a rough estimate - actual contract count will be
        determined during execution based on real option quotes.

        Rule of thumb for 15-delta puts:
        - Premium ~ 1-2% of underlying price at 90 DTE
        - Each contract covers 100 shares

        Args:
            premium_budget: Dollar amount available for premium
            underlying_price: Current price of underlying
            target_delta: Target delta (affects premium estimate)

        Returns:
            Estimated contract count

        """
        if underlying_price is None or underlying_price <= 0:
            # Can't estimate without price - return placeholder
            return 1

        # Estimate premium per contract based on delta
        # 15-delta put at 90 DTE typically costs ~1.5% of underlying
        # Adjusted by delta: lower delta = cheaper premium
        delta_factor = target_delta / Decimal("0.15")  # Normalize to 15-delta
        premium_pct = Decimal("0.015") * delta_factor

        # Premium per contract = premium_pct * underlying_price * 100 shares
        estimated_premium_per_contract = premium_pct * underlying_price * 100

        if estimated_premium_per_contract <= 0:
            return 1

        # Calculate contracts
        contracts = int(premium_budget / estimated_premium_per_contract)

        # Minimum 1 contract
        return max(1, contracts)

    def should_hedge(
        self,
        exposure: PortfolioExposure,
        existing_hedge_count: int = 0,
    ) -> tuple[bool, str | None]:
        """Determine if hedging is needed.

        Args:
            exposure: Portfolio exposure metrics
            existing_hedge_count: Number of existing hedge positions

        Returns:
            Tuple of (should_hedge, skip_reason if not hedging)

        """
        # Skip if NAV is too small - hedge costs would be disproportionate
        if exposure.nav < MIN_NAV_THRESHOLD:
            return False, f"NAV below minimum threshold (${MIN_NAV_THRESHOLD})"

        # Skip if net exposure ratio is very low
        if exposure.net_exposure_ratio < MIN_EXPOSURE_RATIO:
            return False, f"Net exposure ratio below {MIN_EXPOSURE_RATIO}x"

        # Skip if we already have hedges and they cover adequate exposure
        # (This is a simplified check - real check would evaluate hedge coverage)
        if existing_hedge_count >= MAX_EXISTING_HEDGE_COUNT:
            return False, "Existing hedges appear sufficient"

        return True, None
