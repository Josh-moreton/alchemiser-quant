"""Test the StrategyAttributionEngine."""

from decimal import Decimal
from unittest.mock import Mock

from the_alchemiser.domain.portfolio.strategy_attribution.attribution_engine import (
    StrategyAttributionEngine,
)
from the_alchemiser.domain.portfolio.strategy_attribution.symbol_classifier import SymbolClassifier


class TestStrategyAttributionEngine:
    """Test cases for StrategyAttributionEngine."""

    def test_init_with_classifier(self):
        """Test initialization with a classifier."""
        classifier = Mock(spec=SymbolClassifier)
        engine = StrategyAttributionEngine(classifier)
        assert engine.classifier is classifier

    def test_init_without_classifier(self):
        """Test initialization without a classifier creates default."""
        engine = StrategyAttributionEngine()
        assert isinstance(engine.classifier, SymbolClassifier)

    def test_classify_symbol(self):
        """Test symbol classification delegation."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.return_value = "large_cap"

        engine = StrategyAttributionEngine(mock_classifier)
        result = engine.classify_symbol("AAPL")

        mock_classifier.classify_symbol.assert_called_once_with("AAPL")
        assert result == "large_cap"

    def test_get_strategy_for_symbol(self):
        """Test getting strategy for a symbol."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.return_value = "large_cap"

        engine = StrategyAttributionEngine(mock_classifier)
        result = engine.get_strategy_for_symbol("AAPL")

        assert result == "large_cap"

    def test_group_positions_by_strategy(self):
        """Test grouping positions by their strategies."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.side_effect = lambda symbol: {
            "AAPL": "large_cap",
            "MSFT": "large_cap",
            "TSLA": "mid_cap",
            "NVDA": "large_cap",
            "RBLX": "small_cap",
        }.get(symbol, "unknown")

        engine = StrategyAttributionEngine(mock_classifier)

        positions = {
            "AAPL": Decimal("5000"),
            "MSFT": Decimal("3000"),
            "TSLA": Decimal("2000"),
            "NVDA": Decimal("4000"),
            "RBLX": Decimal("1000"),
        }

        grouped = engine.group_positions_by_strategy(positions)

        assert len(grouped) == 3
        assert "large_cap" in grouped
        assert "mid_cap" in grouped
        assert "small_cap" in grouped

        # Large cap should have AAPL, MSFT, NVDA
        large_cap = grouped["large_cap"]
        assert len(large_cap) == 3
        assert large_cap["AAPL"] == Decimal("5000")
        assert large_cap["MSFT"] == Decimal("3000")
        assert large_cap["NVDA"] == Decimal("4000")

        # Mid cap should have TSLA
        mid_cap = grouped["mid_cap"]
        assert len(mid_cap) == 1
        assert mid_cap["TSLA"] == Decimal("2000")

        # Small cap should have RBLX
        small_cap = grouped["small_cap"]
        assert len(small_cap) == 1
        assert small_cap["RBLX"] == Decimal("1000")

    def test_calculate_strategy_allocations(self):
        """Test calculating strategy allocation percentages."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.side_effect = lambda symbol: {
            "AAPL": "large_cap",
            "MSFT": "large_cap",
            "TSLA": "mid_cap",
        }.get(symbol, "unknown")

        engine = StrategyAttributionEngine(mock_classifier)

        positions = {
            "AAPL": Decimal("6000"),  # 60%
            "MSFT": Decimal("3000"),  # 30%
            "TSLA": Decimal("1000"),  # 10%
        }
        portfolio_value = Decimal("10000")

        allocations = engine.calculate_strategy_allocations(positions, portfolio_value)

        assert len(allocations) == 2
        assert "large_cap" in allocations
        assert "mid_cap" in allocations

        # Large cap: (6000 + 3000) / 10000 = 0.9 = 90%
        assert allocations["large_cap"] == Decimal("0.9")

        # Mid cap: 1000 / 10000 = 0.1 = 10%
        assert allocations["mid_cap"] == Decimal("0.1")

    def test_get_strategy_exposures(self):
        """Test getting detailed strategy exposures."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.side_effect = lambda symbol: {
            "AAPL": "large_cap",
            "MSFT": "large_cap",
            "TSLA": "mid_cap",
        }.get(symbol, "unknown")

        engine = StrategyAttributionEngine(mock_classifier)

        positions = {"AAPL": Decimal("6000"), "MSFT": Decimal("3000"), "TSLA": Decimal("1000")}
        portfolio_value = Decimal("10000")

        exposures = engine.get_strategy_exposures(positions, portfolio_value)

        assert len(exposures) == 2

        # Large cap exposure
        large_cap_exposure = exposures["large_cap"]
        assert "total_value" in large_cap_exposure
        assert "allocation_percentage" in large_cap_exposure
        assert "positions" in large_cap_exposure

        assert large_cap_exposure["total_value"] == Decimal("9000")
        assert large_cap_exposure["allocation_percentage"] == Decimal("0.9")
        assert len(large_cap_exposure["positions"]) == 2
        assert "AAPL" in large_cap_exposure["positions"]
        assert "MSFT" in large_cap_exposure["positions"]

        # Mid cap exposure
        mid_cap_exposure = exposures["mid_cap"]
        assert mid_cap_exposure["total_value"] == Decimal("1000")
        assert mid_cap_exposure["allocation_percentage"] == Decimal("0.1")
        assert len(mid_cap_exposure["positions"]) == 1
        assert "TSLA" in mid_cap_exposure["positions"]

    def test_empty_positions(self):
        """Test handling empty positions."""
        engine = StrategyAttributionEngine()

        grouped = engine.group_positions_by_strategy({})
        assert grouped == {}

        allocations = engine.calculate_strategy_allocations({}, Decimal("0"))
        assert allocations == {}

        exposures = engine.get_strategy_exposures({}, Decimal("0"))
        assert exposures == {}

    def test_zero_portfolio_value(self):
        """Test handling zero portfolio value."""
        mock_classifier = Mock(spec=SymbolClassifier)
        mock_classifier.classify_symbol.return_value = "large_cap"

        engine = StrategyAttributionEngine(mock_classifier)

        positions = {"AAPL": Decimal("1000")}
        portfolio_value = Decimal("0")

        # Should handle division by zero gracefully
        allocations = engine.calculate_strategy_allocations(positions, portfolio_value)
        exposures = engine.get_strategy_exposures(positions, portfolio_value)

        # Should return empty results for zero portfolio value
        assert allocations == {}
        assert exposures == {}
