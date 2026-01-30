"""Business Unit: shared | Status: current.

Template chooser for options hedging strategies.

Provides deterministic logic for selecting between tail_first and smoothing
templates based on market regime indicators (IV percentile, skew).

Key Features:
- Deterministic template selection based on VIX and skew
- Hysteresis to prevent excessive whipsaw between templates
- Structured logging of selection rationale
- Backtestable with historical regime data
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Template type alias
TemplateType = Literal["tail_first", "smoothing"]


@dataclass(frozen=True)
class RegimeThresholds:
    """Thresholds for regime classification.

    These thresholds determine when to switch between tail_first and smoothing
    templates based on market conditions.
    """

    # VIX thresholds for IV regime classification
    vix_low_threshold: Decimal = Decimal("18")  # Below = cheap options
    vix_high_threshold: Decimal = Decimal("28")  # Above = expensive options

    # Skew thresholds (placeholder - not yet implemented)
    # Future: Add put/call skew metrics from option chain data
    # For now, we use VIX as a proxy for both IV level and skew richness
    skew_normal_threshold: Decimal = Decimal("1.0")  # Placeholder
    skew_rich_threshold: Decimal = Decimal("1.2")  # Placeholder

    # Hysteresis band to prevent whipsaw (% of threshold)
    hysteresis_pct: Decimal = Decimal("0.10")  # 10% hysteresis band


@dataclass(frozen=True)
class TemplateSelectionRationale:
    """Rationale for template selection.

    Contains all metrics and logic used to select a template,
    for logging and debugging purposes.
    """

    selected_template: TemplateType
    vix: Decimal
    vix_percentile: Decimal | None  # Future: historical percentile
    skew: Decimal | None  # Future: put/call skew metric
    regime: str  # e.g., "low_iv_normal_skew", "high_iv_rich_skew"
    reason: str  # Human-readable explanation
    previous_template: TemplateType | None
    hysteresis_applied: bool


class TemplateChooser:
    """Chooses hedge template based on market regime.

    Implements deterministic logic for selecting between tail_first and
    smoothing templates based on IV percentile and skew indicators.

    Selection Logic:
    - Low IV percentile + normal skew → tail_first (cheap tails)
    - High IV + rich skew → smoothing (spreads reduce cost)
    - Hysteresis prevents rapid switching

    Attributes:
        thresholds: Regime classification thresholds
        _last_template: Last selected template (for hysteresis)

    """

    def __init__(
        self,
        thresholds: RegimeThresholds | None = None,
    ) -> None:
        """Initialize template chooser.

        Args:
            thresholds: Optional custom thresholds (uses defaults if None)

        """
        self.thresholds = thresholds or RegimeThresholds()
        self._last_template: TemplateType | None = None

    def choose_template(
        self,
        vix: Decimal,
        vix_percentile: Decimal | None = None,
        skew: Decimal | None = None,
    ) -> TemplateSelectionRationale:
        """Choose hedge template based on current market regime.

        Args:
            vix: Current VIX index value
            vix_percentile: Optional VIX percentile (0-100) from historical data
            skew: Optional put/call skew metric

        Returns:
            TemplateSelectionRationale with selected template and reasoning

        """
        # Classify regime based on available metrics
        regime = self._classify_regime(vix, vix_percentile, skew)

        # Select template based on regime
        selected_template = self._select_template_for_regime(regime, vix)

        # Apply hysteresis to prevent whipsaw
        final_template, hysteresis_applied = self._apply_hysteresis(selected_template, vix)

        # Generate human-readable reason
        reason = self._generate_reason(
            regime, vix, vix_percentile, skew, hysteresis_applied=hysteresis_applied
        )

        # Create rationale object
        rationale = TemplateSelectionRationale(
            selected_template=final_template,
            vix=vix,
            vix_percentile=vix_percentile,
            skew=skew,
            regime=regime,
            reason=reason,
            previous_template=self._last_template,
            hysteresis_applied=hysteresis_applied,
        )

        # Update last template
        self._last_template = final_template

        # Log selection
        logger.info(
            "Template selected",
            template=final_template,
            regime=regime,
            vix=str(vix),
            vix_percentile=str(vix_percentile) if vix_percentile else None,
            skew=str(skew) if skew else None,
            reason=reason,
            hysteresis_applied=hysteresis_applied,
            previous_template=self._last_template,
        )

        return rationale

    def _classify_regime(
        self,
        vix: Decimal,
        vix_percentile: Decimal | None,
        skew: Decimal | None,
    ) -> str:
        """Classify market regime based on IV and skew metrics.

        Args:
            vix: Current VIX value
            vix_percentile: Optional VIX percentile from historical data
            skew: Optional put/call skew metric

        Returns:
            Regime classification string

        """
        # For now, use VIX as primary regime indicator
        # Future: Incorporate vix_percentile and skew when available

        if vix < self.thresholds.vix_low_threshold:
            # Low VIX = cheap options = good time for tail protection
            return "low_iv_normal_skew"
        if vix < self.thresholds.vix_high_threshold:
            # Mid VIX = moderate pricing = keep current strategy
            return "mid_iv_moderate_skew"
        # High VIX = expensive options = prefer spreads
        return "high_iv_rich_skew"

    def _select_template_for_regime(
        self,
        regime: str,
        vix: Decimal,
    ) -> TemplateType:
        """Select template based on regime classification.

        Args:
            regime: Regime classification string
            vix: Current VIX value

        Returns:
            Selected template type

        """
        if regime == "low_iv_normal_skew":
            # Low IV + normal skew → tail_first (cheap tails)
            return "tail_first"
        if regime == "high_iv_rich_skew":
            # High IV + rich skew → smoothing (spreads reduce cost)
            return "smoothing"
        # Mid IV → prefer tail_first (default to more protection)
        # This is the neutral regime - keep protection bias
        return "tail_first"

    def _apply_hysteresis(
        self,
        selected_template: TemplateType,
        vix: Decimal,
    ) -> tuple[TemplateType, bool]:
        """Apply hysteresis to prevent excessive switching.

        If we're near a threshold and recently used a different template,
        stick with the previous template to avoid whipsaw.

        Args:
            selected_template: Template selected by regime logic
            vix: Current VIX value

        Returns:
            Tuple of (final_template, hysteresis_applied)

        """
        # If no previous template, use selected
        if self._last_template is None:
            return selected_template, False

        # If templates match, no hysteresis needed
        if selected_template == self._last_template:
            return selected_template, False

        # Check if we're in hysteresis band near thresholds
        low_band_min = self.thresholds.vix_low_threshold * (
            Decimal("1") - self.thresholds.hysteresis_pct
        )
        low_band_max = self.thresholds.vix_low_threshold * (
            Decimal("1") + self.thresholds.hysteresis_pct
        )
        high_band_min = self.thresholds.vix_high_threshold * (
            Decimal("1") - self.thresholds.hysteresis_pct
        )
        high_band_max = self.thresholds.vix_high_threshold * (
            Decimal("1") + self.thresholds.hysteresis_pct
        )

        # Check if VIX is in either hysteresis band
        in_low_band = low_band_min <= vix <= low_band_max
        in_high_band = high_band_min <= vix <= high_band_max

        if in_low_band or in_high_band:
            # In hysteresis band - stick with previous template
            logger.info(
                "Applying hysteresis to prevent template whipsaw",
                vix=str(vix),
                selected_template=selected_template,
                previous_template=self._last_template,
                hysteresis_band="low" if in_low_band else "high",
            )
            return self._last_template, True

        # Outside hysteresis band - use selected template
        return selected_template, False

    def _generate_reason(
        self,
        regime: str,
        vix: Decimal,
        vix_percentile: Decimal | None,
        skew: Decimal | None,
        *,
        hysteresis_applied: bool,
    ) -> str:
        """Generate human-readable reason for template selection.

        Args:
            regime: Regime classification
            vix: Current VIX value
            vix_percentile: Optional VIX percentile
            skew: Optional skew metric
            hysteresis_applied: Whether hysteresis was applied

        Returns:
            Human-readable reason string

        """
        parts = []

        # VIX level
        if vix < self.thresholds.vix_low_threshold:
            parts.append(f"VIX = {vix} (low, cheap options)")
        elif vix < self.thresholds.vix_high_threshold:
            parts.append(f"VIX = {vix} (moderate)")
        else:
            parts.append(f"VIX = {vix} (high, expensive options)")

        # VIX percentile (if available)
        if vix_percentile is not None:
            parts.append(f"IV percentile = {vix_percentile}%")

        # Skew (if available)
        if skew is not None:
            parts.append(f"skew = {skew}")

        # Regime
        regime_desc = {
            "low_iv_normal_skew": "Low IV regime favors tail protection",
            "mid_iv_moderate_skew": "Moderate IV regime maintains protection",
            "high_iv_rich_skew": "High IV regime favors spreads for cost efficiency",
        }.get(regime, f"Regime: {regime}")
        parts.append(regime_desc)

        # Hysteresis
        if hysteresis_applied:
            parts.append("Hysteresis applied to prevent whipsaw")

        return "; ".join(parts)

    def reset(self) -> None:
        """Reset chooser state (useful for testing)."""
        self._last_template = None
