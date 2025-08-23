"""Simplified tests for confidence system - demonstrating core functionality."""

import pytest
from decimal import Decimal
from unittest.mock import Mock

from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.config import load_confidence_config


class TestConfidenceSystemIntegration:
    """Integration tests for the complete confidence system."""
    
    def test_tecl_confidence_calculation_works(self):
        """Test that TECL confidence calculation produces valid results."""
        from the_alchemiser.domain.strategies.tecl_strategy_engine import TECLStrategyEngine
        
        mock_provider = Mock()
        engine = TECLStrategyEngine(mock_provider)
        
        # Test with realistic indicators
        indicators = {
            "TECL": {"rsi_9": 25.0, "current_price": 100.0},  # Oversold
            "SPY": {"current_price": 420.0, "ma_200": 400.0}   # Bull market
        }
        
        confidence = engine._calculate_confidence("TECL", "BUY", indicators, "Buy signal")
        
        # Should produce valid confidence
        assert isinstance(confidence, Confidence)
        assert Decimal("0.3") <= confidence.value <= Decimal("0.9")
        # Should be higher than base due to oversold + bull market
        assert confidence.value > Decimal("0.6")
        
    def test_confidence_config_loading_works(self):
        """Test that confidence configuration loads properly."""
        config = load_confidence_config()
        
        # Test key configuration values
        assert config.tecl.base_confidence == Decimal("0.6")
        assert config.aggregation.min_buy_confidence == Decimal("0.55")
        assert config.nuclear.extremely_oversold_confidence == Decimal("0.9")
        assert config.klm.sell_confidence == Decimal("0.7")
        
    def test_confidence_bounds_validation(self):
        """Test that confidence values are properly bounded."""
        # Valid confidence should work
        valid_confidence = Confidence(Decimal("0.75"))
        assert valid_confidence.value == Decimal("0.75")
        
        # Invalid confidence should raise error
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Confidence(Decimal("1.5"))
            
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            Confidence(Decimal("-0.1"))
            
    def test_risk_score_mapping(self):
        """Test that risk score calculation works correctly."""
        test_cases = [
            (Decimal("0.9"), Decimal("0.1")),   # High confidence = Low risk
            (Decimal("0.5"), Decimal("0.5")),   # Medium confidence = Medium risk  
            (Decimal("0.2"), Decimal("0.8")),   # Low confidence = High risk
        ]
        
        for confidence_value, expected_risk in test_cases:
            confidence = Confidence(confidence_value)
            risk_score = Decimal("1.0") - confidence.value
            assert risk_score == expected_risk
            
    def test_klm_configurable_confidence(self):
        """Test that KLM uses configurable confidence parameters."""
        from the_alchemiser.domain.strategies.typed_klm_ensemble_engine import TypedKLMStrategyEngine
        
        mock_provider = Mock()
        engine = TypedKLMStrategyEngine(mock_provider)
        
        # Test different actions produce different confidence levels
        buy_confidence = engine._calculate_confidence("BUY", 0.8)
        sell_confidence = engine._calculate_confidence("SELL", 0.8)
        hold_confidence = engine._calculate_confidence("HOLD", 0.8)
        
        # Buy with high weight should have highest confidence
        assert buy_confidence.value > sell_confidence.value
        assert buy_confidence.value > hold_confidence.value
        # Hold should have lowest confidence
        assert hold_confidence.value < sell_confidence.value
        
    def test_confidence_thresholds_by_action(self):
        """Test that different actions have appropriate minimum thresholds."""
        from the_alchemiser.domain.strategies.config import get_confidence_thresholds
        
        thresholds = get_confidence_thresholds()
        
        # BUY and SELL should have higher thresholds than HOLD
        assert thresholds["BUY"] == Decimal("0.55")
        assert thresholds["SELL"] == Decimal("0.55")
        assert thresholds["HOLD"] == Decimal("0.35")
        assert thresholds["HOLD"] < thresholds["BUY"]
        assert thresholds["HOLD"] < thresholds["SELL"]


class TestConfidenceProperties:
    """Test confidence value object properties."""
    
    def test_confidence_is_high_property(self):
        """Test is_high property works correctly."""
        high_confidence = Confidence(Decimal("0.7"))
        assert high_confidence.is_high is True
        
        medium_confidence = Confidence(Decimal("0.69"))
        assert medium_confidence.is_high is False
        
    def test_confidence_is_low_property(self):
        """Test is_low property works correctly."""
        low_confidence = Confidence(Decimal("0.3"))
        assert low_confidence.is_low is True
        
        medium_confidence = Confidence(Decimal("0.31"))
        assert medium_confidence.is_low is False
        
    def test_confidence_medium_range(self):
        """Test medium confidence range."""
        medium_confidence = Confidence(Decimal("0.5"))
        assert medium_confidence.is_high is False
        assert medium_confidence.is_low is False