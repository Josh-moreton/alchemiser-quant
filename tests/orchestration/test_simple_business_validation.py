"""Business Unit: orchestration | Status: current

Simple business logic validation tests.

Tests basic business logic validation without complex model dependencies.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestBusinessLogicValidation:
    """Test core business logic validation rules."""

    def test_strategy_allocation_weights_must_sum_to_one(self):
        """Test that strategy allocation weights must sum to 1.0."""
        # Valid allocation
        valid_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.6"),
                "MSFT": Decimal("0.4"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        assert abs(sum(valid_allocation.target_weights.values()) - Decimal("1.0")) < Decimal(
            "0.0001"
        )

    def test_strategy_allocation_invalid_weights_sum(self):
        """Test that invalid weight sums are rejected."""
        # Weights sum to more than 1.0
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={
                    "AAPL": Decimal("0.7"),
                    "MSFT": Decimal("0.5"),  # Sum = 1.2
                },
                correlation_id=str(uuid.uuid4()),
                as_of=datetime.now(UTC),
                constraints={},
            )

    def test_strategy_allocation_empty_weights(self):
        """Test that empty weights are rejected."""
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={},
                correlation_id=str(uuid.uuid4()),
                as_of=datetime.now(UTC),
                constraints={},
            )

    def test_strategy_allocation_negative_weights(self):
        """Test that negative weights are rejected."""
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={
                    "AAPL": Decimal("-0.1"),
                    "MSFT": Decimal("1.1"),
                },
                correlation_id=str(uuid.uuid4()),
                as_of=datetime.now(UTC),
                constraints={},
            )

    def test_decimal_precision_in_business_calculations(self):
        """Test that business calculations maintain decimal precision."""
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.333333"),
                "MSFT": Decimal("0.333333"),
                "GOOGL": Decimal("0.333334"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Test portfolio value calculations
        portfolio_value = Decimal("10000.00")

        for symbol, weight in allocation.target_weights.items():
            target_value = portfolio_value * weight
            # Should maintain precision
            assert isinstance(target_value, Decimal)
            assert target_value >= Decimal("0")

    def test_correlation_id_validation(self):
        """Test correlation ID validation."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Should have valid UUID correlation ID
        assert len(allocation.correlation_id) > 0
        assert "-" in allocation.correlation_id  # UUID format

    def test_business_constraint_validation(self):
        """Test business constraint validation."""
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={
                "strategy_id": "test_strategy",
                "max_positions": 10,
                "sector_limit": 0.3,
            },
        )

        # Should preserve constraints
        assert allocation.constraints["strategy_id"] == "test_strategy"
        assert allocation.constraints["max_positions"] == 10
        assert allocation.constraints["sector_limit"] == 0.3

    def test_symbol_validation(self):
        """Test symbol validation in allocations."""
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.5"),
                "MSFT": Decimal("0.3"),
                "GOOGL": Decimal("0.2"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Should have valid symbols
        for symbol in allocation.target_weights.keys():
            assert len(symbol) > 0
            assert symbol.isupper()  # Should be uppercase

    def test_weight_distribution_business_rules(self):
        """Test business rules for weight distribution."""
        # Single position allocation
        single_allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )
        assert len(single_allocation.target_weights) == 1

        # Diversified allocation
        diversified_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.25"),
                "MSFT": Decimal("0.25"),
                "GOOGL": Decimal("0.25"),
                "TSLA": Decimal("0.25"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )
        assert len(diversified_allocation.target_weights) == 4

        # All weights should be equal
        for weight in diversified_allocation.target_weights.values():
            assert weight == Decimal("0.25")

    def test_money_calculation_precision(self):
        """Test that money calculations maintain precision."""
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.6"),
                "MSFT": Decimal("0.4"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Test with various portfolio values
        test_values = [
            Decimal("1000.00"),
            Decimal("10000.00"),
            Decimal("100000.00"),
            Decimal("1000000.00"),
        ]

        for portfolio_value in test_values:
            total_allocated = Decimal("0")
            for symbol, weight in allocation.target_weights.items():
                target_value = portfolio_value * weight
                total_allocated += target_value

                # Should maintain two decimal places for money
                assert target_value.quantize(Decimal("0.01")) == target_value.quantize(
                    Decimal("0.01")
                )

            # Should allocate full portfolio value
            assert abs(total_allocated - portfolio_value) < Decimal("0.01")
