"""Business Unit: execution | Status: current

Trading service facade aggregating order, position, market data, and account operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.execution.brokers.account_service import AccountService
from the_alchemiser.execution.brokers.alpaca import AlpacaManager
from the_alchemiser.execution.lifecycle import (
    LifecycleEventDispatcher,
    LifecycleEventType,
    LoggingObserver,
    MetricsObserver,
    OrderLifecycleManager,
    OrderLifecycleState,
)
from the_alchemiser.execution.mappers.account_mapping import (
    account_summary_to_typed,
    account_typed_to_serializable,
    to_money_usd,
)
from the_alchemiser.execution.mappers.order_mapping import (
    alpaca_order_to_domain,
    summarize_order,
)
from the_alchemiser.execution.mappers.orders import (
    dict_to_order_request_dto,
)
from the_alchemiser.execution.mappers.trading_service_dto_mapping import (
    account_summary_typed_to_dto,
    dict_to_buying_power_dto,
    dict_to_enriched_account_summary_dto,
    dict_to_market_status_dto,
    dict_to_multi_symbol_quotes_dto,
    dict_to_portfolio_allocation_dto,
    dict_to_portfolio_summary_dto,
    dict_to_position_analytics_dto,
    dict_to_position_metrics_dto,
    dict_to_position_summary_dto,
    dict_to_price_dto,
    dict_to_risk_metrics_dto,
    dict_to_spread_analysis_dto,
    dict_to_trade_eligibility_dto,
    list_to_enriched_positions_dto,
    list_to_open_orders_dto,
)
from the_alchemiser.execution.orders.order_id import OrderId
from the_alchemiser.execution.orders.order_schemas import (
    OrderExecutionResultDTO,
    OrderRequestDTO,
)
from the_alchemiser.execution.orders.service import OrderService
from the_alchemiser.execution.orders.validation import OrderValidator
from the_alchemiser.execution.schemas.smart_trading import (
    OrderValidationMetadataDTO,
    SmartOrderExecutionDTO,
    TradingDashboardDTO,
)
from the_alchemiser.portfolio.holdings.position_service import PositionService
from the_alchemiser.portfolio.mappers.position_mapping import (
    alpaca_position_to_summary,
)
from the_alchemiser.portfolio.schemas.positions import (
    ClosePositionResultDTO,
    PortfolioSummaryDTO,
    PortfolioValueDTO,
    PositionAnalyticsDTO,
    PositionMetricsDTO,
    PositionSummaryDTO,
)
from the_alchemiser.shared.math.num import floats_equal
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
from the_alchemiser.strategy.data.market_data_service import MarketDataService


class TradingServiceManager:
    """Centralized service manager providing high-level access to all trading services.

    This class acts as a facade, providing a single entry point for all trading operations
    while maintaining clean separation of concerns through the service layer architecture.
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize the trading service manager.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading environment

        """
        self.logger = logging.getLogger(__name__)

        # Initialize the core repository implementation
        self.alpaca_manager = AlpacaManager(api_key, secret_key, paper)

        # Initialize enhanced services
        self.orders = OrderService(self.alpaca_manager)
        self.positions = PositionService(self.alpaca_manager)
        self.market_data = MarketDataService(self.alpaca_manager)
        self.account = AccountService(self.alpaca_manager)

        # Initialize DTO-based order validator
        self.order_validator = OrderValidator()

        # Initialize order lifecycle management
        self.lifecycle_manager = OrderLifecycleManager()
        self.lifecycle_dispatcher = LifecycleEventDispatcher()
        # Register default observers
        self.lifecycle_dispatcher.register(LoggingObserver(use_rich_logging=True))
        self.lifecycle_dispatcher.register(MetricsObserver())

        self.logger.info(f"TradingServiceManager initialized with paper={paper}")

    def _create_order_id(self, client_order_id: str | None = None) -> OrderId:
        """Create an OrderId for lifecycle tracking.

        Args:
            client_order_id: Optional client-specified order ID

        Returns:
            OrderId for lifecycle tracking

        """
        if client_order_id:
            try:
                return OrderId.from_string(client_order_id)
            except ValueError:
                # If client_order_id is not a valid UUID, generate a new one
                pass
        return OrderId.generate()

    def _emit_lifecycle_event(
        self,
        order_id: OrderId,
        target_state: OrderLifecycleState,
        event_type: LifecycleEventType = LifecycleEventType.STATE_CHANGED,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a lifecycle event for an order.

        Args:
            order_id: Order identifier
            target_state: Target lifecycle state
            event_type: Type of lifecycle event
            metadata: Additional event metadata

        """
        try:
            self.lifecycle_manager.advance(
                order_id=order_id,
                target_state=target_state,
                event_type=event_type,
                metadata=metadata or {},
                dispatcher=self.lifecycle_dispatcher,
            )
        except Exception as e:
            self.logger.warning(
                "Failed to emit lifecycle event for order %s: %s",
                order_id,
                e,
                exc_info=True,
            )

    # place_market_order / place_limit_order removed. Use CanonicalOrderExecutor directly.

    def place_stop_loss_order(
        self, symbol: str, quantity: float, stop_price: float, validate: bool = True
    ) -> OrderExecutionResultDTO:
        """Place a stop-loss order using liquidation (not directly supported)."""
        return OrderExecutionResultDTO(
            success=False,
            error="Stop-loss orders not directly supported. Use liquidate_position for position closure.",
            order_id="",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=None,
        )

    def cancel_order(self, order_id: str) -> OrderCancellationDTO:
        """Cancel an order with enhanced feedback."""
        try:
            success = self.orders.cancel_order(order_id)
            return OrderCancellationDTO(success=success, order_id=order_id)
        except Exception as e:
            return OrderCancellationDTO(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> OrderStatusDTO:
        """Get order status (not directly available - use AlpacaManager directly)."""
        return OrderStatusDTO(
            success=False,
            error="Order status queries not available in enhanced services. Use AlpacaManager directly.",
        )

    @translate_trading_errors(
        default_return=OpenOrdersDTO(
            success=False,
            orders=[],
            symbol_filter=None,
            error="open orders unavailable",
        )
    )
    def get_open_orders(self, symbol: str | None = None) -> OpenOrdersDTO:
        """Get open orders.

        Legacy path returns raw-ish dicts derived from Alpaca objects.
        When the type system flag is enabled, returns a richer dict with
        a 'domain' key containing the mapped domain Order and a 'summary'.
        """
        try:
            orders = self.alpaca_manager.get_orders(status="open")
            # Optional symbol filter for safety (Alpaca filter applied earlier best-effort)
            if symbol:
                orders = [
                    o
                    for o in orders
                    if getattr(o, "symbol", None) == symbol
                    or (isinstance(o, dict) and o.get("symbol") == symbol)
                ]

            # Always use enriched typed path (using typed domain)
            enriched: list[dict[str, Any]] = []
            for o in orders:
                dom = alpaca_order_to_domain(o)
                enriched.append(
                    {
                        "raw": o,
                        "domain": dom,
                        "summary": summarize_order(dom),
                    }
                )

            return list_to_open_orders_dto(enriched, symbol)
        except Exception as e:
            return OpenOrdersDTO(success=False, orders=[], symbol_filter=symbol, error=str(e))

    # Position Management Operations
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
                    position_dict = {
                        "success": True,
                        "symbol": symbol,
                        "position": {
                            "quantity": position.quantity,
                            "market_value": position.market_value,
                            "unrealized_pnl": position.unrealized_pnl,
                            "weight_percent": position.weight_percent,
                        },
                    }
                    return dict_to_position_summary_dto(position_dict)
                return PositionSummaryDTO(
                    success=False,
                    symbol=symbol,
                    error=f"No position found for {symbol}",
                )
            # Get portfolio summary
            portfolio = self.positions.get_portfolio_summary()
            portfolio_dict = {
                "success": True,
                "portfolio": {
                    "total_market_value": portfolio.total_market_value,
                    "cash_balance": portfolio.cash_balance,
                    "total_positions": portfolio.total_positions,
                    "largest_position_percent": portfolio.largest_position_percent,
                },
            }
            return dict_to_portfolio_summary_dto(portfolio_dict)
        except Exception as e:
            if symbol:
                return PositionSummaryDTO(success=False, symbol=symbol, error=str(e))
            return PortfolioSummaryDTO(success=False, error=str(e))

    def close_position(self, symbol: str, percentage: float = 100.0) -> ClosePositionResultDTO:
        """Close a position using liquidation."""
        try:
            # Sonar: replace float equality check with tolerance
            if not floats_equal(percentage, 100.0):
                return ClosePositionResultDTO(
                    success=False,
                    error="Partial position closure not directly supported. Use liquidate_position for full closure.",
                )
            order_id = self.orders.liquidate_position(symbol)
            return ClosePositionResultDTO(success=True, order_id=order_id)
        except Exception as e:
            return ClosePositionResultDTO(success=False, error=str(e))

    def get_position_analytics(self, symbol: str) -> PositionAnalyticsDTO:
        """Get detailed position analytics."""
        try:
            risk_metrics = self.positions.get_position_risk_metrics(symbol)
            analytics_dict = {
                "success": True,
                "symbol": symbol,
                "risk_metrics": risk_metrics,
            }
            return dict_to_position_analytics_dto(analytics_dict)
        except Exception as e:
            return PositionAnalyticsDTO(success=False, symbol=symbol, error=str(e))

    def calculate_position_metrics(self) -> PositionMetricsDTO:
        """Calculate portfolio-wide position metrics."""
        try:
            diversification_score = self.positions.calculate_diversification_score()
            largest_positions = self.positions.get_largest_positions()
            metrics_dict = {
                "success": True,
                "diversification_score": diversification_score,
                "largest_positions": [
                    {
                        "symbol": pos.symbol,
                        "weight": pos.weight_percent,
                        "value": pos.market_value,
                    }
                    for pos in largest_positions
                ],
            }
            return dict_to_position_metrics_dto(metrics_dict)
        except Exception as e:
            return PositionMetricsDTO(success=False, error=str(e))

    # Market Data Operations
    def get_latest_price(self, symbol: str, validate: bool = True) -> PriceDTO:
        """Get latest price with validation and caching."""
        try:
            price = self.market_data.get_validated_price(symbol)
            if price is not None:
                price_dict = {"success": True, "symbol": symbol, "price": price}
                return dict_to_price_dto(price_dict)
            return PriceDTO(
                success=False,
                symbol=symbol,
                error=f"Could not get price for {symbol}",
            )
        except Exception as e:
            return PriceDTO(success=False, symbol=symbol, error=str(e))

    def get_price_history(
        self,
        symbol: str,
        timeframe: str = "1Day",
        limit: int = 100,
        validate: bool = True,
    ) -> PriceHistoryDTO:
        """Get price history (not directly available - use AlpacaManager directly)."""
        return PriceHistoryDTO(
            success=False,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            error="Price history queries not available in enhanced services. Use AlpacaManager directly.",
        )

    def analyze_spread(self, symbol: str) -> SpreadAnalysisDTO:
        """Analyze bid-ask spread for a symbol."""
        try:
            spread_data = self.market_data.get_spread_analysis(symbol)
            if spread_data:
                spread_dict = {
                    "success": True,
                    "symbol": symbol,
                    "spread_analysis": spread_data,
                }
                return dict_to_spread_analysis_dto(spread_dict)
            return SpreadAnalysisDTO(
                success=False,
                symbol=symbol,
                error=f"Could not analyze spread for {symbol}",
            )
        except Exception as e:
            return SpreadAnalysisDTO(success=False, symbol=symbol, error=str(e))

    def get_market_status(self) -> MarketStatusDTO:
        """Get current market status."""
        try:
            is_open = self.market_data.is_market_hours()
            market_dict = {"success": True, "market_open": is_open}
            return dict_to_market_status_dto(market_dict)
        except Exception as e:
            return MarketStatusDTO(success=False, error=str(e))

    def get_multi_symbol_quotes(self, symbols: list[str]) -> MultiSymbolQuotesDTO:
        """Get quotes for multiple symbols efficiently."""
        try:
            prices = self.market_data.get_batch_prices(symbols)
            quotes_dict = {"success": True, "quotes": prices}
            return dict_to_multi_symbol_quotes_dto(quotes_dict)
        except Exception as e:
            return MultiSymbolQuotesDTO(success=False, error=str(e))

    # Account Management Operations
    def get_account_summary(self) -> AccountSummaryDTO:
        """Get comprehensive account summary with metrics."""
        account_dict = self.account.get_account_summary()
        # Convert to typed and then to DTO
        typed = account_summary_to_typed(account_dict)
        return account_summary_typed_to_dto(typed)

    def check_buying_power(self, required_amount: float) -> BuyingPowerDTO:
        """Check available buying power."""
        buying_power_dict = self.account.check_buying_power(required_amount)
        return dict_to_buying_power_dto(buying_power_dict)

    def get_risk_metrics(self) -> RiskMetricsDTO:
        """Calculate comprehensive risk metrics."""
        risk_metrics_dict = self.account.get_risk_metrics()
        return dict_to_risk_metrics_dto(risk_metrics_dict)

    def validate_trade_eligibility(
        self, symbol: str, quantity: int, side: str, estimated_cost: float | None = None
    ) -> TradeEligibilityDTO:
        """Validate if a trade can be executed."""
        eligibility_dict = self.account.validate_trade_eligibility(
            symbol, quantity, side, estimated_cost or 0.0
        )
        return dict_to_trade_eligibility_dto(eligibility_dict)

    def get_portfolio_allocation(self) -> PortfolioAllocationDTO:
        """Get portfolio allocation and diversification metrics."""
        allocation_dict = self.account.get_portfolio_allocation()
        return dict_to_portfolio_allocation_dto(allocation_dict)

    @translate_trading_errors(
        default_return=EnrichedAccountSummaryDTO(
            raw={},
            summary=AccountSummaryDTO(
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
        )
    )
    def get_account_summary_enriched(self) -> EnrichedAccountSummaryDTO:
        """Enriched account summary with typed domain objects.

        Returns structured data including both the raw provider dictionary and typed domain
        objects. The raw dict is preserved for backward-compatible display layers; the typed
        structure should be preferred for all business logic.
        """
        legacy = self.account.get_account_summary()

        # Always return typed path (using typed domain)
        typed = account_summary_to_typed(legacy)
        enriched_dict = {"raw": legacy, "summary": account_typed_to_serializable(typed)}
        return dict_to_enriched_account_summary_dto(enriched_dict)

    def get_all_positions(self) -> EnrichedPositionsDTO:
        """Get all positions from the underlying repository."""
        try:
            raw_positions = self.alpaca_manager.get_all_positions()
            # Convert to enriched format
            enriched = []
            for position in raw_positions:
                summary = alpaca_position_to_summary(position)
                enriched.append(
                    {
                        "raw": position,
                        "summary": (
                            summary.model_dump() if hasattr(summary, "model_dump") else summary
                        ),
                    }
                )
            return list_to_enriched_positions_dto(enriched)
        except Exception as e:
            return EnrichedPositionsDTO(success=False, positions=[], error=str(e))

    @translate_trading_errors(
        default_return=EnrichedPositionsDTO(
            success=False, positions=[], error="positions unavailable"
        )
    )
    def get_positions_enriched(self) -> EnrichedPositionsDTO:
        """Enriched positions list with typed domain objects.

        Returns list of {"raw": pos, "summary": PositionSummary-as-dict}
        """
        try:
            raw_positions = self.alpaca_manager.get_all_positions()

            # Always return enriched typed path (using typed domain)
            enriched: list[dict[str, Any]] = []
            for p in raw_positions:
                s = alpaca_position_to_summary(p)
                enriched.append(
                    {
                        "raw": p,
                        "summary": {
                            "symbol": s.symbol,
                            "qty": float(s.qty),
                            "avg_entry_price": float(s.avg_entry_price),
                            "current_price": float(s.current_price),
                            "market_value": float(s.market_value),
                            "unrealized_pl": float(s.unrealized_pl),
                            "unrealized_plpc": float(s.unrealized_plpc),
                        },
                    }
                )

            return list_to_enriched_positions_dto(enriched)
        except Exception as e:
            return EnrichedPositionsDTO(success=False, positions=[], error=str(e))

    def get_portfolio_value(self) -> PortfolioValueDTO:
        """Get total portfolio value with typed domain objects."""
        raw = self.alpaca_manager.get_portfolio_value()
        money = to_money_usd(raw)
        return PortfolioValueDTO(value=Decimal(str(raw)), money=money)

    # High-Level Trading Operations
    @translate_trading_errors(
        default_return=SmartOrderExecutionDTO(
            success=False,
            reason="Order execution failed",
            error="Service error",
        )
    )
    def execute_smart_order(
        self,
        symbol: str,
        quantity: int,
        side: str,
        order_type: str = "market",
        **kwargs: Any,  # noqa: ANN401  # Order parameters are dynamic (limit_price, stop_price, etc.)
    ) -> SmartOrderExecutionDTO:
        """Execute a smart order with comprehensive validation and risk management.

        Args:
            symbol: Symbol to trade
            quantity: Number of shares
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', or 'stop_loss'
            **kwargs: Additional order parameters (limit_price, stop_price, etc.)

        Returns:
            Comprehensive order execution result.

        """
        try:
            # Create order ID for lifecycle tracking
            client_order_id = kwargs.get("client_order_id")
            order_id = self._create_order_id(
                client_order_id if isinstance(client_order_id, str) else None
            )
            # Emit initial lifecycle event
            self._emit_lifecycle_event(
                order_id=order_id,
                target_state=OrderLifecycleState.NEW,
                event_type=LifecycleEventType.STATE_CHANGED,
                metadata={
                    "symbol": symbol,
                    "quantity": quantity,
                    "side": side,
                    "order_type": order_type,
                },
            )
            # Create OrderRequestDTO for comprehensive validation
            order_data = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "time_in_force": kwargs.get("time_in_force", "day"),
                "limit_price": kwargs.get("limit_price"),
                "client_order_id": kwargs.get("client_order_id"),
            }

            # Convert to DTO and validate using OrderValidator
            try:
                order_request = dict_to_order_request_dto(order_data)
                validated_order = self.order_validator.validate_order_request(order_request)

                # Emit validation success event
                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=OrderLifecycleState.VALIDATED,
                    event_type=LifecycleEventType.STATE_CHANGED,
                    metadata={
                        "estimated_value": (
                            validated_order.estimated_value
                            if validated_order.estimated_value is not None
                            else Decimal("0")
                        ),
                        "risk_score": validated_order.risk_score,
                        "is_fractional": validated_order.is_fractional,
                    },
                )
                self.logger.info(
                    f"Order validation successful for {symbol}: "
                    f"estimated_value=${validated_order.estimated_value}, "
                    f"risk_score={validated_order.risk_score}, "
                    f"is_fractional={validated_order.is_fractional}"
                )

            except Exception as validation_error:
                # Emit validation failure event
                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=OrderLifecycleState.REJECTED,
                    event_type=LifecycleEventType.REJECTED,
                    metadata={
                        "validation_error": str(validation_error),
                    },
                )

                return SmartOrderExecutionDTO(
                    success=False,
                    reason="Order validation failed",
                    error=str(validation_error),
                    validation_details={
                        "symbol": symbol,
                        "quantity": quantity,
                        "side": side,
                        "order_type": order_type,
                    },
                )

            # Pre-trade validation (legacy compatibility)
            estimated_cost = None
            if side.lower() == "buy" and order_type == "market":
                price_data = self.get_latest_price(symbol)
                if price_data.success and price_data.price is not None:
                    # Keep as Decimal
                    estimated_cost = price_data.price * Decimal(str(quantity))

            eligibility = self.validate_trade_eligibility(
                symbol,
                quantity,
                side,
                (float(estimated_cost) if isinstance(estimated_cost, Decimal) else estimated_cost),
            )
            if not eligibility.eligible:
                # Emit rejection event for failed eligibility
                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=OrderLifecycleState.REJECTED,
                    event_type=LifecycleEventType.REJECTED,
                    metadata={
                        "eligibility_reason": eligibility.reason,
                        "eligibility_details": eligibility.details,
                        "estimated_cost": (float(estimated_cost) if estimated_cost else None),
                    },
                )

                return SmartOrderExecutionDTO(
                    success=False,
                    reason=eligibility.reason or "Trade not eligible",
                    error=(
                        f"Trade not eligible: {eligibility.details}"
                        if eligibility.details
                        else eligibility.reason
                    ),
                    pre_trade_validation=eligibility,
                )

            # Execute the order based on type
            # First, emit submission event
            self._emit_lifecycle_event(
                order_id=order_id,
                target_state=OrderLifecycleState.SUBMITTED,
                event_type=LifecycleEventType.STATE_CHANGED,
                metadata={
                    "order_type": order_type,
                },
            )
            order_result: OrderExecutionResultDTO
            if order_type.lower() == "market":
                # Use canonical executor directly since legacy methods removed
                from decimal import Decimal

                from the_alchemiser.execution.core.executor import (
                    CanonicalOrderExecutor,
                )
                from the_alchemiser.execution.orders.order_request import (
                    OrderRequest,
                )
                from the_alchemiser.execution.orders.order_type import (
                    OrderType,
                )
                from the_alchemiser.execution.orders.side import Side
                from the_alchemiser.shared.types.money import (
                    Money,
                )
                from the_alchemiser.shared.types.quantity import (
                    Quantity,
                )
                from the_alchemiser.shared.types.time_in_force import (
                    TimeInForce,
                )
                from the_alchemiser.shared.value_objects.symbol import Symbol

                try:
                    order_request_domain = OrderRequest(
                        symbol=Symbol(symbol),
                        side=Side("buy" if side.lower() == "buy" else "sell"),
                        quantity=Quantity(Decimal(str(quantity))),
                        order_type=OrderType("market"),
                        time_in_force=TimeInForce("day"),
                        limit_price=None,
                    )
                    executor = CanonicalOrderExecutor(self.alpaca_manager)
                    order_result = executor.execute(order_request_domain)
                except Exception as e:
                    from datetime import UTC, datetime

                    order_result = OrderExecutionResultDTO(
                        success=False,
                        error=str(e),
                        order_id="",
                        status="rejected",
                        filled_qty=Decimal("0"),
                        avg_fill_price=None,
                        submitted_at=datetime.now(UTC),
                        completed_at=None,
                    )
            elif order_type.lower() == "limit":
                limit_price = kwargs.get("limit_price")
                if not limit_price or not isinstance(limit_price, int | float):
                    # Emit error event for missing limit price
                    self._emit_lifecycle_event(
                        order_id=order_id,
                        target_state=OrderLifecycleState.ERROR,
                        event_type=LifecycleEventType.ERROR,
                        metadata={
                            "error": "limit_price required for limit orders",
                        },
                    )
                    return SmartOrderExecutionDTO(
                        success=False, reason="limit_price required for limit orders"
                    )
                # Use canonical executor directly since legacy methods removed
                from decimal import Decimal

                from the_alchemiser.execution.core.executor import (
                    CanonicalOrderExecutor,
                )
                from the_alchemiser.execution.orders.order_request import (
                    OrderRequest,
                )
                from the_alchemiser.execution.orders.order_type import (
                    OrderType,
                )
                from the_alchemiser.execution.orders.side import Side
                from the_alchemiser.shared.types.money import (
                    Money,
                )
                from the_alchemiser.shared.types.quantity import (
                    Quantity,
                )
                from the_alchemiser.shared.types.time_in_force import (
                    TimeInForce,
                )
                from the_alchemiser.shared.value_objects.symbol import Symbol

                try:
                    order_request_domain = OrderRequest(
                        symbol=Symbol(symbol),
                        side=Side("buy" if side.lower() == "buy" else "sell"),
                        quantity=Quantity(Decimal(str(quantity))),
                        order_type=OrderType("limit"),
                        time_in_force=TimeInForce("day"),
                        limit_price=Money(amount=Decimal(str(limit_price)), currency="USD"),
                    )
                    executor = CanonicalOrderExecutor(self.alpaca_manager)
                    order_result = executor.execute(order_request_domain)
                except Exception as e:
                    from datetime import UTC, datetime

                    order_result = OrderExecutionResultDTO(
                        success=False,
                        error=str(e),
                        order_id="",
                        status="rejected",
                        filled_qty=Decimal("0"),
                        avg_fill_price=None,
                        submitted_at=datetime.now(UTC),
                        completed_at=None,
                    )
            elif order_type.lower() == "stop_loss":
                stop_price = kwargs.get("stop_price")
                if not stop_price or not isinstance(stop_price, int | float):
                    # Emit error event for missing stop price
                    self._emit_lifecycle_event(
                        order_id=order_id,
                        target_state=OrderLifecycleState.ERROR,
                        event_type=LifecycleEventType.ERROR,
                        metadata={
                            "error": "stop_price required for stop_loss orders",
                        },
                    )
                    return SmartOrderExecutionDTO(
                        success=False, reason="stop_price required for stop_loss orders"
                    )
                order_result = self.place_stop_loss_order(
                    symbol, quantity, float(stop_price), validate=False
                )
            else:
                # Emit error event for unsupported order type
                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=OrderLifecycleState.ERROR,
                    event_type=LifecycleEventType.ERROR,
                    metadata={
                        "error": f"Unsupported order type: {order_type}",
                    },
                )
                return SmartOrderExecutionDTO(
                    success=False, reason=f"Unsupported order type: {order_type}"
                )

            # Emit lifecycle events based on order result
            if order_result.success:
                status_value = order_result.status.lower() if order_result.status else ""
                # Determine final state based on order status
                if status_value in ("filled", "complete"):
                    final_state = OrderLifecycleState.FILLED
                    event_type = LifecycleEventType.STATE_CHANGED
                elif status_value in ("partially_filled", "partial"):
                    final_state = OrderLifecycleState.PARTIALLY_FILLED
                    event_type = LifecycleEventType.PARTIAL_FILL
                else:
                    # Order acknowledged but not yet filled
                    final_state = OrderLifecycleState.ACKNOWLEDGED
                    event_type = LifecycleEventType.STATE_CHANGED

                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=final_state,
                    event_type=event_type,
                    metadata={
                        "broker_order_id": order_result.order_id,
                        "filled_qty": order_result.filled_qty,
                        "avg_fill_price": order_result.avg_fill_price,
                        "status": order_result.status,
                    },
                )
            else:
                # Order failed - emit error or rejection event
                error_message = order_result.error or "Unknown error"
                error_state = (
                    OrderLifecycleState.REJECTED
                    if "reject" in error_message.lower()
                    else OrderLifecycleState.ERROR
                )
                error_event_type = (
                    LifecycleEventType.REJECTED
                    if error_state == OrderLifecycleState.REJECTED
                    else LifecycleEventType.ERROR
                )

                self._emit_lifecycle_event(
                    order_id=order_id,
                    target_state=error_state,
                    event_type=error_event_type,
                    metadata={
                        "error": error_message,
                        "broker_order_id": (
                            order_result.order_id if order_result.order_id else None
                        ),
                    },
                )

            # Create validation metadata
            order_validation_metadata = OrderValidationMetadataDTO(
                validated_order_id=validated_order.client_order_id,
                estimated_value=validated_order.estimated_value,
                risk_score=validated_order.risk_score,
                is_fractional=validated_order.is_fractional,
                validation_timestamp=validated_order.validation_timestamp,
            )

            # Get account impact
            account_summary = self.get_account_summary_enriched()

            # Check if order was successful (status is not "rejected")
            success = order_result.success and order_result.status != "rejected"

            return SmartOrderExecutionDTO(
                success=success,
                order_execution=order_result,
                pre_trade_validation=eligibility,
                order_validation=order_validation_metadata,
                account_impact=account_summary.summary if success else None,
                reason=None if success else order_result.error,
            )

        except Exception as e:
            # Emit error event for any unexpected exception
            try:
                order_id_var = locals().get("order_id")
                if order_id_var is not None and isinstance(order_id_var, OrderId):
                    self._emit_lifecycle_event(
                        order_id=order_id_var,
                        target_state=OrderLifecycleState.ERROR,
                        event_type=LifecycleEventType.ERROR,
                        metadata={
                            "unexpected_error": str(e),
                            "error_type": type(e).__name__,
                        },
                    )
            except Exception as lifecycle_error:
                self.logger.warning("Failed to emit error lifecycle event: %s", lifecycle_error)

            self.logger.error(f"Unexpected error in execute_smart_order: {e}")
            return SmartOrderExecutionDTO(
                success=False, reason="Unexpected execution error", error=str(e)
            )

    # Order Lifecycle Management Operations
    def get_order_lifecycle_state(self, order_id: OrderId) -> OrderLifecycleState | None:
        """Get the current lifecycle state of an order.

        Args:
            order_id: Order identifier

        Returns:
            Current lifecycle state, or None if order not tracked

        """
        return self.lifecycle_manager.get_state(order_id)

    def get_all_tracked_orders(self) -> dict[OrderId, OrderLifecycleState]:
        """Get all tracked orders and their current lifecycle states.

        Returns:
            Dictionary mapping order IDs to their current states

        """
        return self.lifecycle_manager.get_all_orders()

    def get_lifecycle_metrics(self) -> dict[str, Any]:
        """Get lifecycle metrics from the metrics observer.

        Returns:
            Dictionary containing lifecycle event and transition metrics

        """
        # Find the metrics observer
        for observer in self.lifecycle_dispatcher.iter_observers():
            if hasattr(observer, "get_event_counts") and hasattr(observer, "get_transition_counts"):
                return {
                    "event_counts": observer.get_event_counts(),
                    "transition_counts": observer.get_transition_counts(),
                    "total_observers": self.lifecycle_dispatcher.get_observer_count(),
                    "observer_types": self.lifecycle_dispatcher.get_observer_types(),
                }

        return {
            "event_counts": {},
            "transition_counts": {},
            "total_observers": self.lifecycle_dispatcher.get_observer_count(),
            "observer_types": self.lifecycle_dispatcher.get_observer_types(),
        }

    def execute_order_dto(self, order_request: OrderRequestDTO) -> SmartOrderExecutionDTO:
        """Execute an order using OrderRequestDTO directly.

        This method provides a type-safe interface for order execution using DTOs.

        Args:
            order_request: Validated OrderRequestDTO instance

        Returns:
            Comprehensive order execution result

        """
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
            return SmartOrderExecutionDTO(
                success=False, reason="DTO order execution failed", error=str(e)
            )

    @translate_trading_errors(
        default_return=TradingDashboardDTO(
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
            error="Failed to generate dashboard",
        )
    )
    def get_trading_dashboard(self) -> TradingDashboardDTO:
        """Get a comprehensive trading dashboard with all key metrics.

        Returns:
            Complete trading dashboard data

        """
        try:
            # Get all required data (some methods now return DTOs)
            account_summary = self.get_account_summary_enriched()
            risk_metrics = self.get_risk_metrics()
            portfolio_allocation = self.get_portfolio_allocation()
            pos_summary = self.get_position_summary()
            open_orders = self.get_open_orders()
            market_status = self.get_market_status()

            # Serialize position summary generically
            if isinstance(pos_summary, PositionSummaryDTO):
                position_summary_serialized: dict[str, Any] = {
                    "success": pos_summary.success,
                    "symbol": pos_summary.symbol,
                    "error": pos_summary.error,
                    "position": (
                        {
                            "symbol": pos_summary.position.symbol,
                            "quantity": float(pos_summary.position.quantity),
                            "avg_entry_price": float(pos_summary.position.average_entry_price),
                            "current_price": float(pos_summary.position.current_price),
                            "market_value": float(pos_summary.position.market_value),
                            "unrealized_pnl": float(pos_summary.position.unrealized_pnl),
                            "unrealized_pnl_percent": float(
                                pos_summary.position.unrealized_pnl_percent
                            ),
                        }
                        if pos_summary.position
                        else None
                    ),
                }
            else:  # PortfolioSummaryDTO
                position_summary_serialized = {
                    "success": pos_summary.success,
                    "error": pos_summary.error,
                    "portfolio": (
                        {
                            "total_market_value": float(pos_summary.portfolio.total_market_value),
                            "cash_balance": float(pos_summary.portfolio.cash_balance),
                            "total_positions": pos_summary.portfolio.total_positions,
                            "largest_position_percent": float(
                                pos_summary.portfolio.largest_position_percent
                            ),
                        }
                        if pos_summary.portfolio
                        else None
                    ),
                }

            open_orders_list = (
                [o.summary for o in open_orders.orders] if open_orders.success else []
            )

            return TradingDashboardDTO(
                success=True,
                account=account_summary.summary,
                risk_metrics=risk_metrics.risk_metrics or {},
                portfolio_allocation=portfolio_allocation.allocation_data or {},
                position_summary=position_summary_serialized,
                open_orders=open_orders_list,
                market_status={
                    "market_open": market_status.market_open,
                    "success": market_status.success,
                },
                timestamp=datetime.now(UTC),
            )
        except Exception as e:
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
                error=str(e),
            )

    def close(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self.alpaca_manager, "close"):
                self.alpaca_manager.close()
            self.logger.info("TradingServiceManager closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing TradingServiceManager: {e}")

    # _delegate_to_canonical_executor removed.
