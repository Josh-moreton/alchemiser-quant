"""Business Unit: shared | Status: current.

Hedge configuration constants for options hedging module.

Contains:
- Hedge ETF definitions with liquidity requirements
- Tail hedge template (15-delta OTM puts, 90 DTE)
- VIX-adaptive premium budget rates
- Liquidity filters for strike selection
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class HedgeETF:
    """Configuration for a hedge ETF instrument.

    Defines the properties and liquidity requirements for an ETF
    used as an underlying for options hedging.
    """

    symbol: str
    name: str
    beta_to_spy: Decimal  # Historical beta relative to SPY
    min_open_interest: int  # Minimum contract open interest
    max_spread_pct: Decimal  # Maximum bid-ask spread as percentage of mid


@dataclass(frozen=True)
class TailHedgeTemplate:
    """Configuration for tail-first hedge strategy.

    Optimized for leveraged portfolios (2.0x-2.5x+ exposure):
    - 15-delta OTM puts for convex payoff in crashes
    - 90 DTE for cost efficiency and roll management
    - VIX-adaptive budget to buy protection before vol expands
    """

    target_delta: Decimal  # Target put delta (e.g., 0.15 for 15-delta)
    target_dte: int  # Target days to expiry
    roll_trigger_dte: int  # Roll when DTE falls below this
    underlying: str  # Primary underlying ETF
    budget_vix_low: Decimal  # Budget rate when VIX < 18 (% NAV/month)
    budget_vix_mid: Decimal  # Budget rate when VIX 18-28 (% NAV/month)
    budget_vix_high: Decimal  # Budget rate when VIX > 28 (% NAV/month)
    exposure_base: Decimal  # Base exposure multiplier (at 1.0x leverage)
    exposure_per_excess: Decimal  # Additional multiplier per 1.0x above base
    exposure_max_multiplier: Decimal  # Cap on exposure multiplier
    scenario_move: Decimal  # Target underlying move for sizing (-0.20 = -20%)
    min_payoff_nav_pct: Decimal  # Minimum target payoff as % NAV
    max_payoff_nav_pct: Decimal  # Maximum target payoff as % NAV


@dataclass(frozen=True)
class SmoothingHedgeTemplate:
    """Configuration for smoothing hedge strategy using put spreads.

    Optimized for cost efficiency with reduced theta decay:
    - Put spread: buy 30-delta, sell 10-delta
    - 60 DTE for shorter tenor
    - Fixed 21-day roll cadence
    - Lower cost but capped upside
    """

    underlying: str  # Primary underlying ETF
    long_delta: Decimal  # Long put delta (e.g., 0.30 for 30-delta)
    short_delta: Decimal  # Short put delta (e.g., 0.10 for 10-delta)
    target_dte: int  # Target days to expiry
    roll_cadence_days: int  # Fixed roll cadence (not DTE-based)
    scenario_move: Decimal  # Target underlying move for sizing (-0.10 = -10%)
    min_payoff_nav_pct: Decimal  # Minimum target payoff as % NAV
    max_payoff_nav_pct: Decimal  # Maximum target payoff as % NAV
    budget_vix_low: Decimal  # Budget rate when VIX < 18 (% NAV/month)
    budget_vix_mid: Decimal  # Budget rate when VIX 18-28 (% NAV/month)
    budget_vix_high: Decimal  # Budget rate when VIX > 28 (% NAV/month)
    exposure_base: Decimal  # Base exposure multiplier (at 1.0x leverage)
    exposure_per_excess: Decimal  # Additional multiplier per 1.0x above base
    exposure_max_multiplier: Decimal  # Cap on exposure multiplier
    assignment_risk_delta_threshold: Decimal  # Delta threshold for assignment risk (0.80)


@dataclass(frozen=True)
class LiquidityFilters:
    """Liquidity filter configuration for option selection.

    Ensures selected options have adequate liquidity for
    efficient execution and reasonable exit.
    """

    min_open_interest: int  # Minimum contract open interest
    max_spread_pct: Decimal  # Maximum bid-ask spread (% of mid)
    min_dte: int  # Minimum days to expiry (avoid gamma risk)
    max_dte: int  # Maximum days to expiry


# ═══════════════════════════════════════════════════════════════════════════════
# HEDGE ETF DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

HEDGE_ETFS: dict[str, HedgeETF] = {
    # Primary broad market hedges (highest liquidity)
    "SPY": HedgeETF(
        symbol="SPY",
        name="S&P 500 ETF Trust",
        beta_to_spy=Decimal("1.00"),
        min_open_interest=50000,
        max_spread_pct=Decimal("0.02"),
    ),
    "QQQ": HedgeETF(
        symbol="QQQ",
        name="Invesco QQQ Trust (Nasdaq 100)",
        beta_to_spy=Decimal("1.15"),
        min_open_interest=30000,
        max_spread_pct=Decimal("0.02"),
    ),
    "IWM": HedgeETF(
        symbol="IWM",
        name="iShares Russell 2000 ETF",
        beta_to_spy=Decimal("1.20"),
        min_open_interest=10000,
        max_spread_pct=Decimal("0.03"),
    ),
    # Sector ETFs (moderate liquidity)
    "XLK": HedgeETF(
        symbol="XLK",
        name="Technology Select Sector SPDR",
        beta_to_spy=Decimal("1.10"),
        min_open_interest=5000,
        max_spread_pct=Decimal("0.03"),
    ),
    "XLF": HedgeETF(
        symbol="XLF",
        name="Financial Select Sector SPDR",
        beta_to_spy=Decimal("1.05"),
        min_open_interest=5000,
        max_spread_pct=Decimal("0.03"),
    ),
    "XLE": HedgeETF(
        symbol="XLE",
        name="Energy Select Sector SPDR",
        beta_to_spy=Decimal("1.30"),
        min_open_interest=3000,
        max_spread_pct=Decimal("0.04"),
    ),
    "XLV": HedgeETF(
        symbol="XLV",
        name="Health Care Select Sector SPDR",
        beta_to_spy=Decimal("0.85"),
        min_open_interest=3000,
        max_spread_pct=Decimal("0.04"),
    ),
    "XLY": HedgeETF(
        symbol="XLY",
        name="Consumer Discretionary Select Sector SPDR",
        beta_to_spy=Decimal("1.10"),
        min_open_interest=3000,
        max_spread_pct=Decimal("0.04"),
    ),
    "XLP": HedgeETF(
        symbol="XLP",
        name="Consumer Staples Select Sector SPDR",
        beta_to_spy=Decimal("0.65"),
        min_open_interest=3000,
        max_spread_pct=Decimal("0.04"),
    ),
    "XLI": HedgeETF(
        symbol="XLI",
        name="Industrial Select Sector SPDR",
        beta_to_spy=Decimal("1.05"),
        min_open_interest=3000,
        max_spread_pct=Decimal("0.04"),
    ),
    "XLB": HedgeETF(
        symbol="XLB",
        name="Materials Select Sector SPDR",
        beta_to_spy=Decimal("1.15"),
        min_open_interest=2000,
        max_spread_pct=Decimal("0.05"),
    ),
    "XLU": HedgeETF(
        symbol="XLU",
        name="Utilities Select Sector SPDR",
        beta_to_spy=Decimal("0.45"),
        min_open_interest=2000,
        max_spread_pct=Decimal("0.05"),
    ),
    "XLRE": HedgeETF(
        symbol="XLRE",
        name="Real Estate Select Sector SPDR",
        beta_to_spy=Decimal("0.80"),
        min_open_interest=2000,
        max_spread_pct=Decimal("0.05"),
    ),
    "XLC": HedgeETF(
        symbol="XLC",
        name="Communication Services Select Sector SPDR",
        beta_to_spy=Decimal("1.00"),
        min_open_interest=2000,
        max_spread_pct=Decimal("0.05"),
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# TAIL HEDGE TEMPLATE (Template 1)
# ═══════════════════════════════════════════════════════════════════════════════
# Optimized for leveraged (2.0x-2.5x+) tech-heavy portfolios
# Buy protection BEFORE volatility expands (counter-intuitive but optimal)

TAIL_HEDGE_TEMPLATE: TailHedgeTemplate = TailHedgeTemplate(
    target_delta=Decimal("0.15"),  # 15-delta OTM puts
    target_dte=90,  # 90 days to expiry
    roll_trigger_dte=45,  # Roll when DTE < 45
    underlying="QQQ",  # Primary hedge (tech-correlated)
    # VIX-adaptive budget rates (% of NAV per month)
    # Lower budget when VIX is high (options expensive, should already own)
    # Higher budget when VIX is low (options cheap, buy protection early)
    budget_vix_low=Decimal("0.008"),  # VIX < 18: 0.8% NAV/month
    budget_vix_mid=Decimal("0.005"),  # VIX 18-28: 0.5% NAV/month
    budget_vix_high=Decimal("0.003"),  # VIX > 28: 0.3% NAV/month
    # Exposure scaling (for 2.0x-2.5x leverage)
    exposure_base=Decimal("1.0"),
    exposure_per_excess=Decimal("0.5"),  # +0.5x per 1.0x above 1.0x
    exposure_max_multiplier=Decimal("1.5"),  # Cap at 1.5x budget
    # Scenario analysis targets
    scenario_move=Decimal("-0.20"),  # Size for -20% underlying move
    min_payoff_nav_pct=Decimal("0.06"),  # Min +6% NAV payoff
    max_payoff_nav_pct=Decimal("0.10"),  # Max +10% NAV payoff
)


# ═══════════════════════════════════════════════════════════════════════════════
# SMOOTHING HEDGE TEMPLATE (Template 2)
# ═══════════════════════════════════════════════════════════════════════════════
# Lower-cost hedging with put spreads
# Buy 30-delta, sell 10-delta for reduced premium cost and theta decay
# Fixed 21-day roll cadence

SMOOTHING_HEDGE_TEMPLATE: SmoothingHedgeTemplate = SmoothingHedgeTemplate(
    underlying="QQQ",  # Primary hedge (tech-correlated)
    long_delta=Decimal("0.30"),  # Buy 30-delta put
    short_delta=Decimal("0.10"),  # Sell 10-delta put
    target_dte=60,  # 60 days to expiry (shorter than tail)
    roll_cadence_days=21,  # Roll every 3 weeks (fixed cadence)
    scenario_move=Decimal("-0.10"),  # Size for -10% underlying move
    min_payoff_nav_pct=Decimal("0.02"),  # Min +2% NAV payoff
    max_payoff_nav_pct=Decimal("0.04"),  # Max +4% NAV payoff
    # VIX-adaptive budget rates (lower than tail due to spread structure)
    budget_vix_low=Decimal("0.004"),  # VIX < 18: 0.4% NAV/month
    budget_vix_mid=Decimal("0.0025"),  # VIX 18-28: 0.25% NAV/month
    budget_vix_high=Decimal("0.0015"),  # VIX > 28: 0.15% NAV/month
    # Exposure scaling (same as tail)
    exposure_base=Decimal("1.0"),
    exposure_per_excess=Decimal("0.5"),
    exposure_max_multiplier=Decimal("1.5"),
    # Assignment risk threshold (FR-5.3)
    assignment_risk_delta_threshold=Decimal("0.80"),  # Alert when short leg delta > 0.80
)


# ═══════════════════════════════════════════════════════════════════════════════
# LIQUIDITY FILTERS
# ═══════════════════════════════════════════════════════════════════════════════

LIQUIDITY_FILTERS: LiquidityFilters = LiquidityFilters(
    min_open_interest=1000,  # Minimum 1000 contracts OI
    max_spread_pct=Decimal("0.05"),  # Max 5% bid-ask spread
    min_dte=14,  # No options expiring < 14 days (avoid gamma)
    max_dte=120,  # No options expiring > 120 days (too far out)
)


# ═══════════════════════════════════════════════════════════════════════════════
# VIX THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

VIX_LOW_THRESHOLD: Decimal = Decimal("18")
VIX_HIGH_THRESHOLD: Decimal = Decimal("28")

# VIX Proxy Configuration
# Alpaca does not provide direct VIX index quotes. We use VIXY ETF as a liquid proxy.
# VIXY (ProShares VIX Short-Term Futures ETF) tracks VIX short-term futures.
# Historical analysis shows VIX ≈ VIXY * 10, so we scale by 10 to estimate VIX.
# Note: This is an approximation - the relationship varies with contango/backwardation.
# Typical VIX range: 10-80, with 15-25 being normal market conditions.
# The approximation is sufficient for budget tier selection (low/mid/high).
VIX_PROXY_SYMBOL: str = "VIXY"
VIX_PROXY_SCALE_FACTOR: Decimal = Decimal("10")


# ═══════════════════════════════════════════════════════════════════════════════
# HEDGE SIZING THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

# Minimum portfolio NAV required to consider hedging.
# Below this threshold, hedge costs would be disproportionate to portfolio size.
MIN_NAV_THRESHOLD: Decimal = Decimal("10000")

# Minimum net exposure ratio required to consider hedging.
# Portfolios with low exposure don't need protective hedges.
MIN_EXPOSURE_RATIO: Decimal = Decimal("0.5")

# Maximum number of existing hedges before skipping new hedge evaluation.
# Limits hedge accumulation; a portfolio with 3+ hedges is considered adequately protected.
MAX_EXISTING_HEDGE_COUNT: int = 3

# Maximum concentration for a single hedge position as percentage of NAV.
# Prevents excessive capital allocation to a single hedge position.
# Single hedge position premium must not exceed 2% of portfolio NAV.
MAX_SINGLE_POSITION_PCT: Decimal = Decimal("0.02")


# ═══════════════════════════════════════════════════════════════════════════════
# HARD CONSTRAINTS FOR PREMIUM SPEND
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum premium spend per year as percentage of NAV.
# This is a hard cap to prevent excessive hedging costs eating into returns.
# Example: For a $150,000 portfolio, 4% = $6,000/year maximum premium spend.
MAX_PREMIUM_SPEND_ANNUAL_PCT: Decimal = Decimal("0.04")  # 4% NAV/year

# Maximum premium spend per month as percentage of NAV.
# Monthly cap prevents concentrated hedging in a single period.
# Example: For a $150,000 portfolio, 0.35% = $525/month maximum premium spend.
MAX_PREMIUM_SPEND_MONTHLY_PCT: Decimal = Decimal("0.0035")  # 0.35% NAV/month

# Minimum required protection payoff at -20% underlying move as percentage of NAV.
# This ensures hedges provide meaningful protection in severe drawdown scenarios.
# Example: For a $150,000 portfolio with 2.5x leverage = $375,000 exposure.
# At -20% index move: -$75,000 loss. Min protection: $9,000 (6% of NAV).
MIN_PROTECTION_AT_MINUS_20_PCT: Decimal = Decimal("0.06")  # 6% NAV minimum payoff

# Fallback behavior when minimum protection is unaffordable within premium budget.
# Options: "clip_and_report", "switch_template", "skip"
# - clip_and_report: Buy maximum affordable protection and log shortfall
# - switch_template: Try alternative hedge template (e.g., smoothing)
# - skip: Do not hedge if minimum protection cannot be met
PROTECTION_SHORTFALL_FALLBACK: str = "clip_and_report"


# ═══════════════════════════════════════════════════════════════════════════════
# OPTION SELECTION PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# Strike price range as percentage of underlying for OTM put selection.
# MAX: Maximum strike price (closest to ATM) - 5% OTM for reasonable delta
# MIN: Minimum strike price (furthest OTM) - 25% OTM for tail protection
STRIKE_MAX_OTM_RATIO: Decimal = Decimal("0.95")  # Strike <= 95% of underlying
STRIKE_MIN_OTM_RATIO: Decimal = Decimal("0.75")  # Strike >= 75% of underlying

# Limit price discount factor for buy limit orders.
# Set limit price 2% below mid to avoid overpaying while ensuring fills.
LIMIT_PRICE_DISCOUNT_FACTOR: Decimal = Decimal("0.98")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR MAPPER PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# QQQ preference threshold for tech-heavy portfolios.
# If QQQ exposure is >= 80% of max sector exposure, prefer QQQ as primary hedge
# underlying due to higher options liquidity and tech portfolio correlation.
QQQ_PREFERENCE_THRESHOLD: Decimal = Decimal("0.8")


# ═══════════════════════════════════════════════════════════════════════════════
# ROLL MANAGEMENT PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# Critical DTE threshold triggering immediate roll attention.
# Positions below this threshold are flagged as "dte_critical" vs "dte_threshold".
CRITICAL_DTE_THRESHOLD: int = 14


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION SERVICE PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

# Poll interval in seconds when monitoring order fills.
# Affects responsiveness vs API call frequency/cost.
ORDER_POLL_INTERVAL_SECONDS: int = 2


# ═══════════════════════════════════════════════════════════════════════════════
# FALLBACK PRICES
# ═══════════════════════════════════════════════════════════════════════════════
# Default ETF prices used when real-time market data is unavailable.
# These are conservative estimates and should be replaced with live data ASAP.
# TODO: Remove once market data integration is complete.

DEFAULT_ETF_PRICES: dict[str, Decimal] = {
    "QQQ": Decimal("485"),
    "SPY": Decimal("590"),
    "IWM": Decimal("225"),
    "VIXY": Decimal("2.50"),  # VIX proxy ETF (typical range $2-3)
}

# Default price used when ETF symbol is not in DEFAULT_ETF_PRICES
DEFAULT_ETF_PRICE_FALLBACK: Decimal = Decimal("500")


def get_budget_rate_for_vix(vix: Decimal) -> Decimal:
    """Get the appropriate budget rate based on current VIX level.

    Args:
        vix: Current VIX index value

    Returns:
        Budget rate as a percentage of NAV (e.g., 0.008 = 0.8%)

    """
    if vix < VIX_LOW_THRESHOLD:
        return TAIL_HEDGE_TEMPLATE.budget_vix_low
    if vix < VIX_HIGH_THRESHOLD:
        return TAIL_HEDGE_TEMPLATE.budget_vix_mid
    return TAIL_HEDGE_TEMPLATE.budget_vix_high


def get_exposure_multiplier(net_exposure: Decimal) -> Decimal:
    """Calculate budget multiplier based on portfolio net exposure.

    For leveraged portfolios (2.0x-2.5x+), scales the hedge budget
    sublinearly to avoid overpaying at extremes.

    Args:
        net_exposure: Net portfolio exposure ratio (e.g., 2.0 = 2.0x)

    Returns:
        Budget multiplier (1.0 to exposure_max_multiplier)

    Examples:
        >>> get_exposure_multiplier(Decimal("1.0"))
        Decimal('1.0')
        >>> get_exposure_multiplier(Decimal("2.0"))
        Decimal('1.5')  # (1.0 + (2.0-1.0)*0.5) = 1.5

    """
    template = TAIL_HEDGE_TEMPLATE
    excess = max(Decimal("0"), net_exposure - template.exposure_base)
    multiplier = template.exposure_base + (excess * template.exposure_per_excess)
    return min(multiplier, template.exposure_max_multiplier)
