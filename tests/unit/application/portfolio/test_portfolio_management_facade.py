"""Test the PortfolioManagementFacade."""

from decimal import Decimal
from unittest.mock import Mock

from the_alchemiser.application.portfolio.services.portfolio_management_facade import (
    PortfolioManagementFacade,
)
from the_alchemiser.services.enhanced.trading_service_manager import TradingServiceManager


class TestPortfolioManagementFacade:
    """Test cases for PortfolioManagementFacade."""

    def test_init(self):
        """Test initialization of the facade."""
        mock_trading_manager = Mock(spec=TradingServiceManager)

        facade = PortfolioManagementFacade(mock_trading_manager)

        assert facade.trading_manager is mock_trading_manager
        assert facade.rebalance_calculator is not None
        assert facade.position_analyzer is not None
        assert facade.attribution_engine is not None
        assert facade.rebalancing_service is not None
        assert facade.analysis_service is not None
        assert facade.execution_service is not None

    def test_get_current_portfolio_value(self):
        """Test getting current portfolio value."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        mock_trading_manager.get_portfolio_value.return_value = 100000.0

        facade = PortfolioManagementFacade(mock_trading_manager)

        result = facade.get_current_portfolio_value()

        assert result == Decimal("100000.0")
        mock_trading_manager.get_portfolio_value.assert_called_once()

    def test_get_current_positions(self):
        """Test getting current positions."""
        mock_trading_manager = Mock(spec=TradingServiceManager)

        # Mock position objects
        mock_position1 = Mock()
        mock_position1.symbol = "AAPL"
        mock_position1.market_value = 5000.0

        mock_position2 = Mock()
        mock_position2.symbol = "MSFT"
        mock_position2.market_value = 3000.0

        mock_position3 = Mock()
        mock_position3.symbol = "GOOGL"
        mock_position3.market_value = 0.0  # Should be filtered out

        mock_trading_manager.get_all_positions.return_value = [
            mock_position1,
            mock_position2,
            mock_position3,
        ]

        facade = PortfolioManagementFacade(mock_trading_manager)

        result = facade.get_current_positions()

        expected = {"AAPL": Decimal("5000.0"), "MSFT": Decimal("3000.0")}
        assert result == expected
        mock_trading_manager.get_all_positions.assert_called_once()

    def test_get_current_weights(self):
        """Test getting current portfolio weights."""
        mock_trading_manager = Mock(spec=TradingServiceManager)

        # Mock positions
        mock_position1 = Mock()
        mock_position1.symbol = "AAPL"
        mock_position1.market_value = 6000.0

        mock_position2 = Mock()
        mock_position2.symbol = "MSFT"
        mock_position2.market_value = 4000.0

        mock_trading_manager.get_all_positions.return_value = [mock_position1, mock_position2]
        mock_trading_manager.get_portfolio_value.return_value = 10000.0

        facade = PortfolioManagementFacade(mock_trading_manager)

        result = facade.get_current_weights()

        expected = {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")}
        assert result == expected

    def test_get_current_weights_zero_portfolio_value(self):
        """Test getting weights when portfolio value is zero."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        mock_trading_manager.get_all_positions.return_value = []
        mock_trading_manager.get_portfolio_value.return_value = 0.0

        facade = PortfolioManagementFacade(mock_trading_manager)

        result = facade.get_current_weights()

        assert result == {}

    def test_calculate_rebalancing_plan(self):
        """Test calculating rebalancing plan."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        facade = PortfolioManagementFacade(mock_trading_manager)

        # Mock the rebalancing service
        mock_plan = {"AAPL": Mock(), "MSFT": Mock()}
        facade.rebalancing_service.calculate_rebalancing_plan = Mock(return_value=mock_plan)

        target_weights = {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")}

        result = facade.calculate_rebalancing_plan(target_weights)

        assert result == mock_plan
        facade.rebalancing_service.calculate_rebalancing_plan.assert_called_once_with(
            target_weights, None, None
        )

    def test_execute_rebalancing_with_validation_failure(self):
        """Test rebalancing execution when validation fails."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        facade = PortfolioManagementFacade(mock_trading_manager)

        # Mock services
        mock_plan = {"AAPL": Mock()}
        facade.rebalancing_service.calculate_rebalancing_plan = Mock(return_value=mock_plan)

        validation_result = {"is_valid": False, "issues": ["Insufficient buying power"]}
        facade.execution_service.validate_rebalancing_plan = Mock(return_value=validation_result)

        target_weights = {"AAPL": Decimal("1.0")}

        result = facade.execute_rebalancing(target_weights, dry_run=True)

        assert result["status"] == "validation_failed"
        assert result["validation_results"] == validation_result
        assert result["execution_results"] is None

    def test_execute_rebalancing_with_validation_success(self):
        """Test rebalancing execution when validation succeeds."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        facade = PortfolioManagementFacade(mock_trading_manager)

        # Mock services
        mock_plan = {"AAPL": Mock()}
        facade.rebalancing_service.calculate_rebalancing_plan = Mock(return_value=mock_plan)

        validation_result = {"is_valid": True, "issues": []}
        facade.execution_service.validate_rebalancing_plan = Mock(return_value=validation_result)

        execution_result = {"status": "success", "orders_placed": {}}
        facade.execution_service.execute_rebalancing_plan = Mock(return_value=execution_result)

        target_weights = {"AAPL": Decimal("1.0")}

        result = facade.execute_rebalancing(target_weights, dry_run=True)

        assert result["status"] == "completed"
        assert result["validation_results"] == validation_result
        assert result["execution_results"] == execution_result
        assert result["rebalance_plan"] == mock_plan

    def test_get_complete_portfolio_overview_without_targets(self):
        """Test getting portfolio overview without target weights."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        facade = PortfolioManagementFacade(mock_trading_manager)

        # Mock services
        portfolio_analysis = {"portfolio_value": 100000}
        strategy_performance = {"strategies": 3}

        facade.analysis_service.get_comprehensive_portfolio_analysis = Mock(
            return_value=portfolio_analysis
        )
        facade.analysis_service.get_strategy_performance_analysis = Mock(
            return_value=strategy_performance
        )

        result = facade.get_complete_portfolio_overview()

        assert "portfolio_analysis" in result
        assert "strategy_performance" in result
        assert "drift_analysis" not in result
        assert "rebalancing_summary" not in result

    def test_get_complete_portfolio_overview_with_targets(self):
        """Test getting portfolio overview with target weights."""
        mock_trading_manager = Mock(spec=TradingServiceManager)
        facade = PortfolioManagementFacade(mock_trading_manager)

        # Mock all required methods
        facade.analysis_service.get_comprehensive_portfolio_analysis = Mock(return_value={})
        facade.analysis_service.get_strategy_performance_analysis = Mock(return_value={})
        facade.analysis_service.analyze_portfolio_drift = Mock(return_value={})
        facade.rebalancing_service.get_rebalancing_summary = Mock(return_value={})
        facade.rebalancing_service.estimate_rebalancing_impact = Mock(return_value={})
        facade.analysis_service.compare_target_vs_current_strategy_allocation = Mock(
            return_value={}
        )

        target_weights = {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")}

        result = facade.get_complete_portfolio_overview(target_weights)

        assert "portfolio_analysis" in result
        assert "strategy_performance" in result
        assert "drift_analysis" in result
        assert "rebalancing_summary" in result
        assert "rebalancing_impact" in result
        assert "strategy_comparison" in result
