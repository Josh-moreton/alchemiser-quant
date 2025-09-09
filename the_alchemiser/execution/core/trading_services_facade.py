"""Business Unit: execution | Status: current.

Trading services facade providing broker/account/position operations.

This facade delegates to decomposed services for better separation of concerns.
It handles broker-level operations but NOT multi-strategy execution or orchestration.

For multi-strategy execution, use ExecutionManager instead.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.core.account_management_service import AccountManagementService
from the_alchemiser.execution.core.data_transformation_service import DataTransformationService
from the_alchemiser.execution.core.lifecycle_coordinator import LifecycleCoordinator
from the_alchemiser.execution.core.order_execution_service import OrderExecutionService
from the_alchemiser.execution.execution_protocols import BrokerTradingServices
from the_alchemiser.execution.lifecycle import OrderLifecycleState
from the_alchemiser.execution.orders.consolidated_validation import OrderValidator
from the_alchemiser.execution.orders.order_types import OrderId
from the_alchemiser.execution.orders.schemas import OrderRequestDTO
from the_alchemiser.execution.schemas.smart_trading import (
    SmartOrderExecutionDTO,
    TradingDashboardDTO,
)
from the_alchemiser.portfolio.holdings.position_service import PositionService
from the_alchemiser.portfolio.schemas.positions import (
    ClosePositionResultDTO,
    PortfolioSummaryDTO,
    PortfolioValueDTO,
    PositionAnalyticsDTO,
    PositionMetricsDTO,
    PositionSummaryDTO,
)
from the_alchemiser.shared.brokers import AlpacaManager
from the_alchemiser.shared.schemas.accounts import (
    AccountMetricsDTO,
    AccountSummaryDTO,
    BuyingPowerDTO,
    EnrichedAccountSummaryDTO,
    PortfolioAllocationDTO,
    RiskMetricsDTO,
    TradeEligibilityDTO,
)
from the_alchemiser.shared.schemas.enriched_data import (
    EnrichedPositionsDTO,
    OpenOrdersDTO,
)
from the_alchemiser.shared.schemas.market_data import (
    MarketStatusDTO,
    MultiSymbolQuotesDTO,
    PriceDTO,
    PriceHistoryDTO,
    SpreadAnalysisDTO,
)
from the_alchemiser.shared.schemas.operations import (
    OrderCancellationDTO,
    OrderStatusDTO,
)
from the_alchemiser.shared.utils.decorators import translate_trading_errors


def _create_error_dashboard(error_message: str = "Failed to generate dashboard") -> TradingDashboardDTO:
    """Create a standardized error dashboard DTO."""
    return TradingDashboardDTO(
        success=False,
        account=AccountSummaryDTO(
            account_id="error",
            equity=Decimal("0"),
            cash=Decimal("0"),
            market_value=Decimal("0"),
            buying_power=Decimal("0"),
            last_equity=Decimal("0"),
            day_trade_count=0,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=AccountMetricsDTO(
                cash_ratio=Decimal("0"),
                market_exposure=Decimal("0"),
                leverage_ratio=None,
                available_buying_power_ratio=Decimal("0"),
            ),
        ),
        risk_metrics={},
        portfolio_allocation={},
        position_summary={},
        open_orders=[],
        market_status={},
        timestamp=datetime.now(UTC),
        error=error_message,
    )


def _create_order_execution_error(reason: str, error: str) -> SmartOrderExecutionDTO:
    """Create a standardized order execution error DTO."""
    return SmartOrderExecutionDTO(
        success=False,
        reason=reason,
        error=error,
    )


class TradingServicesFacade(BrokerTradingServices):
    """Facade for broker/account/position operations using decomposed services.

    This facade coordinates broker-level operations while maintaining clean separation 
    of concerns. It handles account management, order execution, and position tracking
    but does NOT handle multi-strategy orchestration - use ExecutionManager for that.
    
    Responsibilities:
    - Order placement and management
    - Account information and risk metrics
    - Position tracking and analytics
    - Trading dashboard data
    
    Does NOT handle:
    - Multi-strategy execution (use ExecutionManager)
    - Strategy coordination (use ExecutionManager)
    - Portfolio rebalancing orchestration (use ExecutionManager)
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize the refactored trading service manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading environment

        """
        self.logger = logging.getLogger(__name__)

        # Initialize the core repository implementation
        self.alpaca_manager = AlpacaManager(api_key, secret_key, paper)

        # Initialize decomposed services
        self.order_execution = OrderExecutionService(self.alpaca_manager)
        self.account_management = AccountManagementService(self.alpaca_manager)
        self.lifecycle_coordinator = LifecycleCoordinator()
        self.data_transformation = DataTransformationService(self.alpaca_manager)

        # Initialize remaining services
        self.positions = PositionService(self.alpaca_manager)
        self.order_validator = OrderValidator()

        self.logger.info(f"TradingServicesFacade initialized with paper={paper}")

    # Order Execution Operations (delegated to OrderExecutionService)
    def place_stop_loss_order(
        self, symbol: str, quantity: float, stop_price: float, validate: bool = True
    ) -> OrderRequestDTO:
        """Place a stop-loss order using liquidation (not directly supported)."""
        return self.order_execution.place_stop_loss_order(symbol, quantity, stop_price, validate)

    def cancel_order(self, order_id: str) -> OrderCancellationDTO:
        """Cancel an order with enhanced feedback."""
        return self.order_execution.cancel_order(order_id)

    def get_order_status(self, order_id: str) -> OrderStatusDTO:
        """Get order status (not directly available - use AlpacaManager directly)."""
        return self.order_execution.get_order_status(order_id)

    def get_open_orders(self, symbol: str | None = None) -> OpenOrdersDTO:
        """Get open orders."""
        return self.order_execution.get_open_orders(symbol)

    # Account Management Operations (delegated to AccountManagementService)
    def get_account_summary(self) -> AccountSummaryDTO:
        """Get comprehensive account summary with metrics."""
        return self.account_management.get_account_summary()

    def check_buying_power(self, required_amount: float) -> BuyingPowerDTO:
        """Check available buying power."""
        return self.account_management.check_buying_power(required_amount)

    def get_risk_metrics(self) -> RiskMetricsDTO:
        """Calculate comprehensive risk metrics."""
        return self.account_management.get_risk_metrics()

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> TradeEligibilityDTO:
        """Validate if a trade can be executed."""
        return self.account_management.validate_trade_eligibility(
            symbol, quantity, side, estimated_cost
        )

    def get_portfolio_allocation(self) -> PortfolioAllocationDTO:
        """Get portfolio allocation and diversification metrics."""
        return self.account_management.get_portfolio_allocation()

    def get_account_summary_enriched(self) -> EnrichedAccountSummaryDTO:
        """Enriched account summary with typed domain objects."""
        return self.account_management.get_account_summary_enriched()

    # Lifecycle Management Operations (delegated to LifecycleCoordinator)
    def get_order_lifecycle_state(self, order_id: OrderId) -> OrderLifecycleState | None:
        """Get the current lifecycle state of an order."""
        return self.lifecycle_coordinator.get_order_lifecycle_state(order_id)

    def get_all_tracked_orders(self) -> dict[OrderId, OrderLifecycleState]:
        """Get all tracked orders and their current lifecycle states."""
        return self.lifecycle_coordinator.get_all_tracked_orders()

    def get_lifecycle_metrics(self) -> dict[str, Any]:
        """Get lifecycle metrics from the metrics observer."""
        return self.lifecycle_coordinator.get_lifecycle_metrics()

    # Data Transformation Operations (delegated to DataTransformationService)
    def get_latest_price(self, symbol: str, validate: bool = True) -> PriceDTO:
        """Get latest price with validation and caching."""
        return self.data_transformation.get_latest_price(symbol, validate)

    def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 100,
        validate: bool = True,
    ) -> PriceHistoryDTO:
        """Get price history (not directly available - use AlpacaManager directly)."""
        return self.data_transformation.get_price_history(symbol, timeframe, limit, validate)

    def analyze_spread(self, symbol: str) -> SpreadAnalysisDTO:
        """Analyze bid-ask spread for a symbol."""
        return self.data_transformation.analyze_spread(symbol)

    def get_market_status(self) -> MarketStatusDTO:
        """Get current market status."""
        return self.data_transformation.get_market_status()

    def get_multi_symbol_quotes(self, symbols: list[str]) -> MultiSymbolQuotesDTO:
        """Get quotes for multiple symbols."""
        return self.data_transformation.get_multi_symbol_quotes(symbols)

    def get_all_positions(self) -> EnrichedPositionsDTO:
        """Get all positions from the underlying repository."""
        return self.data_transformation.get_all_positions()

    def get_positions_enriched(self) -> EnrichedPositionsDTO:
        """Enriched positions list with typed domain objects."""
        return self.data_transformation.get_positions_enriched()

    def get_portfolio_value(self) -> PortfolioValueDTO:
        """Get total portfolio value with typed domain objects."""
        return self.data_transformation.get_portfolio_value()

    def calculate_position_metrics(self) -> PositionMetricsDTO:
        """Calculate comprehensive position metrics and analytics."""
        return self.data_transformation.calculate_position_metrics()

    # Position Management Operations (using existing PositionService)
    def get_position_summary(
        self, symbol: str | None = None
    ) -> PositionSummaryDTO | PortfolioSummaryDTO:
        """Get comprehensive position summary."""
        try:
            if symbol:
                # Get specific position info
                positions = self.positions.get_positions_with_analysis()
                position = positions.get(symbol)
                if position:
                    # Return PositionSummaryDTO
                    return PositionSummaryDTO(
                        success=True,
                        symbol=symbol,
                        position=position,
                    )
                return PositionSummaryDTO(
                    success=False,
                    symbol=symbol,
                    error=f"Position not found for {symbol}",
                )
            # Get portfolio summary
            positions_dict = self.positions.get_positions_with_analysis()
            return PortfolioSummaryDTO(
                success=True,
                total_positions=len(positions_dict),
                positions=positions_dict,
            )
        except Exception as e:
            if symbol:
                return PositionSummaryDTO(success=False, symbol=symbol, error=str(e))
            return PortfolioSummaryDTO(success=False, error=str(e))

    def close_position(self, symbol: str, percentage: float = 100.0) -> ClosePositionResultDTO:
        """Close position using enhanced position service."""
        try:
            result = self.positions.close_position(symbol, percentage)
            return ClosePositionResultDTO(
                success=result.get("success", False),
                symbol=symbol,
                quantity_closed=result.get("quantity", 0),
                fill_price=result.get("price"),
                proceeds=result.get("proceeds"),
                error=result.get("error"),
            )
        except Exception as e:
            return ClosePositionResultDTO(success=False, symbol=symbol, error=str(e))

    def get_position_analytics(self, symbol: str) -> PositionAnalyticsDTO:
        """Get position analytics using enhanced position service."""
        try:
            analytics = self.positions.get_position_analytics(symbol)
            return PositionAnalyticsDTO(
                success=analytics.get("success", False),
                symbol=symbol,
                analytics=analytics.get("analytics", {}),
                error=analytics.get("error"),
            )
        except Exception as e:
            return PositionAnalyticsDTO(success=False, symbol=symbol, error=str(e))

    # High-Level Trading Operations
    @translate_trading_errors(default_return=_create_order_execution_error("Order execution failed", "Service error"))
    def execute_smart_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        order_type: str = "market",
        **kwargs: Any,  # noqa: ANN401  # Order parameters are dynamic
    ) -> SmartOrderExecutionDTO:
        """Execute a smart order with comprehensive validation and risk management."""
        try:
            # Create order ID for lifecycle tracking
            client_order_id = kwargs.get("client_order_id")
            order_id = self.lifecycle_coordinator.create_order_id(
                client_order_id if isinstance(client_order_id, str) else None
            )

            # Emit initial lifecycle event
            self.lifecycle_coordinator.emit_lifecycle_event(
                order_id=order_id,
                target_state=OrderLifecycleState.NEW,
                metadata={"symbol": symbol, "quantity": quantity, "side": side},
            )

            # Implementation would continue with actual order execution logic
            # For now, return a placeholder response
            return _create_order_execution_error(
                "Smart order execution not yet implemented in refactored manager",
                "Implementation needed"
            )

        except Exception as e:
            return _create_order_execution_error("Smart order execution failed", str(e))

    def execute_order_dto(self, order_request: OrderRequestDTO) -> SmartOrderExecutionDTO:
        """Execute an order using OrderRequestDTO directly."""
        try:
            # Validate the order using the DTO validator
            validated_order = self.order_validator.validate_order_request(order_request)

            # Convert to parameters for execution
            return self.execute_smart_order(
                symbol=validated_order.symbol,
                quantity=int(validated_order.quantity),
                side=validated_order.side,
                order_type=validated_order.order_type,
                limit_price=(
                    float(validated_order.limit_price) if validated_order.limit_price else None
                ),
                time_in_force=validated_order.time_in_force,
                client_order_id=validated_order.client_order_id,
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in execute_order_dto: {e}")
            return _create_order_execution_error("DTO order execution failed", str(e))

    @translate_trading_errors(default_return=_create_error_dashboard())
    def get_trading_dashboard(self) -> TradingDashboardDTO:
        """Get a comprehensive trading dashboard with all key metrics."""
        try:
            # Get all required data using decomposed services
            account_summary = self.get_account_summary_enriched()
            risk_metrics = self.get_risk_metrics()
            portfolio_allocation = self.get_portfolio_allocation()
            pos_summary = self.get_position_summary()
            open_orders = self.get_open_orders()
            market_status = self.get_market_status()

            # Create dashboard response
            return TradingDashboardDTO(
                success=True,
                account=account_summary.summary,
                risk_metrics=risk_metrics.model_dump()
                if hasattr(risk_metrics, "model_dump")
                else {},
                portfolio_allocation=portfolio_allocation.model_dump()
                if hasattr(portfolio_allocation, "model_dump")
                else {},
                position_summary=pos_summary.model_dump()
                if hasattr(pos_summary, "model_dump")
                else {},
                open_orders=open_orders.orders,
                market_status=market_status.model_dump()
                if hasattr(market_status, "model_dump")
                else {},
                timestamp=datetime.now(UTC),
            )

        except Exception as e:
            self.logger.error(f"Failed to generate trading dashboard: {e}")
            return _create_error_dashboard(str(e))

    def close(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self.alpaca_manager, "close"):
                self.alpaca_manager.close()
            self.logger.info("TradingServicesFacade closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing TradingServicesFacade: {e}")
