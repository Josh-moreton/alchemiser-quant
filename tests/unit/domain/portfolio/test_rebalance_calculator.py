"""Test the RebalanceCalculator."""

from decimal import Decimal
from unittest.mock import patch

from the_alchemiser.domain.portfolio.rebalancing.rebalance_calculator import RebalanceCalculator
from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan


class TestRebalanceCalculator:
    """Test cases for RebalanceCalculator."""

    def test_init_default_threshold(self):
        """Test initialization with default threshold."""
        calculator = RebalanceCalculator()
        assert calculator.min_trade_threshold == Decimal("0.01")

    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        calculator = RebalanceCalculator(min_trade_threshold=Decimal("0.05"))
        assert calculator.min_trade_threshold == Decimal("0.05")

    @patch('the_alchemiser.domain.portfolio.rebalancing.rebalance_calculator.calculate_rebalance_amounts')
    def test_calculate_rebalance_plan(self, mock_calculate):
        """Test calculate_rebalance_plan method."""
        # Mock the response from calculate_rebalance_amounts
        mock_calculate.return_value = {
            "AAPL": {
                "current_weight": 0.4,
                "target_weight": 0.3,
                "weight_diff": -0.1,
                "target_value": 3000.0,
                "current_value": 4000.0,
                "trade_amount": -1000.0,
                "needs_rebalance": True
            },
            "MSFT": {
                "current_weight": 0.2,
                "target_weight": 0.3,
                "weight_diff": 0.1,
                "target_value": 3000.0,
                "current_value": 2000.0,
                "trade_amount": 1000.0,
                "needs_rebalance": True
            }
        }

        calculator = RebalanceCalculator()
        target_weights = {"AAPL": Decimal("0.3"), "MSFT": Decimal("0.3")}
        current_values = {"AAPL": Decimal("4000"), "MSFT": Decimal("2000")}
        portfolio_value = Decimal("10000")

        result = calculator.calculate_rebalance_plan(target_weights, current_values, portfolio_value)

        # Verify the mock was called correctly
        mock_calculate.assert_called_once_with(
            {"AAPL": 0.3, "MSFT": 0.3},
            {"AAPL": 4000.0, "MSFT": 2000.0},
            10000.0,
            0.01
        )

        # Verify the result is properly converted to domain objects
        assert len(result) == 2
        assert "AAPL" in result
        assert "MSFT" in result

        aapl_plan = result["AAPL"]
        assert isinstance(aapl_plan, RebalancePlan)
        assert aapl_plan.symbol == "AAPL"
        assert aapl_plan.current_weight == Decimal("0.4")
        assert aapl_plan.target_weight == Decimal("0.3")
        assert aapl_plan.trade_amount == Decimal("-1000.0")
        assert aapl_plan.needs_rebalance is True

    def test_get_symbols_needing_rebalance(self):
        """Test filtering symbols that need rebalancing."""
        calculator = RebalanceCalculator()

        rebalance_plan = {
            "AAPL": RebalancePlan(
                symbol="AAPL", current_weight=Decimal("0.4"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("-0.1"), target_value=Decimal("3000"), current_value=Decimal("4000"),
                trade_amount=Decimal("-1000"), needs_rebalance=True
            ),
            "MSFT": RebalancePlan(
                symbol="MSFT", current_weight=Decimal("0.3"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.0"), target_value=Decimal("3000"), current_value=Decimal("3000"),
                trade_amount=Decimal("0"), needs_rebalance=False
            ),
            "GOOGL": RebalancePlan(
                symbol="GOOGL", current_weight=Decimal("0.2"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.1"), target_value=Decimal("3000"), current_value=Decimal("2000"),
                trade_amount=Decimal("1000"), needs_rebalance=True
            )
        }

        result = calculator.get_symbols_needing_rebalance(rebalance_plan)

        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result
        assert "MSFT" not in result

    def test_get_sell_plans(self):
        """Test filtering sell plans."""
        calculator = RebalanceCalculator()

        rebalance_plan = {
            "AAPL": RebalancePlan(
                symbol="AAPL", current_weight=Decimal("0.4"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("-0.1"), target_value=Decimal("3000"), current_value=Decimal("4000"),
                trade_amount=Decimal("-1000"), needs_rebalance=True
            ),
            "MSFT": RebalancePlan(
                symbol="MSFT", current_weight=Decimal("0.3"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.0"), target_value=Decimal("3000"), current_value=Decimal("3000"),
                trade_amount=Decimal("0"), needs_rebalance=False
            ),
            "GOOGL": RebalancePlan(
                symbol="GOOGL", current_weight=Decimal("0.2"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.1"), target_value=Decimal("3000"), current_value=Decimal("2000"),
                trade_amount=Decimal("1000"), needs_rebalance=True
            )
        }

        result = calculator.get_sell_plans(rebalance_plan)

        assert len(result) == 1
        assert "AAPL" in result
        assert result["AAPL"].trade_amount < 0

    def test_get_buy_plans(self):
        """Test filtering buy plans."""
        calculator = RebalanceCalculator()

        rebalance_plan = {
            "AAPL": RebalancePlan(
                symbol="AAPL", current_weight=Decimal("0.4"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("-0.1"), target_value=Decimal("3000"), current_value=Decimal("4000"),
                trade_amount=Decimal("-1000"), needs_rebalance=True
            ),
            "GOOGL": RebalancePlan(
                symbol="GOOGL", current_weight=Decimal("0.2"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.1"), target_value=Decimal("3000"), current_value=Decimal("2000"),
                trade_amount=Decimal("1000"), needs_rebalance=True
            )
        }

        result = calculator.get_buy_plans(rebalance_plan)

        assert len(result) == 1
        assert "GOOGL" in result
        assert result["GOOGL"].trade_amount > 0

    def test_calculate_total_trade_value(self):
        """Test calculating total trade value."""
        calculator = RebalanceCalculator()

        rebalance_plan = {
            "AAPL": RebalancePlan(
                symbol="AAPL", current_weight=Decimal("0.4"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("-0.1"), target_value=Decimal("3000"), current_value=Decimal("4000"),
                trade_amount=Decimal("-1000"), needs_rebalance=True
            ),
            "GOOGL": RebalancePlan(
                symbol="GOOGL", current_weight=Decimal("0.2"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.1"), target_value=Decimal("3000"), current_value=Decimal("2000"),
                trade_amount=Decimal("1000"), needs_rebalance=True
            ),
            "MSFT": RebalancePlan(
                symbol="MSFT", current_weight=Decimal("0.3"), target_weight=Decimal("0.3"),
                weight_diff=Decimal("0.0"), target_value=Decimal("3000"), current_value=Decimal("3000"),
                trade_amount=Decimal("0"), needs_rebalance=False
            )
        }

        result = calculator.calculate_total_trade_value(rebalance_plan)

        # Should be 1000 + 1000 = 2000 (absolute values)
        assert result == Decimal("2000")
