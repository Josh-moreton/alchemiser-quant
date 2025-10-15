"""Tests for JSON sanitization functions in shared.utils.serialization.

This module tests the new JSON-safe serialization functions designed for
EventBridge publishing and structured logging.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel, Field

from the_alchemiser.shared.schemas.types import (
    DecimalStr,
    MoneyDecimal,
    PriceDecimal,
    UtcDatetime,
    WeightDecimal,
)
from the_alchemiser.shared.utils.serialization import (
    error_to_payload,
    event_to_detail_str,
    json_sanitise,
    safe_json_dumps,
)


# Test fixtures - Pydantic models
class SimplePydanticModel(BaseModel):
    """Simple Pydantic model for testing."""

    name: str
    value: int


class ModelWithDecimal(BaseModel):
    """Model with Decimal field for testing."""

    amount: Decimal
    price: DecimalStr


class ModelWithDatetime(BaseModel):
    """Model with datetime field for testing."""

    timestamp: datetime
    utc_timestamp: UtcDatetime


class NestedModel(BaseModel):
    """Nested model with various types."""

    title: str
    amount: MoneyDecimal
    price: PriceDecimal
    weight: WeightDecimal
    created_at: UtcDatetime
    nested: SimplePydanticModel


# Test fixtures - Dataclasses
@dataclass
class SimpleDataclass:
    """Simple dataclass for testing."""

    name: str
    value: int


@dataclass
class DataclassWithComplexTypes:
    """Dataclass with Decimal and datetime."""

    amount: Decimal
    timestamp: datetime
    nested: SimpleDataclass


@pytest.mark.unit
class TestJsonSanitise:
    """Test json_sanitise function for various input types."""

    def test_decimal_to_string(self) -> None:
        """Test Decimal values are converted to string."""
        value = Decimal("123.456")
        result = json_sanitise(value)
        assert result == "123.456"
        assert isinstance(result, str)

    def test_datetime_to_rfc3339z(self) -> None:
        """Test datetime conversion to RFC3339 with Z suffix."""
        dt = datetime(2025, 10, 15, 8, 13, 16, 741000, tzinfo=UTC)
        result = json_sanitise(dt)
        assert isinstance(result, str)
        assert result.endswith("Z")
        assert "2025-10-15" in result
        assert "08:13:16" in result

    def test_datetime_naive_to_rfc3339z(self) -> None:
        """Test naive datetime is converted to UTC."""
        dt = datetime(2025, 10, 15, 8, 13, 16)
        result = json_sanitise(dt)
        assert isinstance(result, str)
        assert result.endswith("Z")

    def test_datetime_non_utc_converted(self) -> None:
        """Test non-UTC datetime is converted to UTC."""
        # Create a datetime in PST (UTC-8)
        pst = timezone(timedelta(hours=-8))
        dt = datetime(2025, 10, 15, 0, 13, 16, tzinfo=pst)
        result = json_sanitise(dt)
        assert isinstance(result, str)
        assert result.endswith("Z")
        # Should be 8 hours ahead in UTC
        assert "08:13:16" in result

    def test_exception_to_dict(self) -> None:
        """Test Exception is converted to error dict."""
        exc = ValueError("Test error message")
        result = json_sanitise(exc)
        assert isinstance(result, dict)
        assert result["error_type"] == "ValueError"
        assert result["error_message"] == "Test error message"

    def test_custom_exception_to_dict(self) -> None:
        """Test custom exception types are handled."""

        class CustomError(Exception):
            pass

        exc = CustomError("Custom message")
        result = json_sanitise(exc)
        assert isinstance(result, dict)
        assert result["error_type"] == "CustomError"
        assert result["error_message"] == "Custom message"

    def test_pydantic_model_with_mode_json(self) -> None:
        """Test Pydantic model uses mode='json' for serialization."""
        model = ModelWithDecimal(amount=Decimal("99.99"), price=Decimal("123.456"))
        result = json_sanitise(model)
        assert isinstance(result, dict)
        # With mode="json", Pydantic should convert Decimals to strings
        assert result["amount"] == "99.99"
        assert result["price"] == "123.456"

    def test_pydantic_model_with_datetime(self) -> None:
        """Test Pydantic model with datetime fields."""
        dt = datetime(2025, 10, 15, 8, 13, 16, 741000, tzinfo=UTC)
        model = ModelWithDatetime(timestamp=dt, utc_timestamp=dt)
        result = json_sanitise(model)
        assert isinstance(result, dict)
        # Both should be RFC3339Z strings
        assert result["timestamp"].endswith("Z")
        assert result["utc_timestamp"].endswith("Z")

    def test_nested_pydantic_model(self) -> None:
        """Test nested Pydantic models are recursively sanitized."""
        inner = SimplePydanticModel(name="inner", value=10)
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        model = NestedModel(
            title="outer",
            amount=Decimal("99.99"),
            price=Decimal("123.45"),
            weight=Decimal("0.1234"),
            created_at=dt,
            nested=inner,
        )
        result = json_sanitise(model)
        assert isinstance(result, dict)
        assert result["amount"] == "99.99"
        assert result["price"] == "123.45"
        assert result["weight"] == "0.1234"
        assert result["created_at"].endswith("Z")
        assert result["nested"]["name"] == "inner"

    def test_dataclass_with_complex_types(self) -> None:
        """Test dataclass with Decimal and datetime."""
        inner = SimpleDataclass(name="inner", value=10)
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        dc = DataclassWithComplexTypes(amount=Decimal("99.99"), timestamp=dt, nested=inner)
        result = json_sanitise(dc)
        assert isinstance(result, dict)
        assert result["amount"] == "99.99"
        assert result["timestamp"].endswith("Z")
        assert result["nested"]["name"] == "inner"

    def test_dict_with_mixed_types(self) -> None:
        """Test dict with Decimal, datetime, and Exception."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        exc = ValueError("Test")
        data = {
            "price": Decimal("100.50"),
            "timestamp": dt,
            "error": exc,
            "nested": {"amount": Decimal("50.25")},
        }
        result = json_sanitise(data)
        assert isinstance(result, dict)
        assert result["price"] == "100.50"
        assert result["timestamp"].endswith("Z")
        assert result["error"]["error_type"] == "ValueError"
        assert result["nested"]["amount"] == "50.25"

    def test_list_with_mixed_types(self) -> None:
        """Test list with various complex types."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = [Decimal("10.5"), dt, ValueError("error"), {"key": Decimal("20.3")}]
        result = json_sanitise(data)
        assert isinstance(result, list)
        assert result[0] == "10.5"
        assert result[1].endswith("Z")
        assert result[2]["error_type"] == "ValueError"
        assert result[3]["key"] == "20.3"

    def test_dict_keys_converted_to_strings(self) -> None:
        """Test that dict keys are converted to strings."""
        data = {1: "one", 2: "two", "three": 3}
        result = json_sanitise(data)
        assert isinstance(result, dict)
        # All keys should be strings
        assert "1" in result
        assert "2" in result
        assert "three" in result

    def test_deeply_nested_structure(self) -> None:
        """Test deeply nested structure with all complex types."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = {
            "level1": {
                "level2": [
                    {
                        "price": Decimal("100.00"),
                        "timestamp": dt,
                        "error": ValueError("test"),
                        "items": [Decimal("1.5"), dt, ValueError("nested")],
                    }
                ]
            }
        }
        result = json_sanitise(data)
        assert isinstance(result, dict)
        level2 = result["level1"]["level2"]
        first_item = level2[0]
        assert first_item["price"] == "100.00"
        assert first_item["timestamp"].endswith("Z")
        assert first_item["error"]["error_type"] == "ValueError"
        assert first_item["items"][0] == "1.5"
        assert first_item["items"][1].endswith("Z")
        assert first_item["items"][2]["error_type"] == "ValueError"


@pytest.mark.unit
class TestSafeJsonDumps:
    """Test safe_json_dumps function."""

    def test_simple_dict(self) -> None:
        """Test simple dict serialization."""
        data = {"name": "test", "value": 42}
        result = safe_json_dumps(data)
        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data

    def test_dict_with_decimal(self) -> None:
        """Test dict with Decimal is serializable."""
        data = {"price": Decimal("100.50"), "qty": 10}
        result = safe_json_dumps(data)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["price"] == "100.50"
        assert parsed["qty"] == 10

    def test_dict_with_datetime(self) -> None:
        """Test dict with datetime is serializable."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = {"timestamp": dt}
        result = safe_json_dumps(data)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["timestamp"].endswith("Z")

    def test_dict_with_exception(self) -> None:
        """Test dict with Exception is serializable."""
        data = {"error": ValueError("Test error")}
        result = safe_json_dumps(data)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["error"]["error_type"] == "ValueError"

    def test_pydantic_model(self) -> None:
        """Test Pydantic model serialization."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        model = NestedModel(
            title="test",
            amount=Decimal("99.99"),
            price=Decimal("123.45"),
            weight=Decimal("0.1234"),
            created_at=dt,
            nested=SimplePydanticModel(name="inner", value=10),
        )
        result = safe_json_dumps(model)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["title"] == "test"
        assert parsed["amount"] == "99.99"
        assert parsed["created_at"].endswith("Z")

    def test_with_indent(self) -> None:
        """Test that kwargs like indent are passed through."""
        data = {"name": "test", "value": 42}
        result = safe_json_dumps(data, indent=2)
        assert isinstance(result, str)
        assert "\n" in result  # Indented JSON has newlines

    def test_ensure_ascii_false_by_default(self) -> None:
        """Test that ensure_ascii defaults to False."""
        data = {"name": "test", "emoji": "🚀"}
        result = safe_json_dumps(data)
        assert "🚀" in result  # Should not be escaped

    def test_round_trip(self) -> None:
        """Test that safe_json_dumps produces valid JSON."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = {
            "price": Decimal("100.50"),
            "timestamp": dt,
            "error": ValueError("test"),
            "nested": {"amount": Decimal("50.25")},
        }
        result = safe_json_dumps(data)
        parsed = json.loads(result)
        assert parsed["price"] == "100.50"
        assert parsed["timestamp"].endswith("Z")
        assert parsed["error"]["error_type"] == "ValueError"
        assert parsed["nested"]["amount"] == "50.25"


@pytest.mark.unit
class TestEventToDetailStr:
    """Test event_to_detail_str function."""

    def test_simple_model(self) -> None:
        """Test simple Pydantic model conversion."""
        model = SimplePydanticModel(name="test", value=42)
        result = event_to_detail_str(model)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    def test_model_with_complex_types(self) -> None:
        """Test model with Decimal and datetime."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        model = NestedModel(
            title="event",
            amount=Decimal("99.99"),
            price=Decimal("123.45"),
            weight=Decimal("0.1234"),
            created_at=dt,
            nested=SimplePydanticModel(name="inner", value=10),
        )
        result = event_to_detail_str(model)
        assert isinstance(result, str)
        # Must be valid JSON
        parsed = json.loads(result)
        assert parsed["title"] == "event"
        assert parsed["amount"] == "99.99"
        assert parsed["created_at"].endswith("Z")

    def test_dict_input(self) -> None:
        """Test that dict can also be serialized."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = {"timestamp": dt, "amount": Decimal("100.50")}
        result = event_to_detail_str(data)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["timestamp"].endswith("Z")
        assert parsed["amount"] == "100.50"


@pytest.mark.unit
class TestErrorToPayload:
    """Test error_to_payload function."""

    def test_simple_exception(self) -> None:
        """Test simple exception conversion."""
        exc = ValueError("Test error")
        result = error_to_payload(exc)
        assert result == {"error_type": "ValueError", "error_message": "Test error"}

    def test_custom_exception(self) -> None:
        """Test custom exception type."""

        class CustomError(Exception):
            pass

        exc = CustomError("Custom message")
        result = error_to_payload(exc)
        assert result == {"error_type": "CustomError", "error_message": "Custom message"}

    def test_exception_with_args(self) -> None:
        """Test exception with multiple args."""
        exc = RuntimeError("Error", "with", "args")
        result = error_to_payload(exc)
        assert result["error_type"] == "RuntimeError"
        assert "Error" in result["error_message"]

    def test_payload_is_json_serializable(self) -> None:
        """Test that error payload is JSON-serializable."""
        exc = ValueError("Test error")
        payload = error_to_payload(exc)
        # Should be able to serialize without issues
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        assert parsed == payload


@pytest.mark.unit
class TestRoundTrip:
    """Test that sanitized data can round-trip through JSON."""

    def test_decimal_round_trip(self) -> None:
        """Test Decimal -> JSON -> back preserves value."""
        data = {"amount": Decimal("123.456789")}
        json_str = safe_json_dumps(data)
        parsed = json.loads(json_str)
        restored = Decimal(parsed["amount"])
        assert restored == Decimal("123.456789")

    def test_datetime_round_trip(self) -> None:
        """Test datetime -> JSON -> back preserves value."""
        dt = datetime(2025, 10, 15, 8, 13, 16, 741000, tzinfo=UTC)
        data = {"timestamp": dt}
        json_str = safe_json_dumps(data)
        parsed = json.loads(json_str)
        # Parse back to datetime
        restored = datetime.fromisoformat(parsed["timestamp"].replace("Z", "+00:00"))
        assert restored == dt

    def test_complex_structure_round_trip(self) -> None:
        """Test complex nested structure round-trips."""
        dt = datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)
        data = {
            "prices": [Decimal("100.00"), Decimal("200.00")],
            "timestamps": [dt, dt + timedelta(hours=1)],
            "nested": {"amount": Decimal("99.99"), "created": dt},
        }
        json_str = safe_json_dumps(data)
        parsed = json.loads(json_str)
        # Verify structure is preserved
        assert parsed["prices"] == ["100.00", "200.00"]
        assert len(parsed["timestamps"]) == 2
        assert parsed["nested"]["amount"] == "99.99"


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_values_preserved(self) -> None:
        """Test None values are preserved."""
        data = {"key": None, "list": [1, None, 3]}
        result = json_sanitise(data)
        assert result["key"] is None
        assert result["list"][1] is None

    def test_empty_structures(self) -> None:
        """Test empty dict, list, etc."""
        assert json_sanitise({}) == {}
        assert json_sanitise([]) == []
        assert json_sanitise("") == ""

    def test_special_decimal_values(self) -> None:
        """Test special Decimal values."""
        data = {
            "zero": Decimal("0"),
            "negative": Decimal("-123.456"),
            "scientific": Decimal("1.23E+5"),
        }
        result = safe_json_dumps(data)
        parsed = json.loads(result)
        assert parsed["zero"] == "0"
        assert parsed["negative"] == "-123.456"
        assert "123000" in parsed["scientific"] or "1.23E+5" in parsed["scientific"]

    def test_datetime_microseconds(self) -> None:
        """Test datetime with microseconds."""
        dt = datetime(2025, 10, 15, 8, 13, 16, 741234, tzinfo=UTC)
        result = json_sanitise(dt)
        assert "741234" in result or "741" in result  # Microseconds present

    def test_string_not_treated_as_sequence(self) -> None:
        """Test strings are not converted to list of chars."""
        data = {"text": "hello"}
        result = json_sanitise(data)
        assert result["text"] == "hello"

    def test_bytes_preserved(self) -> None:
        """Test bytes are preserved."""
        data = b"test bytes"
        result = json_sanitise(data)
        assert result == b"test bytes"
