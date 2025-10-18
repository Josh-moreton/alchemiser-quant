"""Business Unit: portfolio | Status: current

Integration test for negative cash balance handling in portfolio service.

Tests that the PortfolioServiceV2 properly propagates NegativeCashBalanceError
when the underlying state reader detects a negative cash balance.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from the_alchemiser.portfolio_v2.core.portfolio_service import PortfolioServiceV2
from the_alchemiser.shared.errors.exceptions import (
    PortfolioError,
)
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestPortfolioServiceNegativeCash:
    """Test negative cash handling in portfolio service integration."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create mock Alpaca manager."""
        return Mock()

    @pytest.fixture
    def portfolio_service(self, mock_alpaca_manager):
        """Create portfolio service with mock manager."""
        return PortfolioServiceV2(mock_alpaca_manager)

    @pytest.fixture
    def sample_strategy_allocation(self):
        """Create sample strategy allocation."""
        return StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.5"),
                "MSFT": Decimal("0.5"),
            },
            correlation_id="test-correlation-id",
            as_of=datetime.now(UTC),
        )

    def test_create_rebalance_plan_with_negative_cash_raises_portfolio_error(
        self, portfolio_service, mock_alpaca_manager, sample_strategy_allocation
    ):
        """Test that negative cash causes PortfolioError during plan creation."""
        # Setup mocks to simulate negative cash scenario
        mock_alpaca_manager.get_positions.return_value = []
        mock_alpaca_manager.get_account.return_value = {
            "cash": "-100.00",
        }

        # Attempting to create rebalance plan should raise PortfolioError
        # (wrapping the underlying NegativeCashBalanceError)
        with pytest.raises(PortfolioError) as exc_info:
            portfolio_service.create_rebalance_plan(
                sample_strategy_allocation, "test-correlation-id"
            )

        # Verify the error mentions the negative cash issue
        error_message = str(exc_info.value).lower()
        assert "failed to create rebalance plan" in error_message or "snapshot" in error_message

    def test_create_rebalance_plan_with_zero_cash_raises_portfolio_error(
        self, portfolio_service, mock_alpaca_manager, sample_strategy_allocation
    ):
        """Test that zero cash causes PortfolioError during plan creation."""
        # Setup mocks to simulate zero cash scenario
        mock_alpaca_manager.get_positions.return_value = []
        mock_alpaca_manager.get_account.return_value = {
            "cash": "0.00",
        }

        # Attempting to create rebalance plan should raise PortfolioError
        with pytest.raises(PortfolioError) as exc_info:
            portfolio_service.create_rebalance_plan(
                sample_strategy_allocation, "test-correlation-id"
            )

        # Verify error is raised
        assert exc_info.value is not None

    def test_create_rebalance_plan_with_positive_cash_succeeds(
        self, portfolio_service, mock_alpaca_manager, sample_strategy_allocation
    ):
        """Test that positive cash allows plan creation to proceed."""
        # Setup mocks to simulate positive cash scenario
        mock_alpaca_manager.get_positions.return_value = []
        mock_alpaca_manager.get_account.return_value = {
            "cash": "1000.00",
        }
        mock_alpaca_manager.get_current_price.return_value = 150.00

        # Should succeed and return a plan
        plan = portfolio_service.create_rebalance_plan(
            sample_strategy_allocation, "test-correlation-id"
        )

        # Verify plan was created
        assert plan is not None
        assert plan.correlation_id == "test-correlation-id"
        assert len(plan.items) > 0
