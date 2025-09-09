"""Business Unit: execution | Status: current

Protocol definitions for execution layer interfaces to clarify boundaries and prevent miswiring.
"""

from __future__ import annotations

from typing import Protocol

from the_alchemiser.execution.orders.order_types import OrderId
from the_alchemiser.execution.orders.schemas import OrderRequestDTO
from the_alchemiser.execution.schemas.smart_trading import TradingDashboardDTO
from the_alchemiser.portfolio.schemas.positions import (
    ClosePositionResultDTO,
    PortfolioSummaryDTO,
    PortfolioValueDTO,
    PositionAnalyticsDTO,
    PositionSummaryDTO,
)
from the_alchemiser.shared.schemas.accounts import (
    AccountSummaryDTO,
    BuyingPowerDTO,
    EnrichedAccountSummaryDTO,
    PortfolioAllocationDTO,
    RiskMetricsDTO,
)
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.shared.schemas.enriched_data import (
    EnrichedPositionsDTO,
    OpenOrdersDTO,
)


class MultiStrategyExecutor(Protocol):
    """Protocol for multi-strategy execution orchestration.

    Implemented by ExecutionManager for strategy coordination and portfolio rebalancing.
    This is the proper interface for running multiple strategies and rebalancing.
    """

    def execute_multi_strategy(self) -> MultiStrategyExecutionResultDTO:
        """Execute all strategies and rebalance portfolio.

        Returns:
            Complete multi-strategy execution results including signals, orders, and portfolio state

        """
        ...


class BrokerTradingServices(Protocol):
    """Protocol for broker and account operations facade.

    Implemented by TradingServicesFacade for broker/account/position operations.
    This interface handles broker-level operations, not strategy orchestration.
    """

    # Order Management
    def place_order(self, order_request: OrderRequestDTO) -> OrderId:
        """Place a single order with the broker."""
        ...

    def cancel_order(self, order_id: OrderId) -> bool:
        """Cancel an existing order."""
        ...

    def get_open_orders(self) -> OpenOrdersDTO:
        """Get all open orders."""
        ...

    # Account Operations
    def get_account_summary(self) -> AccountSummaryDTO:
        """Get basic account information."""
        ...

    def get_enriched_account_summary(self) -> EnrichedAccountSummaryDTO:
        """Get detailed account information with calculated metrics."""
        ...

    def get_risk_metrics(self) -> RiskMetricsDTO:
        """Get account risk metrics."""
        ...

    def get_buying_power(self) -> BuyingPowerDTO:
        """Get available buying power information."""
        ...

    def get_portfolio_allocation(self) -> PortfolioAllocationDTO:
        """Get current portfolio allocation breakdown."""
        ...

    # Position Operations
    def get_position_summary(self) -> PositionSummaryDTO:
        """Get summary of all positions."""
        ...

    def get_position_analytics(self) -> PositionAnalyticsDTO:
        """Get detailed position analytics."""
        ...

    def close_position(self, symbol: str) -> ClosePositionResultDTO:
        """Close a specific position."""
        ...

    def get_portfolio_summary(self) -> PortfolioSummaryDTO:
        """Get overall portfolio summary."""
        ...

    def get_portfolio_value(self) -> PortfolioValueDTO:
        """Get current portfolio valuation."""
        ...

    def get_enriched_positions(self) -> EnrichedPositionsDTO:
        """Get detailed position information."""
        ...

    # Dashboard and Reporting
    def get_trading_dashboard(self) -> TradingDashboardDTO:
        """Get comprehensive trading dashboard data."""
        ...
