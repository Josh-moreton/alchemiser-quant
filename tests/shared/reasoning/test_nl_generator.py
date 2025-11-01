"""Business Unit: shared | Status: current.

Tests for natural language reasoning generator.
"""

import pytest

from the_alchemiser.shared.reasoning import NaturalLanguageGenerator, ReasoningTemplates


@pytest.mark.unit
class TestReasoningTemplates:
    """Test reasoning templates."""

    @pytest.fixture
    def templates(self):
        """Create templates instance."""
        return ReasoningTemplates()

    def test_get_sentiment_opening_bullish(self, templates):
        """Test bullish sentiment opening."""
        result = templates.get_sentiment_opening("bullish")
        assert result == "Bullish sentiment."

    def test_get_sentiment_opening_bearish(self, templates):
        """Test bearish sentiment opening."""
        result = templates.get_sentiment_opening("bearish")
        assert result == "Bearish sentiment."

    def test_get_sentiment_opening_neutral(self, templates):
        """Test neutral sentiment opening."""
        result = templates.get_sentiment_opening("neutral")
        assert result == "Neutral market conditions."

    def test_get_sentiment_opening_volatile(self, templates):
        """Test volatile sentiment opening."""
        result = templates.get_sentiment_opening("volatile")
        assert result == "High volatility detected."

    def test_get_rsi_description_overbought(self, templates):
        """Test RSI overbought description."""
        result = templates.get_rsi_description("SPY", 82.5, 79.0, ">")
        assert "SPY" in result
        assert "82.5" in result
        assert "79" in result

    def test_get_rsi_description_oversold(self, templates):
        """Test RSI oversold description."""
        result = templates.get_rsi_description("TQQQ", 25.0, 30.0, "<")
        assert "TQQQ" in result
        assert "25.0" in result
        assert "oversold" in result.lower()

    def test_get_ma_description_above(self, templates):
        """Test MA above description."""
        result = templates.get_ma_description("SPY", 450.0, 430.0, 200)
        assert "SPY" in result
        assert "above" in result
        assert "200" in result

    def test_get_ma_description_below(self, templates):
        """Test MA below description."""
        result = templates.get_ma_description("SPY", 420.0, 430.0, 200)
        assert "SPY" in result
        assert "below" in result
        assert "200" in result

    def test_get_allocation_rationale_bullish_tech(self, templates):
        """Test bullish tech allocation rationale."""
        allocation = {"TQQQ": 0.75, "BTAL": 0.25}
        context = {"sentiment": "bullish"}
        result = templates.get_allocation_rationale(allocation, context)
        assert "TQQQ" in result
        assert "tech" in result.lower()

    def test_get_allocation_rationale_bearish_defensive(self, templates):
        """Test bearish defensive allocation rationale."""
        allocation = {"BTAL": 0.75, "TQQQ": 0.25}
        context = {"sentiment": "bearish"}
        result = templates.get_allocation_rationale(allocation, context)
        assert "BTAL" in result
        assert "defensive" in result.lower()


@pytest.mark.unit
class TestNaturalLanguageGenerator:
    """Test natural language generator."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return NaturalLanguageGenerator()

    def test_generate_reasoning_with_empty_path(self, generator):
        """Test generation with empty decision path."""
        result = generator.generate_reasoning([], {"TQQQ": 0.75}, "Nuclear")
        assert "TQQQ" in result or "allocation" in result.lower()

    def test_generate_reasoning_bullish_scenario(self, generator):
        """Test generation for bullish scenario."""
        decision_path = [
            {
                "condition": "SPY > moving_average(SPY, 200)",
                "result": True,
                "branch": "then",
                "values": {},
            },
            {
                "condition": "rsi(SPY, 10) < 79",
                "result": True,
                "branch": "then",
                "values": {},
            },
        ]
        allocation = {"TQQQ": 0.75}

        result = generator.generate_reasoning(decision_path, allocation, "Nuclear")

        # Should be natural language (no technical symbols)
        assert "✓" not in result
        assert "→" not in result
        # Should mention key elements
        assert len(result) > 0

    def test_extract_market_context(self, generator):
        """Test market context extraction."""
        decision_path = [
            {
                "condition": "test condition",
                "result": True,
                "branch": "then",
                "values": {},
                "market_context": "bullish",
            }
        ]

        context = generator._extract_market_context(decision_path)
        assert context["sentiment"] == "bullish"

    def test_infer_sentiment_bullish(self, generator):
        """Test sentiment inference for bullish conditions."""
        decision_path = [
            {
                "condition": "SPY > moving_average",
                "result": True,
                "branch": "then",
                "values": {},
            }
        ]

        sentiment = generator._infer_sentiment_from_decisions(decision_path)
        assert sentiment in ["bullish", "neutral"]  # Could be either depending on threshold

    def test_describe_rsi_condition(self, generator):
        """Test RSI condition description."""
        decision = {
            "condition": "rsi(SPY, 10) < 79",
            "result": True,
            "branch": "then",
            "values": {"SPY_rsi_10": 72.0},
            "symbols_involved": ["SPY"],
            "threshold": 79.0,
            "operator_type": "<",
        }

        result = generator._describe_rsi_condition(decision)
        assert "SPY" in result
        assert len(result) > 0

    def test_describe_ma_condition(self, generator):
        """Test MA condition description."""
        decision = {
            "condition": "SPY > moving_average(SPY, 200)",
            "result": True,
            "branch": "then",
            "values": {},
            "symbols_involved": ["SPY"],
        }

        result = generator._describe_ma_condition(decision)
        assert "SPY" in result
        assert "moving average" in result.lower() or "ma" in result.lower()

    def test_extract_symbol_from_string(self, generator):
        """Test symbol extraction from strings."""
        # Updated: new regex-based extraction finds first valid ticker (filters out RSI)
        assert generator._extract_symbol_from_string("rsi(SPY, 10) > 79") == "SPY"
        assert generator._extract_symbol_from_string("TQQQ allocation") == "TQQQ"
        # Should filter out reserved words and indicator names
        assert generator._extract_symbol_from_string("IF THEN ELSE") == ""
        assert generator._extract_symbol_from_string("RSI MA EMA") == ""  # All filtered
        assert generator._extract_symbol_from_string("SPY AND TQQQ") == "SPY"  # Gets first valid symbol

    def test_compose_narrative(self, generator):
        """Test narrative composition."""
        market_context = {"sentiment": "bullish"}
        conditions = "SPY above its 200-day moving average"
        rationale = "so we buy leveraged tech with TQQQ"

        result = generator._compose_narrative(market_context, conditions, rationale)

        assert "Bullish" in result or "bullish" in result.lower()
        assert "SPY" in result
        assert "TQQQ" in result

    def test_generate_simple_allocation(self, generator):
        """Test simple allocation generation."""
        result = generator._generate_simple_allocation({"TQQQ": 0.75})
        assert "TQQQ" in result
        assert "75" in result or "0.75" in result
