"""Test the PositionAnalyzer."""

from decimal import Decimal

from the_alchemiser.domain.portfolio.position.position_analyzer import PositionAnalyzer
from the_alchemiser.domain.portfolio.position.position_delta import PositionDelta


class TestPositionAnalyzer:
    """Test cases for PositionAnalyzer."""

    def test_create_position_delta(self):
        """Test creating a position delta."""
        analyzer = PositionAnalyzer()
        current_value = Decimal("5000")
        target_value = Decimal("3000")

        delta = analyzer.create_position_delta("AAPL", current_value, target_value)

        assert isinstance(delta, PositionDelta)
        assert delta.symbol == "AAPL"
        assert delta.current_value == current_value
        assert delta.target_value == target_value
        assert delta.value_difference == Decimal("-2000")
        assert delta.requires_sell is True
        assert delta.requires_buy is False

    def test_analyze_all_positions(self):
        """Test analyzing all positions."""
        analyzer = PositionAnalyzer()
        current_positions = {
            "AAPL": Decimal("5000"),
            "MSFT": Decimal("2000"),
            "GOOGL": Decimal("1000"),
        }
        target_positions = {
            "AAPL": Decimal("3000"),
            "MSFT": Decimal("3000"),
            "GOOGL": Decimal("2000"),
            "AMZN": Decimal("1000"),  # New position
        }

        deltas = analyzer.analyze_all_positions(current_positions, target_positions)

        assert len(deltas) == 4

        # AAPL - should sell
        aapl_delta = deltas["AAPL"]
        assert aapl_delta.symbol == "AAPL"
        assert aapl_delta.value_difference == Decimal("-2000")
        assert aapl_delta.requires_sell is True

        # MSFT - should buy
        msft_delta = deltas["MSFT"]
        assert msft_delta.symbol == "MSFT"
        assert msft_delta.value_difference == Decimal("1000")
        assert msft_delta.requires_buy is True

        # GOOGL - should buy
        googl_delta = deltas["GOOGL"]
        assert googl_delta.symbol == "GOOGL"
        assert googl_delta.value_difference == Decimal("1000")
        assert googl_delta.requires_buy is True

        # AMZN - new position, should buy
        amzn_delta = deltas["AMZN"]
        assert amzn_delta.symbol == "AMZN"
        assert amzn_delta.current_value == Decimal("0")
        assert amzn_delta.value_difference == Decimal("1000")
        assert amzn_delta.requires_buy is True

    def test_get_positions_to_sell(self):
        """Test filtering positions that need selling."""
        analyzer = PositionAnalyzer()
        deltas = {
            "AAPL": PositionDelta(
                symbol="AAPL", current_value=Decimal("5000"), target_value=Decimal("3000")
            ),
            "MSFT": PositionDelta(
                symbol="MSFT", current_value=Decimal("2000"), target_value=Decimal("3000")
            ),
            "GOOGL": PositionDelta(
                symbol="GOOGL", current_value=Decimal("3000"), target_value=Decimal("3000")
            ),
        }

        sell_positions = analyzer.get_positions_to_sell(deltas)

        assert len(sell_positions) == 1
        assert "AAPL" in sell_positions
        assert sell_positions["AAPL"].requires_sell is True

    def test_get_positions_to_buy(self):
        """Test filtering positions that need buying."""
        analyzer = PositionAnalyzer()
        deltas = {
            "AAPL": PositionDelta(
                symbol="AAPL", current_value=Decimal("5000"), target_value=Decimal("3000")
            ),
            "MSFT": PositionDelta(
                symbol="MSFT", current_value=Decimal("2000"), target_value=Decimal("3000")
            ),
            "GOOGL": PositionDelta(
                symbol="GOOGL", current_value=Decimal("3000"), target_value=Decimal("3000")
            ),
        }

        buy_positions = analyzer.get_positions_to_buy(deltas)

        assert len(buy_positions) == 1
        assert "MSFT" in buy_positions
        assert buy_positions["MSFT"].requires_buy is True

    def test_calculate_total_adjustments_needed(self):
        """Test calculating total adjustment values."""
        analyzer = PositionAnalyzer()
        deltas = {
            "AAPL": PositionDelta(
                symbol="AAPL", current_value=Decimal("5000"), target_value=Decimal("3000")
            ),
            "MSFT": PositionDelta(
                symbol="MSFT", current_value=Decimal("2000"), target_value=Decimal("3000")
            ),
            "GOOGL": PositionDelta(
                symbol="GOOGL", current_value=Decimal("1000"), target_value=Decimal("2000")
            ),
        }

        total_sells, total_buys = analyzer.calculate_total_adjustments_needed(deltas)

        # AAPL needs to sell 2000
        assert total_sells == Decimal("2000")

        # MSFT needs to buy 1000, GOOGL needs to buy 1000
        assert total_buys == Decimal("2000")

    def test_calculate_portfolio_turnover(self):
        """Test calculating portfolio turnover."""
        analyzer = PositionAnalyzer()
        deltas = {
            "AAPL": PositionDelta(
                symbol="AAPL", current_value=Decimal("5000"), target_value=Decimal("3000")
            ),
            "MSFT": PositionDelta(
                symbol="MSFT", current_value=Decimal("2000"), target_value=Decimal("3000")
            ),
        }
        portfolio_value = Decimal("10000")

        turnover = analyzer.calculate_portfolio_turnover(deltas, portfolio_value)

        # Total adjustments: 2000 (sell) + 1000 (buy) = 3000
        # Turnover: 3000 / 10000 = 0.3
        assert turnover == Decimal("0.3")
