"""Tests for Identifier value object.

Business Unit: shared | Status: current

Comprehensive tests for the typed identifier base class including:
- UUID generation and uniqueness
- String parsing and validation
- Immutability guarantees
- Type safety with generics
- Error handling for invalid inputs
"""

from __future__ import annotations

from uuid import UUID

import pytest

from the_alchemiser.shared.value_objects.identifier import Identifier


class UserIdentifier(Identifier[None]):
    """Test identifier for User entities."""


class OrderIdentifier(Identifier[None]):
    """Test identifier for Order entities."""


class TestIdentifierGeneration:
    """Test identifier generation methods."""

    def test_generate_creates_valid_uuid(self) -> None:
        """Test that generate() creates a valid UUID identifier."""
        identifier = UserIdentifier.generate()
        
        assert isinstance(identifier, UserIdentifier)
        assert isinstance(identifier.value, UUID)
        assert str(identifier.value)  # Should be valid UUID string

    def test_generate_creates_unique_identifiers(self) -> None:
        """Test that generate() creates unique identifiers on each call."""
        id1 = UserIdentifier.generate()
        id2 = UserIdentifier.generate()
        id3 = UserIdentifier.generate()
        
        assert id1.value != id2.value
        assert id2.value != id3.value
        assert id1.value != id3.value

    def test_generate_multiple_types_are_independent(self) -> None:
        """Test that different identifier types generate independently."""
        user_id = UserIdentifier.generate()
        order_id = OrderIdentifier.generate()
        
        assert isinstance(user_id, UserIdentifier)
        assert isinstance(order_id, OrderIdentifier)
        assert user_id.value != order_id.value


class TestIdentifierFromString:
    """Test identifier creation from string UUIDs."""

    def test_from_string_creates_valid_identifier(self) -> None:
        """Test from_string() with valid UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        identifier = UserIdentifier.from_string(uuid_str)
        
        assert isinstance(identifier, UserIdentifier)
        assert isinstance(identifier.value, UUID)
        assert str(identifier.value) == uuid_str

    def test_from_string_accepts_various_uuid_formats(self) -> None:
        """Test from_string() accepts different UUID string formats."""
        # Lowercase
        id1 = UserIdentifier.from_string("550e8400-e29b-41d4-a716-446655440000")
        assert str(id1.value) == "550e8400-e29b-41d4-a716-446655440000"
        
        # Uppercase
        id2 = UserIdentifier.from_string("550E8400-E29B-41D4-A716-446655440000")
        assert str(id2.value) == "550e8400-e29b-41d4-a716-446655440000"

    def test_from_string_rejects_invalid_uuid(self) -> None:
        """Test from_string() raises ValueError for invalid UUID."""
        with pytest.raises(ValueError, match="badly formed hexadecimal UUID string"):
            UserIdentifier.from_string("not-a-uuid")

    def test_from_string_rejects_empty_string(self) -> None:
        """Test from_string() raises ValueError for empty string."""
        with pytest.raises(ValueError):
            UserIdentifier.from_string("")

    def test_from_string_rejects_partial_uuid(self) -> None:
        """Test from_string() raises ValueError for partial UUID."""
        with pytest.raises(ValueError):
            UserIdentifier.from_string("550e8400-e29b")

    def test_from_string_preserves_uuid_version(self) -> None:
        """Test from_string() preserves UUID version information."""
        # UUID v4
        uuid_v4 = "550e8400-e29b-41d4-a716-446655440000"
        id_v4 = UserIdentifier.from_string(uuid_v4)
        assert id_v4.value.version == 4


class TestIdentifierImmutability:
    """Test identifier immutability guarantees."""

    def test_identifier_is_frozen(self) -> None:
        """Test that identifier instances are immutable (frozen)."""
        identifier = UserIdentifier.generate()
        
        with pytest.raises(AttributeError):
            identifier.value = UUID("550e8400-e29b-41d4-a716-446655440000")  # type: ignore[misc]

    def test_identifier_value_cannot_be_deleted(self) -> None:
        """Test that identifier value cannot be deleted."""
        identifier = UserIdentifier.generate()
        
        with pytest.raises(AttributeError):
            del identifier.value


class TestIdentifierEquality:
    """Test identifier equality and hashing."""

    def test_identifiers_with_same_uuid_are_equal(self) -> None:
        """Test that identifiers with same UUID value are equal."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        id1 = UserIdentifier.from_string(uuid_str)
        id2 = UserIdentifier.from_string(uuid_str)
        
        assert id1 == id2
        assert id1.value == id2.value

    def test_identifiers_with_different_uuids_are_not_equal(self) -> None:
        """Test that identifiers with different UUIDs are not equal."""
        id1 = UserIdentifier.generate()
        id2 = UserIdentifier.generate()
        
        assert id1 != id2
        assert id1.value != id2.value

    def test_identifier_is_hashable(self) -> None:
        """Test that identifiers can be used as dictionary keys."""
        id1 = UserIdentifier.generate()
        id2 = UserIdentifier.generate()
        
        # Should be usable in dict/set
        id_map = {id1: "first", id2: "second"}
        assert id_map[id1] == "first"
        assert id_map[id2] == "second"
        
        id_set = {id1, id2}
        assert len(id_set) == 2


class TestIdentifierTypeSafety:
    """Test type safety with generic identifiers."""

    def test_different_identifier_types_are_distinct(self) -> None:
        """Test that different identifier types are distinct at runtime."""
        user_id = UserIdentifier.generate()
        order_id = OrderIdentifier.generate()
        
        # Types are different
        assert isinstance(user_id, UserIdentifier)
        assert isinstance(order_id, OrderIdentifier)
        assert not isinstance(user_id, OrderIdentifier)
        assert not isinstance(order_id, UserIdentifier)


class TestIdentifierEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_identifier_with_nil_uuid(self) -> None:
        """Test identifier with nil UUID (all zeros)."""
        nil_uuid = "00000000-0000-0000-0000-000000000000"
        identifier = UserIdentifier.from_string(nil_uuid)
        
        assert str(identifier.value) == nil_uuid
        assert identifier.value.int == 0

    def test_identifier_with_max_uuid(self) -> None:
        """Test identifier with maximum UUID value."""
        max_uuid = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        identifier = UserIdentifier.from_string(max_uuid)
        
        assert str(identifier.value) == max_uuid

    def test_identifier_roundtrip_conversion(self) -> None:
        """Test UUID string -> identifier -> UUID string roundtrip."""
        original = "550e8400-e29b-41d4-a716-446655440000"
        identifier = UserIdentifier.from_string(original)
        result = str(identifier.value)
        
        assert result == original


class TestIdentifierStringRepresentation:
    """Test string representation of identifiers."""

    def test_identifier_value_converts_to_string(self) -> None:
        """Test that identifier.value can be converted to string."""
        identifier = UserIdentifier.generate()
        uuid_str = str(identifier.value)
        
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36  # Standard UUID string length
        assert uuid_str.count("-") == 4  # UUID has 4 hyphens

    def test_identifier_str_returns_uuid_string(self) -> None:
        """Test that str(identifier) returns the UUID string directly."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        identifier = UserIdentifier.from_string(uuid_str)
        
        # str() should return the UUID string directly
        assert str(identifier) == uuid_str
        assert isinstance(str(identifier), str)

    def test_identifier_str_is_consistent(self) -> None:
        """Test that str(identifier) is consistent across calls."""
        identifier = UserIdentifier.generate()
        str1 = str(identifier)
        str2 = str(identifier)
        
        assert str1 == str2
