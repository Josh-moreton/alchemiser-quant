#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for reusable EventBridge type annotations.

This test module validates the symmetric serialization/deserialization
of Decimal and datetime fields through EventBridge JSON.
"""

# ruff: noqa: S101  # Allow asserts in tests

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from the_alchemiser.shared.schemas.types import (
    DecimalStr,
    MoneyDecimal,
    WeightDecimal,
    PriceDecimal,
    UtcDatetime,
)


class TestDecimalStr:
    """Test DecimalStr type annotation."""

    def test_string_deserialization(self):
        """Test deserialization from string."""
        
        class TestModel(BaseModel):
            value: DecimalStr
        
        model = TestModel.model_validate({"value": "123.456"})
        assert model.value == Decimal("123.456")
        assert isinstance(model.value, Decimal)

    def test_numeric_deserialization(self):
        """Test deserialization from numeric types."""
        
        class TestModel(BaseModel):
            value: DecimalStr
        
        # From int
        model = TestModel.model_validate({"value": 123})
        assert model.value == Decimal("123")
        
        # From float
        model = TestModel.model_validate({"value": 123.456})
        assert model.value == Decimal("123.456")

    def test_decimal_passthrough(self):
        """Test that Decimal values pass through unchanged."""
        
        class TestModel(BaseModel):
            value: DecimalStr
        
        model = TestModel(value=Decimal("123.456"))
        assert model.value == Decimal("123.456")

    def test_serialization_to_string(self):
        """Test serialization to string for JSON."""
        
        class TestModel(BaseModel):
            value: DecimalStr
        
        model = TestModel(value=Decimal("123.456"))
        dumped = model.model_dump()
        
        assert dumped["value"] == "123.456"
        assert isinstance(dumped["value"], str)

    def test_round_trip_serialization(self):
        """Test round-trip: Decimal → str → Decimal."""
        
        class TestModel(BaseModel):
            value: DecimalStr
        
        original = TestModel(value=Decimal("123.456789"))
        dumped = original.model_dump()
        restored = TestModel.model_validate(dumped)
        
        assert restored.value == original.value
        assert isinstance(dumped["value"], str)


class TestMoneyDecimal:
    """Test MoneyDecimal type annotation (2 decimal places)."""

    def test_quantization_to_2_decimals(self):
        """Test quantization to 2 decimal places."""
        
        class TestModel(BaseModel):
            amount: MoneyDecimal
        
        # Test rounding
        model = TestModel.model_validate({"amount": "123.456"})
        assert model.amount == Decimal("123.46")  # Rounds up
        
        model = TestModel.model_validate({"amount": "123.454"})
        assert model.amount == Decimal("123.45")  # Rounds down

    def test_serialization_preserves_precision(self):
        """Test serialization maintains 2 decimal precision."""
        
        class TestModel(BaseModel):
            amount: MoneyDecimal
        
        model = TestModel(amount=Decimal("123.456"))
        dumped = model.model_dump()
        
        # Should be quantized to 2 decimals
        assert dumped["amount"] == "123.46"

    def test_round_trip_with_quantization(self):
        """Test round-trip maintains quantization."""
        
        class TestModel(BaseModel):
            amount: MoneyDecimal
        
        original = TestModel.model_validate({"amount": "123.456789"})
        assert original.amount == Decimal("123.46")
        
        dumped = original.model_dump()
        restored = TestModel.model_validate(dumped)
        
        assert restored.amount == Decimal("123.46")


class TestWeightDecimal:
    """Test WeightDecimal type annotation (4 decimal places)."""

    def test_quantization_to_4_decimals(self):
        """Test quantization to 4 decimal places."""
        
        class TestModel(BaseModel):
            weight: WeightDecimal
        
        # Test rounding
        model = TestModel.model_validate({"weight": "0.123456"})
        assert model.weight == Decimal("0.1235")  # Rounds up
        
        model = TestModel.model_validate({"weight": "0.123454"})
        assert model.weight == Decimal("0.1235")  # Rounds up (ROUND_HALF_UP)

    def test_round_trip_with_quantization(self):
        """Test round-trip maintains quantization."""
        
        class TestModel(BaseModel):
            weight: WeightDecimal
        
        original = TestModel.model_validate({"weight": "0.123456789"})
        assert original.weight == Decimal("0.1235")
        
        dumped = original.model_dump()
        restored = TestModel.model_validate(dumped)
        
        assert restored.weight == Decimal("0.1235")


class TestPriceDecimal:
    """Test PriceDecimal type annotation (2 decimal places)."""

    def test_quantization_to_2_decimals(self):
        """Test quantization to 2 decimal places."""
        
        class TestModel(BaseModel):
            price: PriceDecimal
        
        model = TestModel.model_validate({"price": "150.505"})
        assert model.price == Decimal("150.51")  # Rounds up


class TestUtcDatetime:
    """Test UtcDatetime type annotation."""

    def test_string_deserialization_with_z_suffix(self):
        """Test deserialization from ISO 8601 string with Z suffix."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        model = TestModel.model_validate({"timestamp": "2025-01-06T12:30:45Z"})
        
        assert model.timestamp.year == 2025
        assert model.timestamp.month == 1
        assert model.timestamp.day == 6
        assert model.timestamp.tzinfo == timezone.utc

    def test_string_deserialization_with_offset(self):
        """Test deserialization from ISO 8601 string with +00:00 offset."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        model = TestModel.model_validate({"timestamp": "2025-01-06T12:30:45+00:00"})
        
        assert model.timestamp.tzinfo == timezone.utc

    def test_naive_datetime_becomes_utc(self):
        """Test that naive datetime gets UTC timezone."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        naive_dt = datetime(2025, 1, 6, 12, 30, 45)
        model = TestModel(timestamp=naive_dt)
        
        assert model.timestamp.tzinfo == timezone.utc

    def test_non_utc_timezone_converted_to_utc(self):
        """Test that non-UTC timezones are converted to UTC."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        # Create datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        est_dt = datetime(2025, 1, 6, 12, 30, 45, tzinfo=est)
        
        model = TestModel(timestamp=est_dt)
        
        # Should be converted to UTC
        assert model.timestamp.tzinfo == timezone.utc
        assert model.timestamp.hour == 17  # 12 + 5

    def test_serialization_to_rfc3339_with_z(self):
        """Test serialization to RFC3339 string with Z suffix."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        model = TestModel(timestamp=datetime(2025, 1, 6, 12, 30, 45, tzinfo=timezone.utc))
        dumped = model.model_dump()
        
        assert dumped["timestamp"] == "2025-01-06T12:30:45Z"
        assert isinstance(dumped["timestamp"], str)

    def test_round_trip_serialization(self):
        """Test round-trip: datetime → str → datetime."""
        
        class TestModel(BaseModel):
            timestamp: UtcDatetime
        
        original_dt = datetime(2025, 1, 6, 12, 30, 45, 123456, tzinfo=timezone.utc)
        original = TestModel(timestamp=original_dt)
        
        dumped = original.model_dump()
        restored = TestModel.model_validate(dumped)
        
        # Should match (may lose microsecond precision depending on serialization)
        assert restored.timestamp.year == original.timestamp.year
        assert restored.timestamp.month == original.timestamp.month
        assert restored.timestamp.day == original.timestamp.day
        assert restored.timestamp.hour == original.timestamp.hour
        assert restored.timestamp.tzinfo == timezone.utc


class TestComplexModel:
    """Test complex model with multiple type annotations."""

    def test_eventbridge_round_trip(self):
        """Test full EventBridge-style round-trip."""
        
        class TradeModel(BaseModel):
            symbol: str
            price: PriceDecimal
            quantity: Decimal
            weight: WeightDecimal
            total_value: MoneyDecimal
            executed_at: UtcDatetime
        
        # Create model
        original = TradeModel(
            symbol="AAPL",
            price=Decimal("150.505"),  # Will be quantized to 150.51
            quantity=Decimal("10"),
            weight=Decimal("0.123456"),  # Will be quantized to 0.1235
            total_value=Decimal("1505.05"),
            executed_at=datetime(2025, 1, 6, 12, 30, 45, tzinfo=timezone.utc),
        )
        
        # Serialize (simulates EventBridge)
        dumped = original.model_dump()
        
        # Verify serialization
        assert dumped["price"] == "150.51"
        assert dumped["weight"] == "0.1235"
        assert dumped["total_value"] == "1505.05"
        assert dumped["executed_at"] == "2025-01-06T12:30:45Z"
        
        # Deserialize (simulates Lambda receiving event)
        restored = TradeModel.model_validate(dumped)
        
        # Verify values match
        assert restored.symbol == original.symbol
        assert restored.price == Decimal("150.51")
        assert restored.quantity == original.quantity
        assert restored.weight == Decimal("0.1235")
        assert restored.total_value == original.total_value
        assert restored.executed_at == original.executed_at
