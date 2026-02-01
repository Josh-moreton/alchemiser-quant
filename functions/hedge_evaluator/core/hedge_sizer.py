"""Business Unit: hedge_evaluator | Status: current.

Hedge sizing calculator for options hedging.

Determines appropriate hedge sizing based on:
- IV-adaptive premium budget (replaces VIX proxy)
- Portfolio exposure and leverage
- Target delta and payoff objectives
- Template selection (tail_first, smoothing)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.constants import (
    MAX_ANNUAL_PREMIUM_SPEND_PCT,
    MAX_EXISTING_HEDGE_COUNT,
    MAX_SINGLE_POSITION_PCT,
    MIN_EXPOSURE_RATIO,
    MIN_NAV_THRESHOLD,
    SMOOTHING_HEDGE_TEMPLATE,
    TAIL_HEDGE_TEMPLATE,
    apply_rich_iv_adjustment,
    check_annual_spend_cap,
    get_exposure_multiplier,
)
from the_alchemiser.shared.options.payoff_calculator import (
    PayoffCalculator,
    PayoffScenario,
)
from the_alchemiser.shared.options.premium_tracker import PremiumTracker

from .exposure_calculator import PortfolioExposure

if TYPE_CHECKING:
    from the_alchemiser.shared.options.iv_signal import IVRegime, IVSignal

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
    vix_tier: str  # Regime tier (low, mid, high) - kept for backward compatibility
    exposure_multiplier: Decimal  # Multiplier applied for leverage
    # Spread-specific fields (only used for smoothing template)
    short_delta: Decimal | None = None  # Short leg delta (for put spreads)
    is_spread: bool = False  # Whether this is a spread recommendation
    # Rich IV adjustment indicator
    rich_iv_applied: bool = False  # Whether rich IV adjustments were applied
    # Payoff-based sizing fields
    target_payoff_pct: Decimal | None = None  # Target payoff at scenario move
    scenario_move_pct: Decimal | None = None  # Scenario move used for sizing
    contracts_for_target: int | None = None  # Contracts needed for target payoff
    was_clipped_by_budget: bool = False  # Whether budget cap reduced contracts
    clip_report: str | None = None  # Human-readable clipping report


class HedgeSizer:
    """Calculates hedge sizing based on portfolio exposure and market conditions.

    Uses IV-adaptive budgeting to buy protection more aggressively when
    implied volatility is low (options are cheap) and conservatively when high.

    Replaces VIX proxy (VIXY × 10) with proper IV data from the hedge underlying.

    Supports multiple hedge templates:
    - tail_first: Long 15-delta puts (high convexity, higher cost)
    - smoothing: Put spreads (30-delta long / 10-delta short, lower cost)
    """

    def __init__(
        self,
        template: Literal["tail_first", "smoothing"] = "tail_first",
        premium_tracker: PremiumTracker | None = None,
    ) -> None:
        """Initialize hedge sizer.

        Args:
            template: Hedge template to use (default: tail_first)
            premium_tracker: Premium spend tracker (optional, for spend cap enforcement)

        """
        self._template_name = template
        self._payoff_calculator = PayoffCalculator()
        self._premium_tracker = premium_tracker

    def calculate_hedge_recommendation(
        self,
        exposure: PortfolioExposure,
        iv_signal: IVSignal,
        iv_regime: IVRegime,
        underlying_price: Decimal | None = None,
    ) -> HedgeRecommendation:
        """Calculate hedge sizing recommendation using payoff-first approach.

        New approach:
        1. Calculate contracts needed to achieve target payoff at scenario move
        2. Estimate premium cost for those contracts
        3. Clip by budget constraints if needed
        4. Emit explicit report if clipping occurs

        Args:
            exposure: Portfolio exposure metrics from ExposureCalculator
            iv_signal: IV signal with ATM IV, skew, and percentile
            iv_regime: IV regime classification (low/mid/high)
            underlying_price: Current price of hedge underlying (for contract estimate)

        Returns:
            HedgeRecommendation with sizing parameters

        """
        # Map IV regime to budget rate
        # Low IV (< 30th percentile): Buy protection aggressively (0.8% NAV/month)
        # Mid IV (30th-70th percentile): Standard hedging (0.5% NAV/month)
        # High IV (> 70th percentile): Reduce intensity (0.3% NAV/month)
        if self._template_name == "smoothing":
            # Smoothing template has its own budget rates
            if iv_regime.regime == "low":
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_low
            elif iv_regime.regime == "mid":
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_mid
            else:
                base_rate = SMOOTHING_HEDGE_TEMPLATE.budget_vix_high
            scenario_move = SMOOTHING_HEDGE_TEMPLATE.scenario_move
            min_payoff = SMOOTHING_HEDGE_TEMPLATE.min_payoff_nav_pct
            max_payoff = SMOOTHING_HEDGE_TEMPLATE.max_payoff_nav_pct
        else:
            # Tail hedge template budget rates
            if iv_regime.regime == "low":
                base_rate = TAIL_HEDGE_TEMPLATE.budget_vix_low
            elif iv_regime.regime == "mid":
                base_rate = TAIL_HEDGE_TEMPLATE.budget_vix_mid
            else:
                base_rate = TAIL_HEDGE_TEMPLATE.budget_vix_high
            scenario_move = TAIL_HEDGE_TEMPLATE.scenario_move
            min_payoff = TAIL_HEDGE_TEMPLATE.min_payoff_nav_pct
            max_payoff = TAIL_HEDGE_TEMPLATE.max_payoff_nav_pct

        regime_tier = iv_regime.regime  # For backward compatibility with "vix_tier"

        # Apply exposure multiplier for leveraged portfolios
        exposure_multiplier = get_exposure_multiplier(exposure.net_exposure_ratio)

        # Calculate premium budget cap
        adjusted_rate = base_rate * exposure_multiplier
        premium_budget_cap = exposure.nav * adjusted_rate
        nav_pct_cap = adjusted_rate

        # Apply maximum position concentration cap (2% NAV)
        max_premium = exposure.nav * MAX_SINGLE_POSITION_PCT
        if premium_budget_cap > max_premium:
            logger.warning(
                "Premium budget exceeds max concentration limit, capping to 2% NAV",
                original_budget=str(premium_budget_cap),
                original_nav_pct=str(nav_pct_cap),
                max_premium=str(max_premium),
                max_concentration_pct=str(MAX_SINGLE_POSITION_PCT),
                nav=str(exposure.nav),
            )
            premium_budget_cap = max_premium
            nav_pct_cap = MAX_SINGLE_POSITION_PCT

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

        # Calculate midpoint payoff target
        target_payoff_pct = (min_payoff + max_payoff) / Decimal("2")

        # Apply rich IV adjustments if needed (only for outright positions, not spreads)
        # Rich IV: When IV percentile is high (> 70th percentile) OR skew is rich
        # Note: For spreads, adjusting only the long leg delta would change the spread width
        # in unintended ways. Skip rich IV adjustments for spread strategies.
        should_reduce = iv_regime.regime == "high" or iv_regime.skew_rich

        if should_reduce and not is_spread:
            # Convert IV percentile to approximate VIX for legacy adjustment function
            # This is temporary until we refactor apply_rich_iv_adjustment
            approximate_vix = self._iv_percentile_to_vix_approx(iv_signal.atm_iv)

            logger.info(
                "Applying rich IV adjustments",
                iv_percentile=str(iv_signal.iv_percentile),
                iv_skew=str(iv_signal.iv_skew),
                skew_rich=iv_regime.skew_rich,
                original_delta=str(target_delta),
                original_dte=target_dte,
                original_payoff_pct=str(target_payoff_pct),
            )
            target_delta, target_dte, target_payoff_pct = apply_rich_iv_adjustment(
                target_delta=target_delta,
                target_dte=target_dte,
                target_payoff_pct=target_payoff_pct,
                vix=approximate_vix,
            )
            logger.info(
                "Rich IV adjustments applied",
                adjusted_delta=str(target_delta),
                adjusted_dte=target_dte,
                adjusted_payoff_pct=str(target_payoff_pct),
            )
        elif should_reduce and is_spread:
            logger.info(
                "Skipping rich IV adjustments for spread position",
                iv_regime=iv_regime.regime,
                skew_rich=iv_regime.skew_rich,
                template=self._template_name,
                reason="Adjusting long leg delta would change spread width",
            )

        rich_iv_applied = should_reduce and not is_spread

        # PAYOFF-FIRST SIZING: Calculate contracts needed for target payoff
        if underlying_price is None or underlying_price <= 0:
            # Can't do payoff sizing without price - fallback to budget-first
            logger.warning(
                "No underlying price provided, falling back to budget-first sizing",
                underlying=exposure.primary_hedge_underlying,
            )
            contracts_estimated = self._estimate_contracts(
                premium_budget=premium_budget_cap,
                underlying_price=underlying_price,
                target_delta=target_delta,
                is_spread=is_spread,
            )
            recommendation = HedgeRecommendation(
                underlying_symbol=exposure.primary_hedge_underlying,
                target_delta=target_delta,
                target_dte=target_dte,
                premium_budget=premium_budget_cap,
                nav_pct=nav_pct_cap,
                contracts_estimated=contracts_estimated,
                hedge_template=self._template_name,
                vix_tier=regime_tier,
                exposure_multiplier=exposure_multiplier,
                short_delta=short_delta,
                is_spread=is_spread,
                rich_iv_applied=rich_iv_applied,
                target_payoff_pct=target_payoff_pct,
                scenario_move_pct=scenario_move,
                contracts_for_target=None,
                was_clipped_by_budget=False,
                clip_report=None,
            )
            return recommendation

        # Create scenario
        scenario = PayoffScenario(
            scenario_move_pct=scenario_move,
            target_payoff_pct=target_payoff_pct,
            description=f"{scenario_move * 100:.0f}% market move",
        )

        # Calculate contracts for target payoff
        payoff_result = self._payoff_calculator.calculate_contracts_for_scenario(
            underlying_price=underlying_price,
            option_delta=target_delta,
            scenario=scenario,
            nav=exposure.nav,
            leverage_factor=exposure_multiplier,
        )

        contracts_for_target = payoff_result.contracts_required

        # Estimate premium cost for target contracts
        estimated_premium = self._payoff_calculator.estimate_premium_cost(
            contracts=contracts_for_target,
            underlying_price=underlying_price,
            option_delta=target_delta,
            days_to_expiry=target_dte,
            is_spread=is_spread,
        )

        # Check if premium is within budget cap
        was_clipped = estimated_premium > premium_budget_cap
        clip_report = None

        if was_clipped:
            # Clip contracts to fit budget
            # Calculate how many contracts we can afford
            premium_per_contract = estimated_premium / contracts_for_target
            contracts_affordable = int(premium_budget_cap / premium_per_contract)
            contracts_affordable = max(1, contracts_affordable)  # Minimum 1 contract

            # Calculate actual payoff at scenario with affordable contracts
            affordable_payoff = (
                payoff_result.payoff_per_contract * contracts_affordable / exposure.nav
            )

            # Generate clip report
            clip_report = (
                f"Target: {target_payoff_pct * 100:.1f}% NAV at "
                f"{scenario_move * 100:.0f}% move ({contracts_for_target} contracts). "
                f"Affordable: {affordable_payoff * 100:.1f}% NAV at "
                f"{scenario_move * 100:.0f}% move ({contracts_affordable} contracts, "
                f"clipped by premium cap)."
            )

            logger.warning(
                "Contracts clipped by premium budget cap",
                target_contracts=contracts_for_target,
                affordable_contracts=contracts_affordable,
                target_premium=str(estimated_premium),
                premium_cap=str(premium_budget_cap),
                target_payoff_pct=f"{target_payoff_pct * 100:.2f}%",
                affordable_payoff_pct=f"{affordable_payoff * 100:.2f}%",
                scenario_move=str(scenario_move),
                clip_report=clip_report,
            )

            # Use affordable contracts
            contracts_estimated = contracts_affordable
            premium_budget = premium_budget_cap
            nav_pct = nav_pct_cap
        else:
            # No clipping needed - use target contracts
            contracts_estimated = contracts_for_target
            premium_budget = estimated_premium
            nav_pct = estimated_premium / exposure.nav if exposure.nav > 0 else Decimal("0")

            logger.info(
                "Payoff target achievable within budget",
                contracts=contracts_estimated,
                estimated_premium=str(premium_budget),
                premium_cap=str(premium_budget_cap),
                target_payoff_pct=f"{target_payoff_pct * 100:.2f}%",
                scenario_move=str(scenario_move),
            )

        recommendation = HedgeRecommendation(
            underlying_symbol=exposure.primary_hedge_underlying,
            target_delta=target_delta,
            target_dte=target_dte,
            premium_budget=premium_budget,
            nav_pct=nav_pct,
            contracts_estimated=contracts_estimated,
            hedge_template=self._template_name,
            vix_tier=regime_tier,
            exposure_multiplier=exposure_multiplier,
            short_delta=short_delta,
            is_spread=is_spread,
            rich_iv_applied=rich_iv_applied,
            target_payoff_pct=target_payoff_pct,
            scenario_move_pct=scenario_move,
            contracts_for_target=contracts_for_target,
            was_clipped_by_budget=was_clipped,
            clip_report=clip_report,
        )

        logger.info(
            "Calculated hedge recommendation (payoff-first)",
            underlying=exposure.primary_hedge_underlying,
            premium_budget=str(premium_budget),
            nav_pct=str(nav_pct),
            iv_regime=regime_tier,
            iv_percentile=str(iv_signal.iv_percentile),
            iv_skew=str(iv_signal.iv_skew),
            exposure_ratio=str(exposure.net_exposure_ratio),
            exposure_multiplier=str(exposure_multiplier),
            contracts_estimated=contracts_estimated,
            contracts_for_target=contracts_for_target,
            template=self._template_name,
            is_spread=is_spread,
            rich_iv_applied=rich_iv_applied,
            was_clipped=was_clipped,
            target_payoff_pct=f"{target_payoff_pct * 100:.2f}%",
            scenario_move=str(scenario_move),
        )

        return recommendation

    def _iv_percentile_to_vix_approx(self, atm_iv: Decimal) -> Decimal:
        """Convert ATM IV to approximate VIX for legacy adjustment functions.

        This is a temporary mapping until we refactor apply_rich_iv_adjustment
        to work directly with IV percentile.

        Args:
            atm_iv: ATM implied volatility (e.g., 0.20 = 20%)

        Returns:
            Approximate VIX value

        """
        # Convert IV to percentage (0.20 → 20)
        iv_pct = atm_iv * 100

        # Map IV to VIX-like scale
        # Typical ATM IV: 15-25% → VIX 15-25
        # High ATM IV: 30-40% → VIX 30-40
        # Very high ATM IV: > 40% → VIX > 40
        return iv_pct  # Direct mapping for now

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
        year_to_date_spend: Decimal = Decimal("0"),
        proposed_spend: Decimal | None = None,
    ) -> tuple[bool, str | None]:
        """Determine if hedging is needed.

        Checks portfolio conditions and enforces spend caps.
        Uses premium tracker if available for rolling 12-month enforcement.

        Args:
            exposure: Portfolio exposure metrics
            existing_hedge_count: Number of existing hedge positions
            year_to_date_spend: Total premium spent year-to-date (fallback)
            proposed_spend: Proposed additional premium spend (optional)

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

        # Check rolling 12-month spend cap using premium tracker if available
        if self._premium_tracker is not None and proposed_spend is not None:
            check_result = self._premium_tracker.check_spend_within_cap(
                proposed_spend=proposed_spend,
                nav=exposure.nav,
            )

            if not check_result.is_within_cap:
                logger.warning(
                    "Proposed hedge would exceed rolling 12-month spend cap (fail closed)",
                    current_spend_12mo=str(check_result.current_spend_12mo),
                    proposed_spend=str(proposed_spend),
                    total_spend_after=str(check_result.total_spend_after),
                    annual_cap_dollars=str(check_result.annual_cap_dollars),
                    remaining_capacity=str(check_result.remaining_capacity),
                    current_spend_pct=f"{check_result.current_spend_pct * 100:.2f}%",
                    total_spend_pct=f"{check_result.total_spend_pct * 100:.2f}%",
                )
                return (
                    False,
                    f"Rolling 12-month spend cap would be exceeded "
                    f"(current: {check_result.current_spend_pct * 100:.2f}%, "
                    f"after: {check_result.total_spend_pct * 100:.2f}%, "
                    f"cap: {MAX_ANNUAL_PREMIUM_SPEND_PCT * 100:.1f}%)",
                )

            logger.info(
                "Proposed hedge within rolling 12-month spend cap",
                current_spend_12mo=str(check_result.current_spend_12mo),
                proposed_spend=str(proposed_spend),
                remaining_capacity=str(check_result.remaining_capacity),
                current_spend_pct=f"{check_result.current_spend_pct * 100:.2f}%",
            )

        # Fallback: Check annual spend cap using YTD spend if tracker not available
        elif proposed_spend is not None:
            if not check_annual_spend_cap(year_to_date_spend, proposed_spend, exposure.nav):
                ytd_pct = (
                    (year_to_date_spend / exposure.nav * Decimal("100"))
                    if exposure.nav > 0
                    else Decimal("0")
                )
                return False, f"Annual spend cap would be exceeded (YTD: {ytd_pct:.2f}%)"

        return True, None
