"""Tests for StrategySignalModel."""

import pytest
from datetime import datetime, UTC
from decimal import Decimal

from the_alchemiser.domain.strategies.models.strategy_signal_model import StrategySignalModel
from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.types import StrategySignal as StrategySignalDTO


class TestStrategySignalModel:
    """Test cases for StrategySignalModel."""

    def test_create_from_domain_signal(self) -> None:
        """Test creating model from domain StrategySignal value object."""
        # Create domain value object
        domain_signal = StrategySignal(
            symbol=Symbol("AAPL"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.25")),
            reasoning="Strong earnings forecast",
        )
        
        # Create model from domain object
        model = StrategySignalModel.from_domain_signal(domain_signal)
        
        assert model.symbol == domain_signal.symbol
        assert model.action == domain_signal.action
        assert model.confidence == domain_signal.confidence
        assert model.target_allocation == domain_signal.target_allocation
        assert model.reasoning == domain_signal.reasoning
        assert model.timestamp == domain_signal.timestamp

    def test_create_from_dto_with_string_symbol(self) -> None:
        """Test creating model from DTO with string symbol."""
        dto: StrategySignalDTO = {
            "symbol": "TSLA",
            "action": "SELL",
            "confidence": 0.75,
            "reasoning": "Overvalued stock",
            "allocation_percentage": 15.0,
        }
        
        model = StrategySignalModel.from_dto(dto)
        
        assert model.symbol.value == "TSLA"
        assert model.action == "SELL"
        assert model.confidence.value == Decimal("0.75")
        assert model.reasoning == "Overvalued stock"
        assert model.target_allocation.to_percent() == Decimal("15.0")

    def test_create_from_dto_with_portfolio_symbol(self) -> None:
        """Test creating model from DTO with portfolio (dict) symbol."""
        dto: StrategySignalDTO = {
            "symbol": {"UVXY": 0.25, "BIL": 0.75},
            "action": "HOLD",
            "confidence": 0.6,
            "reasoning": "Portfolio rebalancing",
            "allocation_percentage": 0.0,
        }
        
        model = StrategySignalModel.from_dto(dto)
        
        # Should be converted to "PORTFOLIO" which is 9 chars - too long for Symbol
        # Need to fix the model to handle this case
        assert model.symbol.value == "PORT"  # Shortened version
        assert model.action == "HOLD"
        assert model.confidence.value == Decimal("0.6")
        assert model.reasoning == "Portfolio rebalancing"
        assert model.target_allocation.to_percent() == Decimal("0.0")

    def test_create_from_dto_with_legacy_reason_field(self) -> None:
        """Test creating model from DTO with legacy 'reason' field."""
        dto = {
            "symbol": "SPY",
            "action": "BUY",
            "confidence": 0.9,
            "reason": "Strong market momentum",  # Legacy field name
            "allocation_percentage": 30.0,
        }
        
        model = StrategySignalModel.from_dto(dto)  # type: ignore
        
        assert model.reasoning == "Strong market momentum"

    def test_to_dto_conversion(self) -> None:
        """Test converting model to DTO."""
        model = StrategySignalModel(
            symbol=Symbol("MSFT"),
            action="BUY",
            confidence=Confidence(Decimal("0.85")),
            target_allocation=Percentage(Decimal("0.4")),
            reasoning="Cloud growth potential",
            timestamp=datetime.now(UTC),
        )
        
        dto = model.to_dto()
        
        assert dto["symbol"] == "MSFT"
        assert dto["action"] == "BUY"
        assert dto["confidence"] == 0.85
        assert dto["reasoning"] == "Cloud growth potential"
        assert dto["allocation_percentage"] == 40.0

    def test_signal_type_properties(self) -> None:
        """Test signal type property methods."""
        buy_model = StrategySignalModel(
            symbol=Symbol("BUYST"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.2")),
            reasoning="Buy signal",
            timestamp=datetime.now(UTC),
        )
        
        assert buy_model.is_buy_signal
        assert not buy_model.is_sell_signal
        assert not buy_model.is_hold_signal
        
        sell_model = StrategySignalModel(
            symbol=Symbol("SELLX"),
            action="SELL",
            confidence=Confidence(Decimal("0.7")),
            target_allocation=Percentage(Decimal("0.0")),
            reasoning="Sell signal",
            timestamp=datetime.now(UTC),
        )
        
        assert not sell_model.is_buy_signal
        assert sell_model.is_sell_signal
        assert not sell_model.is_hold_signal
        
        hold_model = StrategySignalModel(
            symbol=Symbol("HOLDX"),
            action="HOLD",
            confidence=Confidence(Decimal("0.5")),
            target_allocation=Percentage(Decimal("0.1")),
            reasoning="Hold signal",
            timestamp=datetime.now(UTC),
        )
        
        assert not hold_model.is_buy_signal
        assert not hold_model.is_sell_signal
        assert hold_model.is_hold_signal

    def test_confidence_properties(self) -> None:
        """Test confidence-related properties."""
        high_conf_model = StrategySignalModel(
            symbol=Symbol("HI"),
            action="BUY",
            confidence=Confidence(Decimal("0.9")),
            target_allocation=Percentage(Decimal("0.3")),
            reasoning="High confidence signal",
            timestamp=datetime.now(UTC),
        )
        
        assert high_conf_model.is_high_confidence
        assert not high_conf_model.is_low_confidence
        assert high_conf_model.confidence_level == "HIGH"
        
        low_conf_model = StrategySignalModel(
            symbol=Symbol("LO"),
            action="HOLD",
            confidence=Confidence(Decimal("0.2")),
            target_allocation=Percentage(Decimal("0.05")),
            reasoning="Low confidence signal",
            timestamp=datetime.now(UTC),
        )
        
        assert not low_conf_model.is_high_confidence
        assert low_conf_model.is_low_confidence
        assert low_conf_model.confidence_level == "LOW"
        
        medium_conf_model = StrategySignalModel(
            symbol=Symbol("MED"),
            action="SELL",
            confidence=Confidence(Decimal("0.65")),
            target_allocation=Percentage(Decimal("0.15")),
            reasoning="Medium confidence signal",
            timestamp=datetime.now(UTC),
        )
        
        assert not medium_conf_model.is_high_confidence
        assert not medium_conf_model.is_low_confidence
        assert medium_conf_model.confidence_level == "MEDIUM"

    def test_allocation_percentage_property(self) -> None:
        """Test allocation percentage property."""
        model = StrategySignalModel(
            symbol=Symbol("TEST"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.25")),  # 25%
            reasoning="Test allocation",
            timestamp=datetime.now(UTC),
        )
        
        assert model.allocation_percentage == Decimal("25")

    def test_model_immutability(self) -> None:
        """Test that StrategySignalModel is immutable."""
        model = StrategySignalModel(
            symbol=Symbol("IMMUT"),
            action="BUY",
            confidence=Confidence(Decimal("0.8")),
            target_allocation=Percentage(Decimal("0.2")),
            reasoning="Test immutability",
            timestamp=datetime.now(UTC),
        )
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            model.action = "SELL"  # type: ignore

    def test_from_dto_with_invalid_domain_signal(self) -> None:
        """Test error handling when creating from invalid domain signal."""
        with pytest.raises(TypeError, match="Expected StrategySignal value object"):
            StrategySignalModel.from_domain_signal("not a signal")  # type: ignore

    def test_roundtrip_conversion(self) -> None:
        """Test that DTO -> Model -> DTO conversion preserves data."""
        original_dto: StrategySignalDTO = {
            "symbol": "ROUND",  # Shortened to fit symbol constraints
            "action": "BUY",
            "confidence": 0.75,
            "reasoning": "Test roundtrip",
            "allocation_percentage": 20.0,
        }
        
        # Convert to model and back
        model = StrategySignalModel.from_dto(original_dto)
        converted_dto = model.to_dto()
        
        # Values should be preserved (with precision consideration)
        assert converted_dto["symbol"] == original_dto["symbol"]
        assert converted_dto["action"] == original_dto["action"]
        assert converted_dto["confidence"] == original_dto["confidence"]
        assert converted_dto["reasoning"] == original_dto["reasoning"]
        assert converted_dto["allocation_percentage"] == original_dto["allocation_percentage"]