"""
Unit tests for execution DTOs.

Tests validate key constraints, validation logic, and type safety
for trading execution DTOs in the_alchemiser.interfaces.schemas.execution.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.interfaces.schemas.execution import (
    ExecutionResultDTO,
    LambdaEventDTO,
    LimitOrderResultDTO,
    OrderHistoryDTO,
    QuoteDTO,
    TradingAction,
    TradingPlanDTO,
    WebSocketResultDTO,
    WebSocketStatus,
)


class TestTradingPlanDTO:
    """Test TradingPlanDTO validation and constraints."""

    def test_valid_trading_plan(self) -> None:
        """Test creating a valid trading plan."""
        plan = TradingPlanDTO(
            symbol="AAPL",
            action=TradingAction.BUY,
            quantity=Decimal("100"),
            estimated_price=Decimal("150.25"),
            reasoning="Strong momentum signal"
        )
        
        assert plan.symbol == "AAPL"
        assert plan.action == TradingAction.BUY
        assert plan.quantity == Decimal("100")
        assert plan.estimated_price == Decimal("150.25")
        assert plan.reasoning == "Strong momentum signal"

    def test_symbol_normalization(self) -> None:
        """Test symbol is normalized to uppercase."""
        plan = TradingPlanDTO(
            symbol="aapl",
            action=TradingAction.BUY,
            quantity=Decimal("100"),
            estimated_price=Decimal("150.25"),
            reasoning="Test"
        )
        
        assert plan.symbol == "AAPL"

    def test_symbol_validation_empty(self) -> None:
        """Test symbol validation fails for empty strings."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="",
                action=TradingAction.BUY,
                quantity=Decimal("100"),
                estimated_price=Decimal("150.25"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Symbol cannot be empty" in error["msg"]

    def test_symbol_validation_non_alphanumeric(self) -> None:
        """Test symbol validation fails for non-alphanumeric characters."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="AA-PL",
                action=TradingAction.BUY,
                quantity=Decimal("100"),
                estimated_price=Decimal("150.25"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Symbol must be alphanumeric" in error["msg"]

    def test_quantity_validation_negative(self) -> None:
        """Test quantity validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="AAPL",
                action=TradingAction.BUY,
                quantity=Decimal("-100"),
                estimated_price=Decimal("150.25"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Quantity must be greater than 0" in error["msg"]

    def test_quantity_validation_zero(self) -> None:
        """Test quantity validation fails for zero values."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="AAPL",
                action=TradingAction.BUY,
                quantity=Decimal("0"),
                estimated_price=Decimal("150.25"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Quantity must be greater than 0" in error["msg"]

    def test_estimated_price_validation_negative(self) -> None:
        """Test estimated price validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="AAPL",
                action=TradingAction.BUY,
                quantity=Decimal("100"),
                estimated_price=Decimal("-150.25"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Estimated price must be greater than 0" in error["msg"]

    def test_estimated_price_validation_zero(self) -> None:
        """Test estimated price validation fails for zero values."""
        with pytest.raises(ValidationError) as exc_info:
            TradingPlanDTO(
                symbol="AAPL",
                action=TradingAction.BUY,
                quantity=Decimal("100"),
                estimated_price=Decimal("0"),
                reasoning="Test"
            )
        
        error = exc_info.value.errors()[0]
        assert "Estimated price must be greater than 0" in error["msg"]

    def test_immutability(self) -> None:
        """Test that DTO is immutable (frozen)."""
        plan = TradingPlanDTO(
            symbol="AAPL",
            action=TradingAction.BUY,
            quantity=Decimal("100"),
            estimated_price=Decimal("150.25"),
            reasoning="Test"
        )
        
        with pytest.raises(ValidationError):
            plan.symbol = "TSLA"  # type: ignore[misc]


class TestQuoteDTO:
    """Test QuoteDTO validation and constraints."""

    def test_valid_quote(self) -> None:
        """Test creating a valid quote."""
        quote = QuoteDTO(
            bid_price=Decimal("150.20"),
            ask_price=Decimal("150.25"),
            bid_size=Decimal("100"),
            ask_size=Decimal("200"),
            timestamp="2024-01-01T10:00:00Z"
        )
        
        assert quote.bid_price == Decimal("150.20")
        assert quote.ask_price == Decimal("150.25")
        assert quote.bid_size == Decimal("100")
        assert quote.ask_size == Decimal("200")
        assert quote.timestamp == "2024-01-01T10:00:00Z"

    def test_price_validation_negative(self) -> None:
        """Test price validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            QuoteDTO(
                bid_price=Decimal("-150.20"),
                ask_price=Decimal("150.25"),
                bid_size=Decimal("100"),
                ask_size=Decimal("200"),
                timestamp="2024-01-01T10:00:00Z"
            )
        
        error = exc_info.value.errors()[0]
        assert "Price must be greater than 0" in error["msg"]

    def test_size_validation_negative(self) -> None:
        """Test size validation fails for negative values."""
        with pytest.raises(ValidationError) as exc_info:
            QuoteDTO(
                bid_price=Decimal("150.20"),
                ask_price=Decimal("150.25"),
                bid_size=Decimal("-100"),
                ask_size=Decimal("200"),
                timestamp="2024-01-01T10:00:00Z"
            )
        
        error = exc_info.value.errors()[0]
        assert "Size must be greater than 0" in error["msg"]


class TestWebSocketResultDTO:
    """Test WebSocketResultDTO functionality."""

    def test_valid_websocket_result(self) -> None:
        """Test creating a valid WebSocket result."""
        result = WebSocketResultDTO(
            status=WebSocketStatus.COMPLETED,
            message="Operation successful",
            orders_completed=["ORDER_123", "ORDER_456"]
        )
        
        assert result.status == WebSocketStatus.COMPLETED
        assert result.message == "Operation successful"
        assert result.orders_completed == ["ORDER_123", "ORDER_456"]

    def test_default_orders_completed(self) -> None:
        """Test default empty list for orders_completed."""
        result = WebSocketResultDTO(
            status=WebSocketStatus.ERROR,
            message="Connection failed"
        )
        
        assert result.orders_completed == []


class TestLambdaEventDTO:
    """Test LambdaEventDTO functionality."""

    def test_empty_lambda_event(self) -> None:
        """Test creating an empty Lambda event."""
        event = LambdaEventDTO()
        
        assert event.mode is None
        assert event.trading_mode is None
        assert event.ignore_market_hours is None
        assert event.arguments is None

    def test_full_lambda_event(self) -> None:
        """Test creating a Lambda event with all fields."""
        event = LambdaEventDTO(
            mode="production",
            trading_mode="live",
            ignore_market_hours=True,
            arguments=["--strategy", "nuclear"]
        )
        
        assert event.mode == "production"
        assert event.trading_mode == "live"
        assert event.ignore_market_hours is True
        assert event.arguments == ["--strategy", "nuclear"]


class TestExecutionResultDTO:
    """Test ExecutionResultDTO functionality."""

    def test_valid_execution_result(self) -> None:
        """Test creating a valid execution result."""
        # Create mock data matching the expected types
        account_info = {
            "account_id": "123",
            "equity": "10000.00",
            "cash": "5000.00",
            "buying_power": "15000.00",
            "day_trades_remaining": 3,
            "portfolio_value": "10000.00",
            "last_equity": "9800.00",
            "daytrading_buying_power": "30000.00",
            "regt_buying_power": "15000.00",
            "status": "ACTIVE"
        }
        
        order_details = {
            "id": "ORDER_123",
            "symbol": "AAPL",
            "qty": "100",
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": "100",
            "filled_avg_price": "150.25",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:01:00Z"
        }
        
        result = ExecutionResultDTO(
            orders_executed=[order_details],
            account_info_before=account_info,
            account_info_after=account_info,
            execution_summary={"total_orders": 1, "success": True},
            final_portfolio_state={"AAPL": 100}
        )
        
        assert len(result.orders_executed) == 1
        assert result.execution_summary["total_orders"] == 1
        assert result.final_portfolio_state == {"AAPL": 100}


class TestOrderHistoryDTO:
    """Test OrderHistoryDTO functionality."""

    def test_valid_order_history(self) -> None:
        """Test creating a valid order history."""
        order_details = {
            "id": "ORDER_123",
            "symbol": "AAPL",
            "qty": "100",
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": "100",
            "filled_avg_price": "150.25",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:01:00Z"
        }
        
        history = OrderHistoryDTO(
            orders=[order_details],
            metadata={"total_count": 1, "date_range": "2024-01-01"}
        )
        
        assert len(history.orders) == 1
        assert history.metadata["total_count"] == 1

    def test_default_metadata(self) -> None:
        """Test default empty metadata."""
        history = OrderHistoryDTO(orders=[])
        
        assert history.metadata == {}


class TestLimitOrderResultDTO:
    """Test LimitOrderResultDTO functionality."""

    def test_successful_limit_order_result(self) -> None:
        """Test successful limit order result."""
        result = LimitOrderResultDTO(
            order_request={"symbol": "AAPL", "quantity": 100},
            error_message=None
        )
        
        assert result.order_request is not None
        assert result.error_message is None

    def test_failed_limit_order_result(self) -> None:
        """Test failed limit order result."""
        result = LimitOrderResultDTO(
            order_request=None,
            error_message="Insufficient funds"
        )
        
        assert result.order_request is None
        assert result.error_message == "Insufficient funds"


class TestEnumsAndTypes:
    """Test enums and type definitions."""

    def test_trading_action_enum(self) -> None:
        """Test TradingAction enum values."""
        assert TradingAction.BUY == "BUY"
        assert TradingAction.SELL == "SELL"

    def test_websocket_status_enum(self) -> None:
        """Test WebSocketStatus enum values."""
        assert WebSocketStatus.COMPLETED == "completed"
        assert WebSocketStatus.TIMEOUT == "timeout"
        assert WebSocketStatus.ERROR == "error"