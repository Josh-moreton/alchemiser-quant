"""Business Unit: shared | Status: current

Unit tests for OrderRequest and MarketData DTOs.

Tests DTO validation, immutability, serialization, and timezone handling.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.order_request import MarketData, OrderRequest


class TestOrderRequest:
    """Test OrderRequest DTO validation and behavior."""

    def test_valid_order_request_minimal(self):
        """Test creation of valid order request with minimal required fields."""
        now = datetime.now(UTC)
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=now,
            request_id="req-001",
            portfolio_id="portfolio-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
        )
        assert request.correlation_id == "corr-001"
        assert request.causation_id == "cause-001"
        assert request.timestamp == now
        assert request.request_id == "req-001"
        assert request.portfolio_id == "portfolio-001"
        assert request.symbol == "AAPL"
        assert request.side == "BUY"
        assert request.quantity == Decimal("100")
        assert request.order_type == "MARKET"  # default
        assert request.time_in_force == "DAY"  # default

    def test_valid_order_request_complete(self):
        """Test creation of order request with all optional fields."""
        now = datetime.now(UTC)
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=now,
            request_id="req-001",
            portfolio_id="portfolio-001",
            strategy_id="strategy-001",
            symbol="AAPL",
            side="SELL",
            quantity=Decimal("50"),
            order_type="LIMIT",
            limit_price=Decimal("150.50"),
            stop_price=None,
            time_in_force="GTC",
            extended_hours=True,
            execution_priority="SPEED",
            max_slippage_percent=Decimal("0.01"),
            position_intent="CLOSE",
            risk_budget=Decimal("1000.00"),
            reason="Rebalancing",
            rebalance_plan_id="plan-001",
            metadata={"key": "value"},
        )
        assert request.strategy_id == "strategy-001"
        assert request.order_type == "LIMIT"
        assert request.limit_price == Decimal("150.50")
        assert request.time_in_force == "GTC"
        assert request.extended_hours is True
        assert request.execution_priority == "SPEED"
        assert request.max_slippage_percent == Decimal("0.01")
        assert request.position_intent == "CLOSE"
        assert request.risk_budget == Decimal("1000.00")
        assert request.reason == "Rebalancing"
        assert request.rebalance_plan_id == "plan-001"
        assert request.metadata == {"key": "value"}

    def test_order_request_immutable(self):
        """Test that OrderRequest is frozen/immutable."""
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=datetime.now(UTC),
            request_id="req-001",
            portfolio_id="portfolio-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
        )
        with pytest.raises(ValidationError):
            request.quantity = Decimal("200")  # type: ignore[misc]

    def test_symbol_normalization(self):
        """Test that symbol is normalized to uppercase."""
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=datetime.now(UTC),
            request_id="req-001",
            portfolio_id="portfolio-001",
            symbol="  aapl  ",
            side="BUY",
            quantity=Decimal("100"),
        )
        assert request.symbol == "AAPL"

    def test_side_validation_rejects_invalid(self):
        """Test that invalid side values are rejected."""
        # Note: Pydantic Literal validation happens BEFORE field validators,
        # so normalization doesn't apply to Literal fields
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="INVALID",  # type: ignore[arg-type]
                quantity=Decimal("100"),
            )
        assert "side" in str(exc_info.value).lower()

    def test_order_type_validation_rejects_invalid(self):
        """Test that invalid order_type values are rejected."""
        # Note: Pydantic Literal validation happens BEFORE field validators,
        # so normalization doesn't apply to Literal fields
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                order_type="INVALID",  # type: ignore[arg-type]
            )
        assert "order_type" in str(exc_info.value).lower()

    def test_naive_timestamp_converted_to_utc(self):
        """Test that naive timestamp is converted to UTC."""
        naive_time = datetime(2023, 1, 1, 12, 0, 0)
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=naive_time,
            request_id="req-001",
            portfolio_id="portfolio-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
        )
        assert request.timestamp.tzinfo is not None
        assert request.timestamp.tzinfo == UTC

    def test_invalid_quantity_zero(self):
        """Test that zero quantity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("0"),
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_invalid_quantity_negative(self):
        """Test that negative quantity is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("-100"),
            )
        assert "quantity" in str(exc_info.value).lower()

    def test_invalid_limit_price_zero(self):
        """Test that zero limit price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                order_type="LIMIT",
                limit_price=Decimal("0"),
            )
        assert "limit_price" in str(exc_info.value).lower()

    def test_invalid_max_slippage_negative(self):
        """Test that negative max slippage is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                max_slippage_percent=Decimal("-0.01"),
            )
        assert "max_slippage_percent" in str(exc_info.value).lower()

    def test_invalid_max_slippage_exceeds_one(self):
        """Test that max slippage > 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="corr-001",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
                max_slippage_percent=Decimal("1.5"),
            )
        assert "max_slippage_percent" in str(exc_info.value).lower()

    def test_empty_correlation_id(self):
        """Test that empty correlation_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            OrderRequest(
                correlation_id="",
                causation_id="cause-001",
                timestamp=datetime.now(UTC),
                request_id="req-001",
                portfolio_id="portfolio-001",
                symbol="AAPL",
                side="BUY",
                quantity=Decimal("100"),
            )
        assert "correlation_id" in str(exc_info.value).lower()

    def test_to_dict_serialization(self):
        """Test to_dict serializes properly."""
        now = datetime.now(UTC)
        request = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=now,
            request_id="req-001",
            portfolio_id="portfolio-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            limit_price=Decimal("150.50"),
        )
        data = request.to_dict()
        
        assert isinstance(data, dict)
        assert data["correlation_id"] == "corr-001"
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == "100"  # Decimal serialized to string
        assert data["limit_price"] == "150.50"  # Decimal serialized to string
        assert isinstance(data["timestamp"], str)  # datetime serialized to ISO string

    def test_from_dict_deserialization(self):
        """Test from_dict deserializes properly."""
        data = {
            "correlation_id": "corr-001",
            "causation_id": "cause-001",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "request_id": "req-001",
            "portfolio_id": "portfolio-001",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": "100",
            "limit_price": "150.50",
        }
        request = OrderRequest.from_dict(data)
        
        assert request.correlation_id == "corr-001"
        assert request.symbol == "AAPL"
        assert request.quantity == Decimal("100")
        assert request.limit_price == Decimal("150.50")
        assert request.timestamp.tzinfo is not None

    def test_from_dict_handles_z_suffix(self):
        """Test from_dict handles 'Z' timezone suffix."""
        data = {
            "correlation_id": "corr-001",
            "causation_id": "cause-001",
            "timestamp": "2023-01-01T12:00:00Z",
            "request_id": "req-001",
            "portfolio_id": "portfolio-001",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": "100",
        }
        request = OrderRequest.from_dict(data)
        assert request.timestamp.tzinfo is not None

    def test_from_dict_invalid_timestamp(self):
        """Test from_dict raises error for invalid timestamp."""
        data = {
            "correlation_id": "corr-001",
            "causation_id": "cause-001",
            "timestamp": "invalid-timestamp",
            "request_id": "req-001",
            "portfolio_id": "portfolio-001",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": "100",
        }
        with pytest.raises(ValueError) as exc_info:
            OrderRequest.from_dict(data)
        assert "timestamp" in str(exc_info.value).lower()

    def test_from_dict_invalid_decimal(self):
        """Test from_dict raises error for invalid decimal field."""
        data = {
            "correlation_id": "corr-001",
            "causation_id": "cause-001",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "request_id": "req-001",
            "portfolio_id": "portfolio-001",
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": "invalid",
        }
        with pytest.raises(ValueError) as exc_info:
            OrderRequest.from_dict(data)
        assert "quantity" in str(exc_info.value).lower()

    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserves data."""
        now = datetime.now(UTC)
        original = OrderRequest(
            correlation_id="corr-001",
            causation_id="cause-001",
            timestamp=now,
            request_id="req-001",
            portfolio_id="portfolio-001",
            strategy_id="strategy-001",
            symbol="AAPL",
            side="BUY",
            quantity=Decimal("100"),
            order_type="LIMIT",
            limit_price=Decimal("150.50"),
            time_in_force="GTC",
            extended_hours=True,
            execution_priority="SPEED",
            max_slippage_percent=Decimal("0.01"),
            position_intent="OPEN",
            risk_budget=Decimal("1000.00"),
            reason="Test order",
            rebalance_plan_id="plan-001",
            metadata={"key": "value"},
        )
        
        data = original.to_dict()
        restored = OrderRequest.from_dict(data)
        
        assert restored.correlation_id == original.correlation_id
        assert restored.causation_id == original.causation_id
        assert restored.request_id == original.request_id
        assert restored.portfolio_id == original.portfolio_id
        assert restored.strategy_id == original.strategy_id
        assert restored.symbol == original.symbol
        assert restored.side == original.side
        assert restored.quantity == original.quantity
        assert restored.order_type == original.order_type
        assert restored.limit_price == original.limit_price
        assert restored.time_in_force == original.time_in_force
        assert restored.extended_hours == original.extended_hours
        assert restored.execution_priority == original.execution_priority
        assert restored.max_slippage_percent == original.max_slippage_percent
        assert restored.position_intent == original.position_intent
        assert restored.risk_budget == original.risk_budget
        assert restored.reason == original.reason
        assert restored.rebalance_plan_id == original.rebalance_plan_id
        assert restored.metadata == original.metadata


class TestMarketData:
    """Test MarketData DTO validation and behavior."""

    def test_valid_market_data_minimal(self):
        """Test creation of valid market data with minimal required fields."""
        now = datetime.now(UTC)
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=now,
            symbol="AAPL",
            data_type="QUOTE",
        )
        assert market_data.correlation_id == "corr-001"
        assert market_data.timestamp == now
        assert market_data.symbol == "AAPL"
        assert market_data.data_type == "QUOTE"

    def test_valid_market_data_complete(self):
        """Test creation of market data with all optional fields."""
        now = datetime.now(UTC)
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=now,
            symbol="AAPL",
            data_type="BAR",
            price=Decimal("150.00"),
            bid_price=Decimal("149.95"),
            ask_price=Decimal("150.05"),
            volume=Decimal("1000000"),
            bid_size=Decimal("500"),
            ask_size=Decimal("600"),
            open_price=Decimal("149.50"),
            high_price=Decimal("151.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("150.00"),
            market_open=True,
            halted=False,
            data_source="alpaca",
            quality_score=Decimal("0.98"),
            metadata={"exchange": "NYSE"},
        )
        assert market_data.price == Decimal("150.00")
        assert market_data.bid_price == Decimal("149.95")
        assert market_data.ask_price == Decimal("150.05")
        assert market_data.volume == Decimal("1000000")
        assert market_data.quality_score == Decimal("0.98")
        assert market_data.metadata == {"exchange": "NYSE"}

    def test_market_data_immutable(self):
        """Test that MarketData is frozen/immutable."""
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            data_type="QUOTE",
        )
        with pytest.raises(ValidationError):
            market_data.price = Decimal("150.00")  # type: ignore[misc]

    def test_symbol_normalization(self):
        """Test that symbol is normalized to uppercase."""
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=datetime.now(UTC),
            symbol="  aapl  ",
            data_type="QUOTE",
        )
        assert market_data.symbol == "AAPL"

    def test_naive_timestamp_converted_to_utc(self):
        """Test that naive timestamp is converted to UTC."""
        naive_time = datetime(2023, 1, 1, 12, 0, 0)
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=naive_time,
            symbol="AAPL",
            data_type="QUOTE",
        )
        assert market_data.timestamp.tzinfo is not None
        assert market_data.timestamp.tzinfo == UTC

    def test_invalid_price_zero(self):
        """Test that zero price is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                correlation_id="corr-001",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                data_type="QUOTE",
                price=Decimal("0"),
            )
        assert "price" in str(exc_info.value).lower()

    def test_invalid_quality_score_negative(self):
        """Test that negative quality score is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                correlation_id="corr-001",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                data_type="QUOTE",
                quality_score=Decimal("-0.1"),
            )
        assert "quality_score" in str(exc_info.value).lower()

    def test_invalid_quality_score_exceeds_one(self):
        """Test that quality score > 1 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MarketData(
                correlation_id="corr-001",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                data_type="QUOTE",
                quality_score=Decimal("1.5"),
            )
        assert "quality_score" in str(exc_info.value).lower()

    def test_to_dict_serialization(self):
        """Test to_dict serializes properly."""
        now = datetime.now(UTC)
        market_data = MarketData(
            correlation_id="corr-001",
            timestamp=now,
            symbol="AAPL",
            data_type="QUOTE",
            price=Decimal("150.00"),
            volume=Decimal("1000000"),
        )
        data = market_data.to_dict()
        
        assert isinstance(data, dict)
        assert data["correlation_id"] == "corr-001"
        assert data["symbol"] == "AAPL"
        assert data["price"] == "150.00"  # Decimal serialized to string
        assert data["volume"] == "1000000"
        assert isinstance(data["timestamp"], str)

    def test_from_dict_deserialization(self):
        """Test from_dict deserializes properly."""
        data = {
            "correlation_id": "corr-001",
            "timestamp": "2023-01-01T12:00:00+00:00",
            "symbol": "AAPL",
            "data_type": "QUOTE",
            "price": "150.00",
            "volume": "1000000",
        }
        market_data = MarketData.from_dict(data)
        
        assert market_data.correlation_id == "corr-001"
        assert market_data.symbol == "AAPL"
        assert market_data.price == Decimal("150.00")
        assert market_data.volume == Decimal("1000000")
        assert market_data.timestamp.tzinfo is not None

    def test_from_dict_handles_z_suffix(self):
        """Test from_dict handles 'Z' timezone suffix."""
        data = {
            "correlation_id": "corr-001",
            "timestamp": "2023-01-01T12:00:00Z",
            "symbol": "AAPL",
            "data_type": "QUOTE",
        }
        market_data = MarketData.from_dict(data)
        assert market_data.timestamp.tzinfo is not None

    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserves data."""
        now = datetime.now(UTC)
        original = MarketData(
            correlation_id="corr-001",
            timestamp=now,
            symbol="AAPL",
            data_type="BAR",
            price=Decimal("150.00"),
            bid_price=Decimal("149.95"),
            ask_price=Decimal("150.05"),
            volume=Decimal("1000000"),
            bid_size=Decimal("500"),
            ask_size=Decimal("600"),
            open_price=Decimal("149.50"),
            high_price=Decimal("151.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("150.00"),
            market_open=True,
            halted=False,
            data_source="alpaca",
            quality_score=Decimal("0.98"),
            metadata={"exchange": "NYSE"},
        )
        
        data = original.to_dict()
        restored = MarketData.from_dict(data)
        
        assert restored.correlation_id == original.correlation_id
        assert restored.timestamp.replace(microsecond=0) == original.timestamp.replace(microsecond=0)
        assert restored.symbol == original.symbol
        assert restored.data_type == original.data_type
        assert restored.price == original.price
        assert restored.bid_price == original.bid_price
        assert restored.ask_price == original.ask_price
        assert restored.volume == original.volume
        assert restored.quality_score == original.quality_score
        assert restored.metadata == original.metadata
