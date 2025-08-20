import pytest
from decimal import Decimal
from datetime import datetime, UTC

from tests._tolerances import DEFAULT_ATL
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    legacy_signal_to_typed,
    typed_strategy_signal_to_validated_order,
    typed_dict_to_domain_signal,
    convert_signals_dict_to_domain,
)
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal as TypedStrategySignal
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.strategies.strategy_manager import StrategyType


def test_legacy_to_typed_basic_buy():
    legacy = {
        "symbol": "AAPL",
        "action": "buy",
        "reason": "RSI oversold",
        "confidence": 0.75,
        "allocation_percentage": 25.0,
    }
    typed = legacy_signal_to_typed(legacy)

    assert typed["symbol"] == "AAPL"
    assert typed["action"] == "BUY"
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert typed["confidence"] == pytest.approx(0.75, rel=1e-9, abs=DEFAULT_ATL)
    assert typed["reasoning"] == "RSI oversold"
    # Sonar rule: avoid direct float comparison (IEEE-754 rounding).
    assert typed["allocation_percentage"] == pytest.approx(25.0, rel=1e-9, abs=DEFAULT_ATL)


def test_legacy_to_typed_action_enum_like():
    # Simulate ActionType enum string repr
    legacy = {"symbol": "SPY", "action": "ActionType.SELL", "reason": "Take profit"}
    typed = legacy_signal_to_typed(legacy)
    assert typed["action"] == "SELL"


def test_legacy_portfolio_symbol_maps_to_label():
    legacy = {"symbol": {"UVXY": 0.25, "BIL": 0.75}, "action": "BUY", "reason": "Hedge"}
    typed = legacy_signal_to_typed(legacy)
    assert typed["symbol"] == "PORTFOLIO"


# Tests for typed domain StrategySignal → ValidatedOrderDTO mapping


def test_typed_signal_to_validated_order_buy():
    """Test converting BUY signal to validated order."""
    signal = TypedStrategySignal(
        symbol=Symbol("AAPL"),
        action="BUY",
        confidence=Confidence(Decimal("0.8")),
        target_allocation=Percentage(Decimal("0.25")),  # 25%
        reasoning="Strong bullish signal"
    )
    
    portfolio_value = Decimal("100000")  # $100k portfolio
    
    result = typed_strategy_signal_to_validated_order(signal, portfolio_value)
    
    assert result.symbol == "AAPL"
    assert result.side == "buy"
    assert result.quantity == pytest.approx(Decimal("25000"), rel=1e-9, abs=DEFAULT_ATL)  # 25% of 100k
    assert result.order_type == "market"
    assert result.time_in_force == "day"
    assert result.limit_price is None
    assert result.estimated_value == pytest.approx(Decimal("25000"), rel=1e-9, abs=DEFAULT_ATL)
    assert result.risk_score == pytest.approx(Decimal("0.2"), rel=1e-9, abs=DEFAULT_ATL)  # 1 - 0.8 confidence
    assert isinstance(result.validation_timestamp, datetime)


def test_typed_signal_to_validated_order_sell():
    """Test converting SELL signal to validated order."""
    signal = TypedStrategySignal(
        symbol=Symbol("TSLA"),
        action="SELL",
        confidence=Confidence(Decimal("0.9")),
        target_allocation=Percentage(Decimal("0.1")),  # 10%
        reasoning="Overbought conditions"
    )
    
    portfolio_value = Decimal("50000")  # $50k portfolio
    
    result = typed_strategy_signal_to_validated_order(signal, portfolio_value)
    
    assert result.symbol == "TSLA"
    assert result.side == "sell"
    assert result.quantity == pytest.approx(Decimal("5000"), rel=1e-9, abs=DEFAULT_ATL)  # 10% of 50k
    assert result.order_type == "market"
    assert result.risk_score == pytest.approx(Decimal("0.1"), rel=1e-9, abs=DEFAULT_ATL)  # 1 - 0.9 confidence


def test_typed_signal_to_validated_order_limit():
    """Test creating limit order from signal."""
    signal = TypedStrategySignal(
        symbol=Symbol("SPY"),
        action="BUY",
        confidence=Confidence(Decimal("0.75")),
        target_allocation=Percentage(Decimal("0.5")),
        reasoning="Support level reached"
    )
    
    portfolio_value = Decimal("200000")
    limit_price = Decimal("420.50")
    
    result = typed_strategy_signal_to_validated_order(
        signal, 
        portfolio_value,
        order_type="limit",
        limit_price=limit_price,
        time_in_force="gtc"
    )
    
    assert result.order_type == "limit"
    assert result.limit_price == pytest.approx(limit_price, rel=1e-9, abs=DEFAULT_ATL)
    assert result.time_in_force == "gtc"
    assert result.quantity == pytest.approx(Decimal("100000"), rel=1e-9, abs=DEFAULT_ATL)  # 50% of 200k


def test_typed_signal_to_validated_order_hold_raises_error():
    """Test that HOLD signals raise an error as they cannot be converted to orders."""
    signal = TypedStrategySignal(
        symbol=Symbol("VTI"),
        action="HOLD",
        confidence=Confidence(Decimal("0.6")),
        target_allocation=Percentage(Decimal("0.3")),
        reasoning="Sideways market"
    )
    
    with pytest.raises(ValueError, match="HOLD signals cannot be converted to orders"):
        typed_strategy_signal_to_validated_order(signal, Decimal("100000"))


def test_typed_signal_to_validated_order_limit_without_price_raises_error():
    """Test that limit orders without limit_price raise an error."""
    signal = TypedStrategySignal(
        symbol=Symbol("QQQ"),
        action="BUY",
        confidence=Confidence(Decimal("0.7")),
        target_allocation=Percentage(Decimal("0.2")),
        reasoning="Tech recovery"
    )
    
    with pytest.raises(ValueError, match="Limit price required for limit orders"):
        typed_strategy_signal_to_validated_order(
            signal, 
            Decimal("100000"),
            order_type="limit"
        )


def test_typed_signal_to_validated_order_zero_allocation_raises_error():
    """Test that zero allocation raises an error."""
    signal = TypedStrategySignal(
        symbol=Symbol("MSFT"),
        action="BUY",
        confidence=Confidence(Decimal("0.8")),
        target_allocation=Percentage(Decimal("0")),  # 0% allocation
        reasoning="Testing edge case"
    )
    
    with pytest.raises(ValueError, match="Calculated quantity must be positive"):
        typed_strategy_signal_to_validated_order(signal, Decimal("100000"))


def test_typed_signal_to_validated_order_with_client_id():
    """Test creating order with custom client order ID."""
    signal = TypedStrategySignal(
        symbol=Symbol("AMZN"),
        action="BUY",
        confidence=Confidence(Decimal("0.85")),
        target_allocation=Percentage(Decimal("0.15")),
        reasoning="E-commerce growth"
    )
    
    client_id = "TEST_ORDER_001"
    result = typed_strategy_signal_to_validated_order(
        signal, 
        Decimal("100000"),
        client_order_id=client_id
    )
    
    assert result.client_order_id == client_id
    assert result.symbol == "AMZN"


# Tests for TypedDict to Domain signal conversion


def test_typed_dict_to_domain_signal_basic():
    """Test converting TypedDict StrategySignal to domain StrategySignal."""
    typed_dict_signal = {
        "symbol": "MSFT", 
        "action": "BUY",
        "confidence": 0.85,
        "reasoning": "Strong earnings",
        "allocation_percentage": 30.0
    }
    
    domain_signal = typed_dict_to_domain_signal(typed_dict_signal)
    
    assert domain_signal.symbol.value == "MSFT"
    assert domain_signal.action == "BUY"
    assert domain_signal.confidence.value == pytest.approx(Decimal("0.85"), rel=1e-9, abs=DEFAULT_ATL)
    assert domain_signal.reasoning == "Strong earnings"
    assert domain_signal.target_allocation.value == pytest.approx(Decimal("0.3"), rel=1e-9, abs=DEFAULT_ATL)  # 30% -> 0.3


def test_typed_dict_to_domain_signal_portfolio():
    """Test converting portfolio signal to domain signal.""" 
    typed_dict_signal = {
        "symbol": {"AAPL": 0.6, "MSFT": 0.4},
        "action": "SELL", 
        "confidence": 0.7,
        "allocation_percentage": 50.0
    }
    
    domain_signal = typed_dict_to_domain_signal(typed_dict_signal)
    
    assert domain_signal.symbol.value == "PORT"  # Shortened from PORTFOLIO
    assert domain_signal.action == "SELL"
    assert domain_signal.confidence.value == pytest.approx(Decimal("0.7"), rel=1e-9, abs=DEFAULT_ATL)


def test_convert_signals_dict_to_domain():
    """Test converting entire dict of TypedDict signals to domain signals."""
    legacy_signals = {
        StrategyType.NUCLEAR: {
            "symbol": "VTI",
            "action": "BUY", 
            "confidence": 0.8,
            "allocation_percentage": 25.0
        },
        StrategyType.TECL: {
            "symbol": "TECL",
            "action": "SELL",
            "confidence": 0.6,
            "allocation_percentage": 15.0 
        }
    }
    
    domain_signals = convert_signals_dict_to_domain(legacy_signals)
    
    assert len(domain_signals) == 2
    assert StrategyType.NUCLEAR in domain_signals
    assert StrategyType.TECL in domain_signals
    
    nuclear_signal = domain_signals[StrategyType.NUCLEAR]
    assert nuclear_signal.symbol.value == "VTI"
    assert nuclear_signal.action == "BUY"
    
    tecl_signal = domain_signals[StrategyType.TECL] 
    assert tecl_signal.symbol.value == "TECL"
    assert tecl_signal.action == "SELL"
