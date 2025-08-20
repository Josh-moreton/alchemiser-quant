"""Tests for StrategyPositionModel."""

import pytest
from decimal import Decimal

from the_alchemiser.domain.strategies.models.strategy_position_model import StrategyPositionModel
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.types import StrategyPositionData as StrategyPositionDTO


class TestStrategyPositionModel:
    """Test cases for StrategyPositionModel."""

    def test_create_from_dto(self) -> None:
        """Test creating model from DTO."""
        dto: StrategyPositionDTO = {
            "symbol": "AAPL",
            "quantity": 100.0,
            "entry_price": 150.50,
            "current_price": 155.75,
            "strategy_type": "momentum",
        }
        
        model = StrategyPositionModel.from_dto(dto)
        
        assert model.symbol.value == "AAPL"
        assert model.quantity == Decimal("100.0")
        assert model.entry_price == Decimal("150.50")
        assert model.current_price == Decimal("155.75")
        assert model.strategy_type == "momentum"

    def test_create_from_dto_with_fractional_shares(self) -> None:
        """Test creating model from DTO with fractional shares."""
        dto: StrategyPositionDTO = {
            "symbol": "TSLA",
            "quantity": 12.5,
            "entry_price": 200.25,
            "current_price": 195.50,
            "strategy_type": "mean_reversion",
        }
        
        model = StrategyPositionModel.from_dto(dto)
        
        assert model.symbol.value == "TSLA"
        assert model.quantity == Decimal("12.5")
        assert model.entry_price == Decimal("200.25")
        assert model.current_price == Decimal("195.50")

    def test_to_dto_conversion(self) -> None:
        """Test converting model to DTO."""
        model = StrategyPositionModel(
            symbol=Symbol("MSFT"),
            quantity=Decimal("50.0"),
            entry_price=Decimal("300.00"),
            current_price=Decimal("320.50"),
            strategy_type="growth",
        )
        
        dto = model.to_dto()
        
        assert dto["symbol"] == "MSFT"
        assert dto["quantity"] == 50.0
        assert dto["entry_price"] == 300.0
        assert dto["current_price"] == 320.5
        assert dto["strategy_type"] == "growth"

    def test_unrealized_pnl_calculation(self) -> None:
        """Test unrealized P&L calculation."""
        # Profitable long position
        profitable_model = StrategyPositionModel(
            symbol=Symbol("PROF"),
            quantity=Decimal("100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("55.00"),
            strategy_type="test",
        )
        
        expected_pnl = Decimal("500.00")  # (55 - 50) * 100
        assert profitable_model.unrealized_pnl == expected_pnl
        assert profitable_model.unrealized_pnl_float == 500.0
        
        # Loss-making long position
        loss_model = StrategyPositionModel(
            symbol=Symbol("LOSS"),
            quantity=Decimal("200"),
            entry_price=Decimal("25.00"),
            current_price=Decimal("22.50"),
            strategy_type="test",
        )
        
        expected_loss = Decimal("-500.00")  # (22.5 - 25) * 200
        assert loss_model.unrealized_pnl == expected_loss
        assert loss_model.unrealized_pnl_float == -500.0

    def test_unrealized_pnl_percentage_calculation(self) -> None:
        """Test unrealized P&L percentage calculation."""
        model = StrategyPositionModel(
            symbol=Symbol("PERC"),
            quantity=Decimal("100"),
            entry_price=Decimal("100.00"),
            current_price=Decimal("110.00"),
            strategy_type="test",
        )
        
        expected_percentage = Decimal("10.00")  # 10% gain
        assert model.unrealized_pnl_percentage == expected_percentage
        assert model.unrealized_pnl_percentage_float == 10.0

    def test_unrealized_pnl_percentage_zero_entry_price(self) -> None:
        """Test P&L percentage with zero entry price."""
        model = StrategyPositionModel(
            symbol=Symbol("ZERO"),
            quantity=Decimal("100"),
            entry_price=Decimal("0.00"),
            current_price=Decimal("10.00"),
            strategy_type="test",
        )
        
        assert model.unrealized_pnl_percentage == Decimal("0")

    def test_total_value_calculation(self) -> None:
        """Test total value calculation."""
        model = StrategyPositionModel(
            symbol=Symbol("VAL"),
            quantity=Decimal("50"),
            entry_price=Decimal("100.00"),
            current_price=Decimal("120.00"),
            strategy_type="test",
        )
        
        expected_value = Decimal("6000.00")  # 50 * 120
        assert model.total_value == expected_value
        assert model.total_value_float == 6000.0

    def test_total_value_with_negative_quantity(self) -> None:
        """Test total value calculation with negative quantity (short position)."""
        short_model = StrategyPositionModel(
            symbol=Symbol("SHORT"),
            quantity=Decimal("-100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("45.00"),
            strategy_type="short",
        )
        
        # Should use absolute value of quantity
        expected_value = Decimal("4500.00")  # abs(-100) * 45
        assert short_model.total_value == expected_value

    def test_position_direction_properties(self) -> None:
        """Test position direction properties."""
        # Long position
        long_model = StrategyPositionModel(
            symbol=Symbol("LONG"),
            quantity=Decimal("100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("55.00"),
            strategy_type="long",
        )
        
        assert long_model.is_long
        assert not long_model.is_short
        
        # Short position
        short_model = StrategyPositionModel(
            symbol=Symbol("SHORT"),
            quantity=Decimal("-50"),
            entry_price=Decimal("40.00"),
            current_price=Decimal("35.00"),
            strategy_type="short",
        )
        
        assert not short_model.is_long
        assert short_model.is_short
        
        # Zero position (edge case)
        zero_model = StrategyPositionModel(
            symbol=Symbol("ZERO"),
            quantity=Decimal("0"),
            entry_price=Decimal("30.00"),
            current_price=Decimal("30.00"),
            strategy_type="neutral",
        )
        
        assert not zero_model.is_long
        assert not zero_model.is_short

    def test_profitability_property(self) -> None:
        """Test profitability property."""
        # Profitable position
        profitable_model = StrategyPositionModel(
            symbol=Symbol("PROF"),
            quantity=Decimal("100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("60.00"),
            strategy_type="winning",
        )
        
        assert profitable_model.is_profitable
        
        # Unprofitable position
        loss_model = StrategyPositionModel(
            symbol=Symbol("LOSS"),
            quantity=Decimal("100"),
            entry_price=Decimal("60.00"),
            current_price=Decimal("50.00"),
            strategy_type="losing",
        )
        
        assert not loss_model.is_profitable
        
        # Break-even position
        breakeven_model = StrategyPositionModel(
            symbol=Symbol("EVEN"),
            quantity=Decimal("100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("50.00"),
            strategy_type="neutral",
        )
        
        assert not breakeven_model.is_profitable

    def test_short_position_profitability(self) -> None:
        """Test profitability for short positions."""
        # Profitable short position (price went down)
        profitable_short = StrategyPositionModel(
            symbol=Symbol("SPROF"),
            quantity=Decimal("-100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("45.00"),
            strategy_type="short",
        )
        
        # P&L = (45 - 50) * (-100) = 500
        assert profitable_short.unrealized_pnl == Decimal("500.00")
        assert profitable_short.is_profitable
        
        # Unprofitable short position (price went up)
        loss_short = StrategyPositionModel(
            symbol=Symbol("SLOSS"),
            quantity=Decimal("-100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("55.00"),
            strategy_type="short",
        )
        
        # P&L = (55 - 50) * (-100) = -500
        assert loss_short.unrealized_pnl == Decimal("-500.00")
        assert not loss_short.is_profitable

    def test_validation_errors(self) -> None:
        """Test validation errors for invalid data."""
        # Negative entry price
        with pytest.raises(ValueError, match="Entry price cannot be negative"):
            StrategyPositionModel(
                symbol=Symbol("TEST"),
                quantity=Decimal("100"),
                entry_price=Decimal("-10.00"),
                current_price=Decimal("50.00"),
                strategy_type="test",
            )
        
        # Negative current price
        with pytest.raises(ValueError, match="Current price cannot be negative"):
            StrategyPositionModel(
                symbol=Symbol("TEST"),
                quantity=Decimal("100"),
                entry_price=Decimal("50.00"),
                current_price=Decimal("-10.00"),
                strategy_type="test",
            )

    def test_model_immutability(self) -> None:
        """Test that StrategyPositionModel is immutable."""
        model = StrategyPositionModel(
            symbol=Symbol("IMMUT"),
            quantity=Decimal("100"),
            entry_price=Decimal("50.00"),
            current_price=Decimal("55.00"),
            strategy_type="test",
        )
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            model.quantity = Decimal("200")  # type: ignore

    def test_roundtrip_conversion(self) -> None:
        """Test that DTO -> Model -> DTO conversion preserves data."""
        original_dto: StrategyPositionDTO = {
            "symbol": "ROUND",  # Shortened to fit symbol constraints
            "quantity": 75.5,
            "entry_price": 123.45,
            "current_price": 130.67,
            "strategy_type": "test_strategy",
        }
        
        # Convert to model and back
        model = StrategyPositionModel.from_dto(original_dto)
        converted_dto = model.to_dto()
        
        # Values should be preserved
        assert converted_dto["symbol"] == original_dto["symbol"]
        assert converted_dto["quantity"] == original_dto["quantity"]
        assert converted_dto["entry_price"] == original_dto["entry_price"]
        assert converted_dto["current_price"] == original_dto["current_price"]
        assert converted_dto["strategy_type"] == original_dto["strategy_type"]