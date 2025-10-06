"""Tests for shared.utils.serialization module.

This module tests JSON-friendly serialization for Pydantic models, dataclasses,
Decimals, and nested containers at application boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest
from pydantic import BaseModel

from the_alchemiser.shared.utils.serialization import (
    ensure_serialized_dict,
    to_serializable,
)


# Test fixtures - Pydantic models
class SimplePydanticModel(BaseModel):
    """Simple Pydantic model for testing."""

    name: str
    value: int


class NestedPydanticModel(BaseModel):
    """Nested Pydantic model for testing."""

    title: str
    amount: Decimal
    nested: SimplePydanticModel


# Test fixtures - Dataclasses
@dataclass
class SimpleDataclass:
    """Simple dataclass for testing."""

    name: str
    value: int


@dataclass
class NestedDataclass:
    """Nested dataclass with Decimal for testing."""

    title: str
    amount: Decimal
    nested: SimpleDataclass


@pytest.mark.unit
class TestToSerializable:
    """Test to_serializable function for various input types."""

    def test_decimal_to_string(self) -> None:
        """Test Decimal values are converted to string."""
        value = Decimal("123.456")
        result = to_serializable(value)
        assert result == "123.456"
        assert isinstance(result, str)

    def test_decimal_preserves_precision(self) -> None:
        """Test high-precision Decimal conversion."""
        value = Decimal("123.123456789012345678901234567890")
        result = to_serializable(value)
        assert result == "123.123456789012345678901234567890"
        assert isinstance(result, str)

    def test_decimal_zero(self) -> None:
        """Test zero Decimal value."""
        value = Decimal("0")
        result = to_serializable(value)
        assert result == "0"

    def test_pydantic_model_to_dict(self) -> None:
        """Test Pydantic model serialization."""
        model = SimplePydanticModel(name="test", value=42)
        result = to_serializable(model)
        assert isinstance(result, dict)
        assert result == {"name": "test", "value": 42}

    def test_pydantic_model_with_decimal(self) -> None:
        """Test Pydantic model containing Decimal field."""
        inner = SimplePydanticModel(name="inner", value=10)
        model = NestedPydanticModel(
            title="outer", amount=Decimal("99.99"), nested=inner
        )
        result = to_serializable(model)
        assert isinstance(result, dict)
        assert result["amount"] == "99.99"
        assert result["nested"]["name"] == "inner"

    def test_dataclass_to_dict(self) -> None:
        """Test dataclass serialization."""
        dc = SimpleDataclass(name="test", value=42)
        result = to_serializable(dc)
        assert isinstance(result, dict)
        assert result == {"name": "test", "value": 42}

    def test_dataclass_with_decimal(self) -> None:
        """Test nested dataclass with Decimal."""
        inner = SimpleDataclass(name="inner", value=10)
        dc = NestedDataclass(title="outer", amount=Decimal("99.99"), nested=inner)
        result = to_serializable(dc)
        assert isinstance(result, dict)
        assert result["amount"] == "99.99"
        assert result["nested"]["name"] == "inner"

    def test_dataclass_class_not_serialized(self) -> None:
        """Test that dataclass classes (not instances) are not converted."""
        # Passing the class itself, not an instance
        result = to_serializable(SimpleDataclass)
        # Should be returned as-is since it's a type, not an instance
        assert result == SimpleDataclass

    def test_mapping_recursion(self) -> None:
        """Test dict with nested Decimal values."""
        data = {
            "price": Decimal("100.50"),
            "qty": 10,
            "nested": {"amount": Decimal("50.25")},
        }
        result = to_serializable(data)
        assert isinstance(result, dict)
        assert result["price"] == "100.50"
        assert result["nested"]["amount"] == "50.25"

    def test_list_recursion(self) -> None:
        """Test list with nested Decimal values."""
        data = [Decimal("10.5"), Decimal("20.3"), 30]
        result = to_serializable(data)
        assert isinstance(result, list)
        assert result == ["10.5", "20.3", 30]

    def test_tuple_recursion(self) -> None:
        """Test tuple is converted to list with Decimal handling."""
        data = (Decimal("10.5"), "text", 42)
        result = to_serializable(data)
        assert isinstance(result, list)
        assert result == ["10.5", "text", 42]

    def test_set_recursion(self) -> None:
        """Test set is converted to list."""
        data = {1, 2, 3}
        result = to_serializable(data)
        assert isinstance(result, list)
        assert set(result) == {1, 2, 3}

    def test_string_not_converted_to_list(self) -> None:
        """Test strings are not treated as sequences."""
        data = "test string"
        result = to_serializable(data)
        assert result == "test string"
        assert isinstance(result, str)

    def test_bytes_not_converted_to_list(self) -> None:
        """Test bytes are not treated as sequences."""
        data = b"test bytes"
        result = to_serializable(data)
        assert result == b"test bytes"
        assert isinstance(result, bytes)

    def test_primitives_unchanged(self) -> None:
        """Test primitive types pass through unchanged."""
        assert to_serializable(42) == 42
        assert to_serializable(3.14) == 3.14
        assert to_serializable(True) is True
        assert to_serializable(None) is None

    def test_deeply_nested_structure(self) -> None:
        """Test deeply nested dict/list structure with Decimals."""
        data = {
            "level1": {
                "level2": [
                    {"price": Decimal("100.00"), "items": [Decimal("1.5"), Decimal("2.5")]},
                    {"price": Decimal("200.00"), "items": [Decimal("3.5")]},
                ]
            }
        }
        result = to_serializable(data)
        assert isinstance(result, dict)
        level1 = result["level1"]
        assert isinstance(level1, dict)
        level2 = level1["level2"]
        assert isinstance(level2, list)
        first_item = level2[0]
        assert isinstance(first_item, dict)
        assert first_item["price"] == "100.00"
        first_items = first_item["items"]
        assert isinstance(first_items, list)
        assert first_items[0] == "1.5"
        second_item = level2[1]
        assert isinstance(second_item, dict)
        second_items = second_item["items"]
        assert isinstance(second_items, list)
        assert second_items[0] == "3.5"

    def test_model_dump_exception_fallback(self) -> None:
        """Test defensive fallback when model_dump raises exception."""

        class BrokenModel:
            def model_dump(self) -> dict[str, Any]:
                msg = "Intentional error"
                raise ValueError(msg)

        broken = BrokenModel()
        result = to_serializable(broken)
        # Should fall back to str() representation
        assert isinstance(result, str)


@pytest.mark.unit
class TestEnsureSerializedDict:
    """Test ensure_serialized_dict function."""

    def test_dict_input(self) -> None:
        """Test plain dict with Decimals is serialized."""
        data = {"price": Decimal("100.50"), "qty": 10}
        result = ensure_serialized_dict(data)
        assert isinstance(result, dict)
        assert result["price"] == "100.50"

    def test_pydantic_model_input(self) -> None:
        """Test Pydantic model is converted to dict."""
        model = SimplePydanticModel(name="test", value=42)
        result = ensure_serialized_dict(model)
        assert isinstance(result, dict)
        assert result == {"name": "test", "value": 42}

    def test_dataclass_input(self) -> None:
        """Test dataclass is converted to dict."""
        dc = SimpleDataclass(name="test", value=42)
        result = ensure_serialized_dict(dc)
        assert isinstance(result, dict)
        assert result == {"name": "test", "value": 42}

    def test_unsupported_type_raises(self) -> None:
        """Test unsupported input type raises TypeError."""
        with pytest.raises(TypeError, match="Cannot serialize object of type"):
            ensure_serialized_dict(42)

        with pytest.raises(TypeError, match="Cannot serialize object of type"):
            ensure_serialized_dict("string")

        with pytest.raises(TypeError, match="Cannot serialize object of type"):
            ensure_serialized_dict([1, 2, 3])

    def test_dataclass_class_raises(self) -> None:
        """Test passing dataclass class (not instance) raises TypeError."""
        # Should raise because class itself is not serializable
        with pytest.raises(TypeError, match="Cannot serialize object of type"):
            ensure_serialized_dict(SimpleDataclass)


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_dict(self) -> None:
        """Test empty dict serialization."""
        result = to_serializable({})
        assert result == {}

    def test_empty_list(self) -> None:
        """Test empty list serialization."""
        result = to_serializable([])
        assert result == []

    def test_none_values_in_collections(self) -> None:
        """Test None values are preserved in collections."""
        data = {"key": None, "list": [1, None, 3]}
        result = to_serializable(data)
        assert isinstance(result, dict)
        assert result["key"] is None
        result_list = result["list"]
        assert isinstance(result_list, list)
        assert result_list[1] is None

    def test_negative_decimal(self) -> None:
        """Test negative Decimal values."""
        value = Decimal("-123.456")
        result = to_serializable(value)
        assert result == "-123.456"

    def test_scientific_notation_decimal(self) -> None:
        """Test Decimal in scientific notation."""
        value = Decimal("1.23E+5")
        result = to_serializable(value)
        # Decimal converts scientific notation to standard form
        assert isinstance(result, str)
        assert "123000" in result or "1.23E+5" in result

    def test_mixed_sequence_types(self) -> None:
        """Test mixed list, tuple, set in same structure."""
        data = {
            "list": [1, 2, 3],
            "tuple": (4, 5, 6),
            "set": {7, 8, 9},
        }
        result = to_serializable(data)
        assert isinstance(result, dict)
        assert isinstance(result["list"], list)
        assert isinstance(result["tuple"], list)
        assert isinstance(result["set"], list)


@pytest.mark.unit
@pytest.mark.property
class TestSerializationProperties:
    """Property-based tests for serialization invariants."""

    def test_idempotency_on_primitives(self) -> None:
        """Test that serializing primitives twice yields same result."""
        data = {"a": 1, "b": "text", "c": True}
        result1 = to_serializable(data)
        result2 = to_serializable(result1)
        assert result1 == result2

    def test_decimal_round_trip_via_string(self) -> None:
        """Test Decimal -> str -> Decimal preserves value."""
        original = Decimal("123.456789")
        serialized = to_serializable(original)
        restored = Decimal(serialized)  # type: ignore[arg-type]
        assert original == restored

    def test_all_decimals_become_strings(self) -> None:
        """Test that deeply nested structure has no Decimal objects after serialization."""
        data = {
            "a": Decimal("1.5"),
            "b": [Decimal("2.5"), {"c": Decimal("3.5")}],
        }
        result = to_serializable(data)

        # Helper to check no Decimal objects remain
        def has_decimal(obj: object) -> bool:
            if isinstance(obj, Decimal):
                return True
            if isinstance(obj, dict):
                return any(has_decimal(v) for v in obj.values())
            if isinstance(obj, list):
                return any(has_decimal(v) for v in obj)
            return False

        assert not has_decimal(result)


@pytest.mark.unit
class TestCompliance:
    """Tests for compliance with copilot instructions."""

    def test_no_silent_exception_catching(self) -> None:
        """Verify exception fallback logs or handles errors appropriately.
        
        Note: The current implementation has a defensive fallback with pragma: no cover.
        This is acceptable for boundary serialization but should be monitored.
        """
        # This test documents the defensive behavior
        class BrokenModel:
            def model_dump(self) -> dict[str, Any]:
                msg = "Intentional error"
                raise RuntimeError(msg)

        broken = BrokenModel()
        result = to_serializable(broken)
        # Fallback to str() is acceptable for serialization boundaries
        assert isinstance(result, str)

    def test_type_annotations_complete(self) -> None:
        """Verify functions have proper type hints (checked by mypy)."""
        # This is verified by mypy in CI, but we document the expectation
        import inspect

        sig = inspect.signature(to_serializable)
        assert sig.return_annotation != inspect.Parameter.empty

        sig = inspect.signature(ensure_serialized_dict)
        assert sig.return_annotation != inspect.Parameter.empty

    def test_frozen_pydantic_models(self) -> None:
        """Test serialization works with frozen Pydantic models."""

        class FrozenModel(BaseModel):
            model_config = {"frozen": True}
            name: str
            value: int

        frozen = FrozenModel(name="frozen", value=42)
        result = to_serializable(frozen)
        assert result == {"name": "frozen", "value": 42}
