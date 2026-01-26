"""Business Unit: hedge_evaluator | Status: current.

Hedge sizing calculator for options hedging.

Determines appropriate hedge sizing based on:
- VIX-adaptive premium budget
- Portfolio exposure and leverage
- Target delta and payoff objectives
- Template selection (tail_first, smoothing)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    MAX_EXISTING_HEDGE_COUNT,
    MAX_SINGLE_POSITION_PCT,
    MIN_EXPOSURE_RATIO,
    MIN_NAV_THRESHOLD,
    SMOOTHING_HEDGE_TEMPLATE,
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
    hedge_template: Literal["tail_first", "smoothing"]  # Template name
    vix_tier: str  # VIX tier used (low, mid, high)
    exposure_multiplier: Decimal  # Multiplier applied for leverage
    # Spread-specific fields (only used for smoothing template)
    short_delta: Decimal | None = None  # Short leg delta (for put spreads)
    is_spread: bool = False  # Whether this is a spread recommendation


class HedgeSizer:
    """Calculates hedge sizing based on portfolio exposure and market conditions.

    Uses VIX-adaptive budgeting to buy protection more aggressively when
    volatility is low (options are cheap) and conservatively when high.

    Supports multiple hedge templates:
    - tail_first: Long 15-delta puts (high convexity, higher cost)
    - smoothing: Put spreads (30-delta long / 10-delta short, lower cost)
    """

    def __init__(
        self,
        template: Literal["tail_first", "smoothing"] = "tail_first",
    ) -> None:
        """Initialize hedge sizer.

        Args:
            template: Hedge template to use (default: tail_first)

        """
        self._template_name = template

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
        if self._template_name == "smoothing":
            # Smoothing template has its own budget rates
            if vix < VIX_LOW_THRESHOLD:
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_low
            elif vix < VIX_HIGH_THRESHOLD:
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_mid
            else:
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_high
        else:
            base_rate = get_budget_rate_for_vix(vix)

        vix_tier = self._get_vix_tier(vix)

        # Apply exposure multiplier for leveraged portfolios
        exposure_multiplier = get_exposure_multiplier(exposure.net_exposure_ratio)

        # Calculate premium budget
        adjusted_rate = base_rate * exposure_multiplier
        premium_budget = exposure.nav * adjusted_rate
        nav_pct = adjusted_rate

        # Determine target delta and DTE based on template
        if self._template_name == "smoothing":
            target_delta = SMOOTHING_HEDGE_TEMPLATE.long_delta
            target_dte = SMOOTHING_HEDGE_TEMPLATE.target_dte
            short_delta = SMOOTHING_HEDGE_TEMPLATE.short_delta
            is_spread = True
        else:
            target_delta = TAIL_HEDGE_TEMPLATE.target_delta
            target_dte = TAIL_HEDGE_TEMPLATE.target_dte
            short_delta = None
            is_spread = False

        # Apply maximum position concentration cap (2% NAV)
        max_premium = exposure.nav * MAX_SINGLE_POSITION_PCT
        if premium_budget > max_premium:
            logger.warning(
                "Premium budget exceeds max concentration limit, capping to 2% NAV",
                original_budget=str(premium_budget),
                original_nav_pct=str(nav_pct),
                max_premium=str(max_premium),
                max_concentration_pct=str(MAX_SINGLE_POSITION_PCT),
                nav=str(exposure.nav),
            )
            premium_budget = max_premium
            nav_pct = MAX_SINGLE_POSITION_PCT

        # Estimate contracts (will be refined during execution based on actual quotes)
        contracts_estimated = self._estimate_contracts(
            premium_budget=premium_budget,
            underlying_price=underlying_price,
            target_delta=target_delta,
            is_spread=is_spread,
        )

        recommendation = HedgeRecommendation(
            underlying_symbol=exposure.primary_hedge_underlying,
            target_delta=target_delta,
            target_dte=target_dte,
            premium_budget=premium_budget,
            nav_pct=nav_pct,
            contracts_estimated=contracts_estimated,
            hedge_template=self._template_name,
            vix_tier=vix_tier,
            exposure_multiplier=exposure_multiplier,
            short_delta=short_delta,
            is_spread=is_spread,
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
            template=self._template_name,
            is_spread=is_spread,
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
        *,
        is_spread: bool = False,
    ) -> int:
        """Estimate number of contracts based on budget.

        This is a rough estimate - actual contract count will be
        determined during execution based on real option quotes.

        Rule of thumb for OTM puts:
        - 15-delta put: Premium ~ 1-2% of underlying price at 90 DTE
        - 30-delta put: Premium ~ 2-3% of underlying price at 60 DTE
        - 10-delta put: Premium ~ 0.5-1% of underlying price at 60 DTE
        - Put spread (30-10): Net premium ~ 1-2% of underlying

        Args:
            premium_budget: Dollar amount available for premium
            underlying_price: Current price of underlying
            target_delta: Target delta (affects premium estimate)
            is_spread: Whether this is a spread (affects net premium)

        Returns:
            Estimated contract count

        """
        if underlying_price is None or underlying_price <= 0:
            # Can't estimate without price - return placeholder
            return 1

        # Estimate premium per contract based on delta and structure
        if is_spread:
            # Put spread: buy 30-delta, sell 10-delta
            # Net premium is roughly 1.5% of underlying at 60 DTE
            premium_pct = Decimal("0.015")
        else:
            # Single put: scale by delta
            # 15-delta put at 90 DTE typically costs ~1.5% of underlying
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
