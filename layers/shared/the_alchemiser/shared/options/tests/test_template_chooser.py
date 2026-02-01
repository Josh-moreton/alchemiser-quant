"""Business Unit: shared | Status: current.

Unit tests for TemplateChooser regime-based template selection.

Tests:
- Template selection based on VIX regimes
- Hysteresis prevents excessive switching
- Deterministic rationale generation
- Edge cases and boundary conditions
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.shared.options.template_chooser import (
    RegimeThresholds,
    TemplateChooser,
    TemplateSelectionRationale,
)


class TestTemplateChooser:
    """Test suite for TemplateChooser."""
    
    def test_low_vix_selects_tail_first(self) -> None:
        """Test that low VIX selects tail_first template."""
        chooser = TemplateChooser()
        
        # Low VIX = 15 (below 18 threshold)
        rationale = chooser.choose_template(vix=Decimal("15"))
        
        assert rationale.selected_template == "tail_first"
        assert rationale.regime == "low_iv_normal_skew"
        assert "low" in rationale.reason.lower()
        assert "cheap" in rationale.reason.lower()
    
    def test_mid_vix_selects_tail_first(self) -> None:
        """Test that mid VIX selects tail_first template (default)."""
        chooser = TemplateChooser()
        
        # Mid VIX = 22 (between 18-28)
        rationale = chooser.choose_template(vix=Decimal("22"))
        
        assert rationale.selected_template == "tail_first"
        assert rationale.regime == "mid_iv_moderate_skew"
        assert "moderate" in rationale.reason.lower()
    
    def test_high_vix_selects_smoothing(self) -> None:
        """Test that high VIX selects smoothing template."""
        chooser = TemplateChooser()
        
        # High VIX = 35 (above 28 threshold)
        rationale = chooser.choose_template(vix=Decimal("35"))
        
        assert rationale.selected_template == "smoothing"
        assert rationale.regime == "high_iv_rich_skew"
        assert "high" in rationale.reason.lower()
        assert "expensive" in rationale.reason.lower()
    
    def test_hysteresis_prevents_whipsaw_near_low_threshold(self) -> None:
        """Test hysteresis prevents switching near low VIX threshold.
        
        Low threshold is 18, hysteresis band is 16.2-19.8.
        We test crossing from mid regime (where a switch would occur)
        into the hysteresis band.
        """
        chooser = TemplateChooser()
        
        # Start with VIX = 22 (mid regime) → tail_first
        rationale1 = chooser.choose_template(vix=Decimal("22"))
        assert rationale1.selected_template == "tail_first"
        assert not rationale1.hysteresis_applied
        
        # Move to VIX = 35 (high) → smoothing (establishes different template)
        rationale2 = chooser.choose_template(vix=Decimal("35"))
        assert rationale2.selected_template == "smoothing"
        assert not rationale2.hysteresis_applied
        
        # Move to VIX = 17 (in low band 16.2-19.8, regime would select tail_first)
        # Hysteresis SHOULD apply: we're switching templates AND in the band
        rationale3 = chooser.choose_template(vix=Decimal("17"))
        # VIX 17 is in low_iv_normal_skew regime → tail_first
        # Previous was smoothing, so this IS a template change
        # 17 is in hysteresis band (16.2-19.8), so hysteresis applies
        assert rationale3.selected_template == "smoothing"  # Kept previous due to hysteresis
        assert rationale3.hysteresis_applied
        assert rationale3.previous_template == "smoothing"
    
    def test_hysteresis_prevents_whipsaw_near_high_threshold(self) -> None:
        """Test hysteresis prevents switching near high VIX threshold."""
        chooser = TemplateChooser()
        
        # Start with VIX = 35 (high) → smoothing
        rationale1 = chooser.choose_template(vix=Decimal("35"))
        assert rationale1.selected_template == "smoothing"
        assert not rationale1.hysteresis_applied
        
        # Move to VIX = 27 (just below high threshold but in hysteresis band)
        # Should stick with smoothing due to hysteresis
        rationale2 = chooser.choose_template(vix=Decimal("27"))
        # Hysteresis band is 28 * (1 - 0.10) = 25.2 to 28 * (1 + 0.10) = 30.8
        # 27 is in band, should apply hysteresis
        assert rationale2.selected_template == "smoothing"
        assert rationale2.hysteresis_applied
    
    def test_clear_regime_change_switches_template(self) -> None:
        """Test that clear regime changes switch template."""
        chooser = TemplateChooser()
        
        # Start with VIX = 15 (low) → tail_first
        rationale1 = chooser.choose_template(vix=Decimal("15"))
        assert rationale1.selected_template == "tail_first"
        
        # Jump to VIX = 40 (high, outside hysteresis) → smoothing
        rationale2 = chooser.choose_template(vix=Decimal("40"))
        assert rationale2.selected_template == "smoothing"
        assert not rationale2.hysteresis_applied
    
    def test_edge_case_exactly_at_low_threshold(self) -> None:
        """Test behavior exactly at low VIX threshold."""
        chooser = TemplateChooser()
        
        # VIX = 18 (exactly at threshold)
        rationale = chooser.choose_template(vix=Decimal("18"))
        
        # Should be in mid regime (>= 18 is not low)
        assert rationale.regime == "mid_iv_moderate_skew"
        assert rationale.selected_template == "tail_first"
    
    def test_edge_case_exactly_at_high_threshold(self) -> None:
        """Test behavior exactly at high VIX threshold."""
        chooser = TemplateChooser()
        
        # VIX = 28 (exactly at threshold)
        rationale = chooser.choose_template(vix=Decimal("28"))
        
        # Should be in high regime (>= 28 is high)
        assert rationale.regime == "high_iv_rich_skew"
        assert rationale.selected_template == "smoothing"
    
    def test_custom_thresholds(self) -> None:
        """Test chooser with custom thresholds."""
        custom_thresholds = RegimeThresholds(
            vix_low_threshold=Decimal("15"),
            vix_high_threshold=Decimal("25"),
            hysteresis_pct=Decimal("0.05"),  # 5% hysteresis
        )
        chooser = TemplateChooser(thresholds=custom_thresholds)
        
        # VIX = 20 (between 15-25) → tail_first
        rationale = chooser.choose_template(vix=Decimal("20"))
        assert rationale.selected_template == "tail_first"
        assert rationale.regime == "mid_iv_moderate_skew"
        
        # VIX = 30 (above 25) → smoothing
        rationale = chooser.choose_template(vix=Decimal("30"))
        assert rationale.selected_template == "smoothing"
        assert rationale.regime == "high_iv_rich_skew"
    
    def test_reset_clears_state(self) -> None:
        """Test that reset clears previous template state."""
        chooser = TemplateChooser()
        
        # Select template
        rationale1 = chooser.choose_template(vix=Decimal("15"))
        assert rationale1.selected_template == "tail_first"
        
        # Reset
        chooser.reset()
        
        # Next selection should not have previous template
        rationale2 = chooser.choose_template(vix=Decimal("15"))
        assert rationale2.previous_template is None
    
    def test_rationale_includes_all_fields(self) -> None:
        """Test that rationale includes all expected fields."""
        chooser = TemplateChooser()
        
        rationale = chooser.choose_template(
            vix=Decimal("22"),
            vix_percentile=Decimal("50"),
            skew=Decimal("1.1"),
        )
        
        assert rationale.selected_template in ["tail_first", "smoothing"]
        assert rationale.vix == Decimal("22")
        assert rationale.vix_percentile == Decimal("50")
        assert rationale.skew == Decimal("1.1")
        assert rationale.regime is not None
        assert rationale.reason is not None
        assert isinstance(rationale.hysteresis_applied, bool)
    
    def test_multiple_regime_cycles(self) -> None:
        """Test template selection through multiple regime cycles."""
        chooser = TemplateChooser()
        
        # Cycle: Low → High → Low
        vix_sequence = [
            Decimal("15"),   # Low → tail_first
            Decimal("40"),   # High → smoothing
            Decimal("12"),   # Low → tail_first
        ]
        
        expected_templates = ["tail_first", "smoothing", "tail_first"]
        
        for vix, expected in zip(vix_sequence, expected_templates):
            rationale = chooser.choose_template(vix=vix)
            assert rationale.selected_template == expected
    
    def test_reason_includes_vix_value(self) -> None:
        """Test that reason includes VIX value."""
        chooser = TemplateChooser()
        
        rationale = chooser.choose_template(vix=Decimal("15"))
        
        assert "15" in rationale.reason
        assert "VIX" in rationale.reason or "vix" in rationale.reason.lower()
    
    def test_reason_includes_regime_explanation(self) -> None:
        """Test that reason includes regime explanation."""
        chooser = TemplateChooser()
        
        # Low VIX
        rationale_low = chooser.choose_template(vix=Decimal("15"))
        assert "low" in rationale_low.reason.lower() or "cheap" in rationale_low.reason.lower()
        
        # High VIX
        rationale_high = chooser.choose_template(vix=Decimal("35"))
        assert "high" in rationale_high.reason.lower() or "expensive" in rationale_high.reason.lower()


class TestRegimeThresholds:
    """Test suite for RegimeThresholds configuration."""
    
    def test_default_thresholds(self) -> None:
        """Test default threshold values."""
        thresholds = RegimeThresholds()
        
        assert thresholds.vix_low_threshold == Decimal("18")
        assert thresholds.vix_high_threshold == Decimal("28")
        assert thresholds.hysteresis_pct == Decimal("0.10")
    
    def test_custom_thresholds(self) -> None:
        """Test custom threshold values."""
        thresholds = RegimeThresholds(
            vix_low_threshold=Decimal("20"),
            vix_high_threshold=Decimal("30"),
            hysteresis_pct=Decimal("0.15"),
        )
        
        assert thresholds.vix_low_threshold == Decimal("20")
        assert thresholds.vix_high_threshold == Decimal("30")
        assert thresholds.hysteresis_pct == Decimal("0.15")
    
    def test_thresholds_are_frozen(self) -> None:
        """Test that RegimeThresholds is immutable."""
        thresholds = RegimeThresholds()
        
        with pytest.raises(AttributeError):
            thresholds.vix_low_threshold = Decimal("25")  # type: ignore


class TestTemplateSelectionRationale:
    """Test suite for TemplateSelectionRationale DTO."""
    
    def test_rationale_creation(self) -> None:
        """Test creating rationale object."""
        rationale = TemplateSelectionRationale(
            selected_template="tail_first",
            vix=Decimal("20"),
            vix_percentile=Decimal("60"),
            skew=Decimal("1.15"),
            regime="mid_iv_moderate_skew",
            reason="Test reason",
            previous_template=None,
            hysteresis_applied=False,
        )
        
        assert rationale.selected_template == "tail_first"
        assert rationale.vix == Decimal("20")
        assert rationale.vix_percentile == Decimal("60")
        assert rationale.skew == Decimal("1.15")
        assert rationale.regime == "mid_iv_moderate_skew"
        assert rationale.reason == "Test reason"
        assert rationale.previous_template is None
        assert not rationale.hysteresis_applied
    
    def test_rationale_is_frozen(self) -> None:
        """Test that TemplateSelectionRationale is immutable."""
        rationale = TemplateSelectionRationale(
            selected_template="tail_first",
            vix=Decimal("20"),
            vix_percentile=None,
            skew=None,
            regime="mid_iv_moderate_skew",
            reason="Test",
            previous_template=None,
            hysteresis_applied=False,
        )
        
        with pytest.raises(AttributeError):
            rationale.selected_template = "smoothing"  # type: ignore
