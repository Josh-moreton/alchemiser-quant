"""Tests for typed strategy manager confidence aggregation and conflict resolution."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.domain.registry.strategy_registry import StrategyType
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class TestTypedStrategyManagerAggregation:
    """Test confidence-based aggregation in TypedStrategyManager."""

    @pytest.fixture
    def mock_strategy_manager(self):
        """Create a mock TypedStrategyManager for testing."""
        from the_alchemiser.domain.strategies.typed_strategy_manager import TypedStrategyManager

        # Mock the initialization to avoid complex dependencies
        manager = TypedStrategyManager.__new__(TypedStrategyManager)
        manager.strategy_allocations = {
            StrategyType.NUCLEAR: 0.4,
            StrategyType.TECL: 0.35,
            StrategyType.KLM: 0.25
        }
        manager.logger = Mock()
        return manager

    def test_confidence_gating_filters_low_confidence_signals(self, mock_strategy_manager):
        """Test that signals below minimum confidence thresholds are filtered out."""
        # Create signals with varying confidence levels
        low_confidence_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.45")),  # Below 0.55 BUY threshold
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Low confidence signal",
            timestamp=datetime.now(UTC)
        )

        high_confidence_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.75")),  # Above threshold
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="High confidence signal",
            timestamp=datetime.now(UTC)
        )

        strategy_signals = [
            (StrategyType.NUCLEAR, low_confidence_signal),
            (StrategyType.TECL, high_confidence_signal)
        ]

        result = mock_strategy_manager._select_highest_confidence_signal("AAPL", strategy_signals)

        # Should select the high confidence signal
        assert result.confidence.value == Decimal("0.75")
        assert "GATED" in result.reasoning

    def test_explicit_tie_breaking_by_priority(self, mock_strategy_manager):
        """Test that ties are broken by explicit strategy priority."""
        # Create two signals with identical weighted scores
        nuclear_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.75")),  # 0.75 * 0.4 = 0.3 weighted score
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Nuclear signal",
            timestamp=datetime.now(UTC)
        )

        # Adjust KLM confidence to create identical weighted score: 0.3 / 0.25 = 1.2 (clamped to 0.9)
        klm_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("1.2")),  # This will create same weighted score when clamped
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="KLM signal",
            timestamp=datetime.now(UTC)
        )

        # Manually create identical scores for testing
        klm_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.75")),  # 0.75 * 0.4 = 0.3 for NUCLEAR priority test
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="KLM signal",
            timestamp=datetime.now(UTC)
        )

        # Adjust manager allocations for identical weighted scores
        mock_strategy_manager.strategy_allocations = {
            StrategyType.NUCLEAR: 0.4,  # 0.75 * 0.4 = 0.3
            StrategyType.KLM: 0.4       # 0.75 * 0.4 = 0.3 (identical weighted score)
        }

        strategy_signals = [
            (StrategyType.KLM, klm_signal),      # KLM listed first
            (StrategyType.NUCLEAR, nuclear_signal),  # But NUCLEAR has higher priority
        ]

        result = mock_strategy_manager._select_highest_confidence_signal("AAPL", strategy_signals)

        # Should select NUCLEAR due to priority order despite KLM being first in list
        assert "Nuclear signal" in result.reasoning
        assert "TIE" in result.reasoning
        assert "NUCLEAR" in result.reasoning

    def test_minimum_confidence_thresholds_by_action(self, mock_strategy_manager):
        """Test that different actions have different minimum confidence thresholds."""
        from the_alchemiser.domain.strategies.config import load_confidence_config

        config = load_confidence_config().aggregation

        # Test BUY threshold
        buy_threshold = mock_strategy_manager._get_minimum_confidence_for_action("BUY", config)
        assert buy_threshold == Decimal("0.55")

        # Test SELL threshold
        sell_threshold = mock_strategy_manager._get_minimum_confidence_for_action("SELL", config)
        assert sell_threshold == Decimal("0.55")

        # Test HOLD threshold (should be lower)
        hold_threshold = mock_strategy_manager._get_minimum_confidence_for_action("HOLD", config)
        assert hold_threshold == Decimal("0.35")
        assert hold_threshold < buy_threshold
        assert hold_threshold < sell_threshold

    def test_detailed_score_logging(self, mock_strategy_manager):
        """Test that detailed scoring information is logged when enabled."""
        signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Test signal",
            timestamp=datetime.now(UTC)
        )

        strategy_signals = [(StrategyType.NUCLEAR, signal)]

        result = mock_strategy_manager._select_highest_confidence_signal("AAPL", strategy_signals)

        # Should include detailed scoring in reasoning
        assert "confidence: 0.80" in result.reasoning
        assert "weight: 40.0%" in result.reasoning
        assert "score:" in result.reasoning

    def test_no_signals_meet_threshold_fallback(self, mock_strategy_manager):
        """Test fallback behavior when no signals meet minimum confidence."""
        # Create signals all below threshold
        low_signal_1 = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.4")),  # Below 0.55 threshold
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Low signal 1",
            timestamp=datetime.now(UTC)
        )

        low_signal_2 = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.3")),  # Below 0.55 threshold
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="Low signal 2",
            timestamp=datetime.now(UTC)
        )

        strategy_signals = [
            (StrategyType.NUCLEAR, low_signal_1),
            (StrategyType.TECL, low_signal_2)
        ]

        result = mock_strategy_manager._select_highest_confidence_signal("AAPL", strategy_signals)

        # Should still return a result using fallback logic
        assert result is not None
        assert "No signals meet minimum confidence thresholds" in result.reasoning

    def test_combine_agreeing_signals_weighted_confidence(self, mock_strategy_manager):
        """Test that agreeing signals are combined with weighted confidence average."""
        signal_1 = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Signal 1",
            timestamp=datetime.now(UTC)
        )

        signal_2 = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",  # Same action = agreeing
            confidence=Confidence(Decimal("0.6")),
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="Signal 2",
            timestamp=datetime.now(UTC)
        )

        strategy_signals = [
            (StrategyType.NUCLEAR, signal_1),  # weight 0.4
            (StrategyType.TECL, signal_2)      # weight 0.35
        ]

        result = mock_strategy_manager._combine_agreeing_signals("AAPL", strategy_signals)

        # Calculate expected weighted average: (0.8*0.4 + 0.6*0.35) / (0.4+0.35) = 0.72
        expected_confidence = (Decimal("0.8") * Decimal("0.4") + Decimal("0.6") * Decimal("0.35")) / (Decimal("0.4") + Decimal("0.35"))

        assert result.confidence.value == pytest.approx(float(expected_confidence), rel=1e-6)
        assert "Combined signal" in result.reasoning

    def test_tie_breaking_priority_order(self, mock_strategy_manager):
        """Test that tie breaking follows configured priority order."""
        from the_alchemiser.domain.strategies.config import AggregationConfig

        config = AggregationConfig()

        # Create signals for tie-breaking test
        nuclear_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="Nuclear signal",
            timestamp=datetime.now(UTC)
        )

        tecl_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="TECL signal",
            timestamp=datetime.now(UTC)
        )

        tied_signals = [
            (StrategyType.TECL, tecl_signal),
            (StrategyType.NUCLEAR, nuclear_signal)
        ]

        winner_type, winner_signal = mock_strategy_manager._break_tie(tied_signals, config)

        # NUCLEAR should win due to priority order ("NUCLEAR", "TECL", "KLM")
        assert winner_type == StrategyType.NUCLEAR
        assert winner_signal.reasoning == "Nuclear signal"


class TestConfidenceCalculationIntegration:
    """Test confidence calculation with risk mapping validation."""

    def test_risk_score_calculation_mapping(self):
        """Test that risk_score = 1 - confidence mapping is validated."""
        from the_alchemiser.domain.strategies.value_objects.confidence import Confidence

        # Test various confidence levels
        test_cases = [
            (Decimal("0.9"), Decimal("0.1")),   # High confidence = Low risk
            (Decimal("0.7"), Decimal("0.3")),   # Medium confidence = Medium risk
            (Decimal("0.3"), Decimal("0.7")),   # Low confidence = High risk
            (Decimal("0.0"), Decimal("1.0")),   # No confidence = Max risk
            (Decimal("1.0"), Decimal("0.0")),   # Full confidence = No risk
        ]

        for confidence_value, expected_risk in test_cases:
            confidence = Confidence(confidence_value)
            risk_score = Decimal("1.0") - confidence.value

            assert risk_score == expected_risk
            assert Decimal("0.0") <= risk_score <= Decimal("1.0")

    def test_confidence_properties_thresholds(self):
        """Test confidence property thresholds for is_high and is_low."""
        # Test high confidence boundary
        high_confidence = Confidence(Decimal("0.7"))
        assert high_confidence.is_high is True
        assert high_confidence.is_low is False

        just_below_high = Confidence(Decimal("0.69"))
        assert just_below_high.is_high is False

        # Test low confidence boundary
        low_confidence = Confidence(Decimal("0.3"))
        assert low_confidence.is_low is True
        assert low_confidence.is_high is False

        just_above_low = Confidence(Decimal("0.31"))
        assert just_above_low.is_low is False

        # Test medium confidence
        medium_confidence = Confidence(Decimal("0.5"))
        assert medium_confidence.is_high is False
        assert medium_confidence.is_low is False
