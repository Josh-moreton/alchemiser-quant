"""Business Unit: shared | Status: current.

Partial bar indicator configuration and eligibility classification.

This module classifies all indicators by their suitability for partial-bar
evaluation (using today's incomplete bar with close-so-far as the latest price).

Classification Criteria:
- Input requirements: CLOSE_ONLY vs OHLC vs OHLCV
- Partial bar eligibility: Whether indicator remains well-defined with incomplete data
- Edge cases: Adjusted prices, missing intraday data, session calendar issues
- Modification notes: Changes needed to support partial bar evaluation

All indicators in the Alchemiser system currently use CLOSE prices only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InputRequirement(str, Enum):
    """Data inputs required by an indicator.

    Attributes:
        CLOSE_ONLY: Only close prices required (current implementation)
        OHLC: Open, High, Low, Close required
        OHLCV: Open, High, Low, Close, Volume required

    """

    CLOSE_ONLY = "close_only"
    OHLC = "ohlc"
    OHLCV = "ohlcv"


class PartialBarEligibility(str, Enum):
    """Eligibility for partial-bar (close-so-far) evaluation.

    Attributes:
        YES: Indicator works correctly with partial bar close-so-far
        NO: Indicator requires completed bars only
        CONDITIONAL: Indicator works but with caveats (e.g., increased variance)

    """

    YES = "yes"
    NO = "no"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class PartialBarIndicatorConfig:
    """Configuration for an indicator's partial-bar support.

    Attributes:
        indicator_name: DSL operator name (e.g., "rsi", "current-price")
        indicator_type: Internal type name used by IndicatorService
        module_path: Python module containing the implementation
        function_name: Function or method name in TechnicalIndicators
        input_requirement: Data inputs required (CLOSE_ONLY/OHLC/OHLCV)
        current_behavior: Description of how indicator currently handles bars
        eligible_for_partial_bar: Whether partial bar is supported
        modification_notes: What changes are needed for partial bar support
        use_live_bar: Whether to include live/partial bar in computation
        edge_cases: Known edge cases that cause divergence or issues

    """

    indicator_name: str
    indicator_type: str
    module_path: str
    function_name: str
    input_requirement: InputRequirement
    current_behavior: str
    eligible_for_partial_bar: PartialBarEligibility
    modification_notes: str
    use_live_bar: bool = True  # Default: include live bar (opt-out per indicator)
    edge_cases: tuple[str, ...] = field(default_factory=tuple)


# ==============================================================================
# INDICATOR CLASSIFICATION REGISTRY
# ==============================================================================
# Each indicator is classified by:
# 1. Required inputs (all current indicators use CLOSE_ONLY)
# 2. Partial bar eligibility (whether indicator works with incomplete bar)
# 3. Edge cases that may cause divergence between backtest and live
# ==============================================================================

_INDICATOR_CONFIGS: dict[str, PartialBarIndicatorConfig] = {
    # -------------------------------------------------------------------------
    # CLOSE-ONLY FAMILY: All current indicators
    # -------------------------------------------------------------------------
    "current_price": PartialBarIndicatorConfig(
        indicator_name="current-price",
        indicator_type="current_price",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="N/A (returns prices.iloc[-1])",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Returns the latest close price from the bar series. "
        "When live bar is appended, returns today's close-so-far.",
        eligible_for_partial_bar=PartialBarEligibility.YES,
        modification_notes="No modifications needed. Already works with partial bars "
        "because it simply returns the latest close value regardless of completeness.",
        use_live_bar=True,  # Always use live bar - must return today's current price
        edge_cases=(
            "Stale price if market closed and cache not updated",
            "Pre-market/after-hours price may differ from regular session",
        ),
    ),
    "rsi": PartialBarIndicatorConfig(
        indicator_name="rsi",
        indicator_type="rsi",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.rsi",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes RSI using Wilder's smoothing over close prices. "
        "Uses ewm() which processes all bars including the latest.",
        eligible_for_partial_bar=PartialBarEligibility.CONDITIONAL,
        modification_notes="Works with partial bar but RSI will be more volatile intraday. "
        "The partial bar's close-so-far contributes to the gain/loss calculation. "
        "Consider adding metadata flag to indicate partial bar was used.",
        use_live_bar=True,  # RSI too volatile with partial bars
        edge_cases=(
            "RSI may jump significantly near market open when close-so-far equals open",
            "Intraday RSI variance higher than end-of-day due to price swings",
            "Early in session (first 30 min), high/low may not yet be established",
        ),
    ),
    "moving_average": PartialBarIndicatorConfig(
        indicator_name="moving-average-price",
        indicator_type="moving_average",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.moving_average",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes simple moving average over close prices using "
        "rolling().mean(). Requires min_periods=window to produce non-NaN values.",
        eligible_for_partial_bar=PartialBarEligibility.YES,
        modification_notes="Works with partial bar. The partial close contributes 1/N "
        "weight to the average. Effect is minimal for large windows (e.g., 200-day).",
        use_live_bar=True,  # T-1 mode: exclude live bar (validated 2026-01-16)
        edge_cases=(
            "For short windows (5-20 days), partial bar has higher relative impact",
            "Gap up/down at open creates larger deviation from yesterday's close-based MA",
        ),
    ),
    "exponential_moving_average_price": PartialBarIndicatorConfig(
        indicator_name="exponential-moving-average-price",
        indicator_type="exponential_moving_average_price",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.exponential_moving_average",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes EMA using ewm(span=window). More weight on recent "
        "prices means partial bar has higher influence than in SMA.",
        eligible_for_partial_bar=PartialBarEligibility.CONDITIONAL,
        modification_notes="Works but partial bar has higher weight due to exponential decay. "
        "Short-term EMAs (8, 12) will show more intraday variance than long-term (50, 200).",
        use_live_bar=True,  # EMA gives too much weight to partial bar
        edge_cases=(
            "EMA crossover signals may flip intraday then revert by close",
            "For EMA-8 vs SMA-10 comparisons, timing of evaluation matters significantly",
        ),
    ),
    "moving_average_return": PartialBarIndicatorConfig(
        indicator_name="moving-average-return",
        indicator_type="moving_average_return",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.moving_average_return",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes rolling mean of pct_change(). The partial bar's "
        "return (close-so-far vs yesterday's close) is included in the average.",
        eligible_for_partial_bar=PartialBarEligibility.CONDITIONAL,
        modification_notes="Works but today's return is incomplete. Early in session, "
        "today's return is (close-so-far / yesterday_close - 1) which may not reflect "
        "final daily return. Impact depends on window size.",
        use_live_bar=True,  # T-1 mode: exclude live bar (validated 2026-01-16)
        edge_cases=(
            "Morning volatility causes today's return to swing significantly",
            "Rolling average may differ from EOD value if session ends differently",
        ),
    ),
    "cumulative_return": PartialBarIndicatorConfig(
        indicator_name="cumulative-return",
        indicator_type="cumulative_return",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.cumulative_return",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes ((current_price / price_N_days_ago) - 1) * 100. "
        "Uses shift(window) to get historical reference price.",
        eligible_for_partial_bar=PartialBarEligibility.YES,
        modification_notes="Works well with partial bar. Compares today's close-so-far "
        "to the close from N days ago. This is the intended behavior for momentum signals.",
        use_live_bar=True,  # T-1 mode: exclude live bar (validated 2026-01-16)
        edge_cases=(
            "Reference price (N days ago) must be from a completed bar",
            "For window=60, comparing to price from ~3 months ago is stable",
        ),
    ),
    "stdev_return": PartialBarIndicatorConfig(
        indicator_name="stdev-return",
        indicator_type="stdev_return",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.stdev_return",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes rolling std of pct_change(). Today's return "
        "(close-so-far vs yesterday) is included in the volatility calculation.",
        eligible_for_partial_bar=PartialBarEligibility.CONDITIONAL,
        modification_notes="Works but today's incomplete return may skew volatility. "
        "If today has unusually high intraday range, stdev will spike. "
        "For short windows (6 days), this effect is pronounced.",
        use_live_bar=True,  # T-1 mode: exclude live bar (validated 2026-01-16)
        edge_cases=(
            "Flash crash or spike intraday inflates volatility reading",
            "Near market open, return is small (close-so-far ≈ open)",
            "Volatility reading changes significantly throughout the day",
        ),
    ),
    "stdev_price": PartialBarIndicatorConfig(
        indicator_name="stdev-price",
        indicator_type="stdev_price",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.stdev_price",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes rolling std of raw close prices. Today's "
        "close-so-far is included in the standard deviation calculation.",
        eligible_for_partial_bar=PartialBarEligibility.CONDITIONAL,
        modification_notes="Works but today's price may increase variance reading. "
        "Unlike stdev_return, this uses absolute prices so gap effects are included.",
        use_live_bar=True,  # Price stdev too sensitive to partial bars
        edge_cases=(
            "Large gap up/down increases price stdev immediately at open",
            "Trending price action may show lower stdev than mean-reverting action",
        ),
    ),
    "max_drawdown": PartialBarIndicatorConfig(
        indicator_name="max-drawdown",
        indicator_type="max_drawdown",
        module_path="functions.strategy_worker.indicators.indicators",
        function_name="TechnicalIndicators.max_drawdown",
        input_requirement=InputRequirement.CLOSE_ONLY,
        current_behavior="Computes rolling max drawdown using cummax(). Today's "
        "close-so-far extends the price series for peak-to-trough calculation.",
        eligible_for_partial_bar=PartialBarEligibility.YES,
        modification_notes="Works well with partial bar. If today's close-so-far is "
        "below the rolling high, drawdown increases. If it sets a new high, drawdown "
        "may decrease. This reflects real-time risk exposure.",
        use_live_bar=True,  # T-1 mode: exclude live bar (validated 2026-01-16)
        edge_cases=(
            "Intraday drawdown may exceed EOD drawdown if price recovers later",
            "New all-time high intraday resets drawdown to 0 even if price falls later",
        ),
    ),
}


def get_indicator_config(indicator_type: str) -> PartialBarIndicatorConfig | None:
    """Get partial bar configuration for an indicator.

    Args:
        indicator_type: Internal indicator type (e.g., "rsi", "moving_average")

    Returns:
        PartialBarIndicatorConfig if found, None otherwise

    """
    return _INDICATOR_CONFIGS.get(indicator_type)


def get_all_indicator_configs() -> dict[str, PartialBarIndicatorConfig]:
    """Get all indicator configurations.

    Returns:
        Dictionary mapping indicator_type to PartialBarIndicatorConfig

    """
    return dict(_INDICATOR_CONFIGS)


def is_eligible_for_partial_bar(indicator_type: str) -> bool:
    """Check if an indicator is eligible for partial bar evaluation.

    Args:
        indicator_type: Internal indicator type

    Returns:
        True if indicator can use partial bar (YES or CONDITIONAL),
        False if indicator requires complete bars only (NO),
        True by default if indicator is unknown (permissive)

    """
    config = get_indicator_config(indicator_type)
    if config is None:
        # Unknown indicator - allow partial bar by default
        return True
    return config.eligible_for_partial_bar in (
        PartialBarEligibility.YES,
        PartialBarEligibility.CONDITIONAL,
    )


def should_use_live_bar(indicator_type: str) -> bool:
    """Check if an indicator should include live/partial bars in computation.

    This provides per-indicator control over whether the live bar (today's
    close-so-far) is included when computing the indicator. Some indicators
    like RSI are too volatile with partial bars and should exclude them.

    Args:
        indicator_type: Internal indicator type (e.g., "rsi", "moving_average")

    Returns:
        True if indicator should include live bars (default for unknown indicators),
        False if indicator should exclude live/partial bars from computation

    Example:
        >>> should_use_live_bar("moving_average")  # Simple average - stable
        True
        >>> should_use_live_bar("rsi")  # Too volatile with partial bars
        False

    """
    config = get_indicator_config(indicator_type)
    if config is None:
        # Unknown indicator - include live bar by default
        return True
    return config.use_live_bar
