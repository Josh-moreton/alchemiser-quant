"""Business Unit: shared | Status: current.

Integration tests for natural language reasoning generation.
"""

import pytest

from the_alchemiser.shared.reasoning import NaturalLanguageGenerator


@pytest.mark.integration
class TestNaturalLanguageGenerationIntegration:
    """Integration tests for end-to-end natural language generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return NaturalLanguageGenerator()

    def test_bullish_tech_scenario(self, generator):
        """Test complete bullish tech allocation scenario."""
        # Simulate decision path from Nuclear strategy evaluation
        decision_path = [
            {
                "condition": "current_price(SPY) > moving_average_price(SPY, {:window 200})",
                "result": True,
                "branch": "then",
                "values": {"SPY_current_price": 450.0, "SPY_moving_average_price_200": 430.0},
                "condition_type": "ma_comparison",
                "symbols_involved": ["SPY"],
                "operator_type": "greater_than",
                "indicator_name": "moving_average_price",
                "indicator_params": {"window": 200},
            },
            {
                "condition": "rsi(SPY, {:window 10}) < 79",
                "result": True,
                "branch": "then",
                "values": {"SPY_rsi_10": 72.0},
                "condition_type": "rsi_check",
                "symbols_involved": ["SPY"],
                "operator_type": "less_than",
                "threshold": 79.0,
                "indicator_name": "rsi",
                "indicator_params": {"window": 10},
            },
            {
                "condition": "rsi(TQQQ, {:window 10}) < 81",
                "result": True,
                "branch": "then",
                "values": {"TQQQ_rsi_10": 75.0},
                "condition_type": "rsi_check",
                "symbols_involved": ["TQQQ"],
                "operator_type": "less_than",
                "threshold": 81.0,
                "indicator_name": "rsi",
                "indicator_params": {"window": 10},
            },
        ]

        allocation = {"TQQQ": 0.75, "BTAL": 0.25}

        result = generator.generate_reasoning(decision_path, allocation, "Nuclear")

        # Verify natural language output
        assert "✓" not in result, "Should not contain technical symbols"
        assert "→" not in result, "Should not contain arrow symbols"
        assert len(result) > 0, "Should generate non-empty narrative"
        assert len(result) < 500, "Should be concise"

        # Should mention key elements (at least some of them)
        has_sentiment = any(
            word in result.lower() for word in ["bullish", "bearish", "neutral", "volatile"]
        )
        has_symbol = any(symbol in result for symbol in ["SPY", "TQQQ"])

        assert has_sentiment or has_symbol, "Should mention sentiment or symbols"

    def test_bearish_defensive_scenario(self, generator):
        """Test bearish defensive positioning scenario."""
        decision_path = [
            {
                "condition": "current_price(SPY) < moving_average_price(SPY, {:window 200})",
                "result": True,
                "branch": "then",
                "values": {"SPY_current_price": 420.0, "SPY_moving_average_price_200": 430.0},
                "condition_type": "ma_comparison",
                "symbols_involved": ["SPY"],
                "operator_type": "less_than",
            },
            {
                "condition": "max_drawdown(TQQQ, {:window 60}) > 0.10",
                "result": True,
                "branch": "then",
                "values": {"TQQQ_max_drawdown_60": 0.15},
                "condition_type": "max_drawdown_check",
                "symbols_involved": ["TQQQ"],
                "operator_type": "greater_than",
                "threshold": 0.10,
            },
        ]

        allocation = {"BTAL": 1.0}

        result = generator.generate_reasoning(decision_path, allocation, "Nuclear")

        # Verify natural language output
        assert "✓" not in result
        assert "→" not in result
        assert len(result) > 0
        assert "BTAL" in result or "defensive" in result.lower()

    def test_volatile_hedge_scenario(self, generator):
        """Test high volatility hedge scenario."""
        decision_path = [
            {
                "condition": "rsi(SPY, {:window 10}) > 81",
                "result": True,
                "branch": "then",
                "values": {"SPY_rsi_10": 82.5},
                "condition_type": "rsi_check",
                "symbols_involved": ["SPY"],
                "operator_type": "greater_than",
                "threshold": 81.0,
            },
            {
                "condition": "current_price(VIX) > 30",
                "result": True,
                "branch": "then",
                "values": {"VIX_current_price": 35.0},
                "symbols_involved": ["VIX"],
                "operator_type": "greater_than",
                "threshold": 30.0,
            },
        ]

        allocation = {"UVXY": 0.50, "CASH": 0.50}

        result = generator.generate_reasoning(decision_path, allocation, "Nuclear")

        # Verify natural language output
        assert "✓" not in result
        assert "→" not in result
        assert len(result) > 0

    def test_minimal_decision_path(self, generator):
        """Test with minimal decision path (no metadata)."""
        decision_path = [
            {
                "condition": "some condition",
                "result": True,
                "branch": "then",
                "values": {},
            }
        ]

        allocation = {"TQQQ": 0.75}

        result = generator.generate_reasoning(decision_path, allocation, "Strategy")

        # Should still generate something reasonable
        assert len(result) > 0
        assert "✓" not in result
        assert "→" not in result

    def test_empty_decision_path(self, generator):
        """Test with empty decision path."""
        result = generator.generate_reasoning([], {"TQQQ": 0.75}, "Strategy")

        # Should generate simple allocation description
        assert len(result) > 0
        assert "TQQQ" in result
        assert "75" in result or "0.75" in result

    def test_multiple_symbols_allocation(self, generator):
        """Test with multiple symbols in allocation."""
        decision_path = [
            {
                "condition": "balanced allocation",
                "result": True,
                "branch": "then",
                "values": {},
            }
        ]

        allocation = {"TQQQ": 0.40, "FNGU": 0.35, "BTAL": 0.25}

        result = generator.generate_reasoning(decision_path, allocation, "MultiStrat")

        assert len(result) > 0
        # Should mention primary symbol
        assert "TQQQ" in result or "allocation" in result.lower()

    def test_reasoning_length_constraint(self, generator):
        """Test that reasoning respects length constraints."""
        # Create a long decision path
        decision_path = [
            {
                "condition": f"condition_{i} with long description",
                "result": True,
                "branch": "then",
                "values": {},
            }
            for i in range(20)
        ]

        allocation = {"TQQQ": 0.75}

        result = generator.generate_reasoning(decision_path, allocation, "Strategy")

        # Should be reasonably concise (under 1000 chars as per StrategySignal.reasoning)
        assert len(result) < 1000, "Reasoning should be under 1000 characters"

    def test_special_characters_handling(self, generator):
        """Test handling of special characters in conditions."""
        decision_path = [
            {
                "condition": "price > threshold && rsi < 70",
                "result": True,
                "branch": "then",
                "values": {},
                "symbols_involved": ["SPY"],
            }
        ]

        allocation = {"SPY": 1.0}

        result = generator.generate_reasoning(decision_path, allocation, "Strategy")

        # Should handle special characters gracefully
        assert len(result) > 0
        assert "✓" not in result
        assert "→" not in result
