"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for Identifier value object.

Tests Identifier value object operations including UUID generation, parsing,
validation, and immutability per project guardrails.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.value_objects.identifier import Identifier


class TestIdentifierConstruction:
    """Test Identifier value object construction and validation."""

    @pytest.mark.unit
    def test_identifier_creation_with_uuid(self):
        """Test creating identifier with a UUID."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        identifier = Identifier[str](value=test_uuid)
        assert identifier.value == test_uuid
        assert isinstance(identifier.value, UUID)

    @pytest.mark.unit
    def test_identifier_generation(self):
        """Test generating a new identifier."""
        identifier = Identifier[str].generate()
        assert isinstance(identifier.value, UUID)
        assert identifier.value is not None

    @pytest.mark.unit
    def test_identifier_generation_unique(self):
        """Test that generated identifiers are unique."""
        id1 = Identifier[str].generate()
        id2 = Identifier[str].generate()
        assert id1.value != id2.value

    @pytest.mark.unit
    def test_identifier_from_string_valid(self):
        """Test creating identifier from valid UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        identifier = Identifier[str].from_string(uuid_str)
        assert identifier.value == UUID(uuid_str)
        assert isinstance(identifier.value, UUID)

    @pytest.mark.unit
    def test_identifier_from_string_uppercase(self):
        """Test creating identifier from uppercase UUID string."""
        uuid_str = "550E8400-E29B-41D4-A716-446655440000"
        identifier = Identifier[str].from_string(uuid_str)
        assert identifier.value == UUID(uuid_str)

    @pytest.mark.unit
    def test_identifier_from_string_no_hyphens(self):
        """Test creating identifier from UUID string without hyphens."""
        uuid_str = "550e8400e29b41d4a716446655440000"
        identifier = Identifier[str].from_string(uuid_str)
        assert isinstance(identifier.value, UUID)

    @pytest.mark.unit
    def test_identifier_from_string_invalid_raises(self):
        """Test that invalid UUID string raises ValueError."""
        with pytest.raises(ValueError):
            Identifier[str].from_string("not-a-uuid")

    @pytest.mark.unit
    def test_identifier_from_string_empty_raises(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            Identifier[str].from_string("")

    @pytest.mark.unit
    def test_identifier_from_string_too_short_raises(self):
        """Test that too short string raises ValueError."""
        with pytest.raises(ValueError):
            Identifier[str].from_string("550e8400")

    @pytest.mark.unit
    def test_identifier_from_string_too_long_raises(self):
        """Test that too long string raises ValueError."""
        with pytest.raises(ValueError):
            Identifier[str].from_string("550e8400-e29b-41d4-a716-446655440000-extra")

    @pytest.mark.unit
    def test_identifier_from_string_special_chars_raises(self):
        """Test that UUID string with special characters raises ValueError."""
        with pytest.raises(ValueError):
            Identifier[str].from_string("550e8400-e29b-41d4-a716-44665544000@")

    @pytest.mark.unit
    def test_identifier_is_frozen(self):
        """Test that Identifier is immutable (frozen dataclass)."""
        identifier = Identifier[str].generate()
        with pytest.raises(AttributeError):
            identifier.value = UUID("550e8400-e29b-41d4-a716-446655440000")  # type: ignore


class TestIdentifierEquality:
    """Test Identifier equality and comparison."""

    @pytest.mark.unit
    def test_identifier_equality_same_uuid(self):
        """Test that identifiers with same UUID are equal."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        id1 = Identifier[str](value=test_uuid)
        id2 = Identifier[str](value=test_uuid)
        assert id1 == id2
        assert hash(id1) == hash(id2)

    @pytest.mark.unit
    def test_identifier_equality_from_string(self):
        """Test that identifiers from same UUID string are equal."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        id1 = Identifier[str].from_string(uuid_str)
        id2 = Identifier[str].from_string(uuid_str)
        assert id1 == id2

    @pytest.mark.unit
    def test_identifier_inequality_different_uuid(self):
        """Test that identifiers with different UUIDs are not equal."""
        id1 = Identifier[str].generate()
        id2 = Identifier[str].generate()
        assert id1 != id2

    @pytest.mark.unit
    def test_identifier_equality_mixed_construction(self):
        """Test equality between identifiers created differently but same value."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        id1 = Identifier[str](value=test_uuid)
        id2 = Identifier[str].from_string("550e8400-e29b-41d4-a716-446655440000")
        assert id1 == id2


class TestIdentifierRepresentation:
    """Test Identifier string representation."""

    @pytest.mark.unit
    def test_identifier_repr(self):
        """Test __repr__ method for debugging."""
        test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        identifier = Identifier[str](value=test_uuid)
        repr_str = repr(identifier)
        assert "Identifier" in repr_str
        assert "550e8400-e29b-41d4-a716-446655440000" in repr_str


class TestIdentifierTypeParameter:
    """Test Identifier type parameter usage."""

    @pytest.mark.unit
    def test_identifier_different_type_parameters(self):
        """Test that identifiers can be typed with different parameters."""
        # Type parameters are contravariant, so this tests the generic nature
        id_str = Identifier[str].generate()
        id_int = Identifier[int].generate()
        id_object = Identifier[object].generate()

        # All should be valid Identifier instances
        assert isinstance(id_str, Identifier)
        assert isinstance(id_int, Identifier)
        assert isinstance(id_object, Identifier)

    @pytest.mark.unit
    def test_identifier_type_safety_at_runtime(self):
        """Test that different typed identifiers are structurally the same at runtime."""
        uuid_val = UUID("550e8400-e29b-41d4-a716-446655440000")
        id_str = Identifier[str](value=uuid_val)
        id_int = Identifier[int](value=uuid_val)

        # At runtime, both have the same value
        assert id_str.value == id_int.value


# Property-based tests using Hypothesis
class TestIdentifierProperties:
    """Property-based tests for Identifier value object."""

    @pytest.mark.property
    @given(st.uuids())
    def test_construction_preserves_uuid(self, uuid_val):
        """Property: constructed Identifier should preserve the UUID value."""
        identifier = Identifier[str](value=uuid_val)
        assert identifier.value == uuid_val

    @pytest.mark.property
    @given(st.uuids())
    def test_from_string_roundtrip(self, uuid_val):
        """Property: UUID -> string -> Identifier should preserve value."""
        uuid_str = str(uuid_val)
        identifier = Identifier[str].from_string(uuid_str)
        assert identifier.value == uuid_val

    @pytest.mark.property
    @given(st.uuids())
    def test_identifier_equality_reflexive(self, uuid_val):
        """Property: identifier should equal itself (reflexive)."""
        identifier = Identifier[str](value=uuid_val)
        assert identifier == identifier

    @pytest.mark.property
    @given(st.uuids())
    def test_identifier_equality_symmetric(self, uuid_val):
        """Property: if id1 == id2, then id2 == id1 (symmetric)."""
        id1 = Identifier[str](value=uuid_val)
        id2 = Identifier[str](value=uuid_val)
        assert (id1 == id2) == (id2 == id1)

    @pytest.mark.property
    @given(st.uuids())
    def test_identifier_hash_consistency(self, uuid_val):
        """Property: equal identifiers should have equal hashes."""
        id1 = Identifier[str](value=uuid_val)
        id2 = Identifier[str](value=uuid_val)
        if id1 == id2:
            assert hash(id1) == hash(id2)

    @pytest.mark.property
    def test_generated_identifiers_are_unique(self):
        """Property: generated identifiers should be unique with high probability."""
        # Generate 100 identifiers and check they're all unique
        identifiers = [Identifier[str].generate() for _ in range(100)]
        uuid_values = [id_.value for id_ in identifiers]
        assert len(uuid_values) == len(set(uuid_values))


class TestIdentifierEdgeCases:
    """Test Identifier edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_identifier_with_nil_uuid(self):
        """Test identifier with nil UUID (all zeros)."""
        nil_uuid = UUID("00000000-0000-0000-0000-000000000000")
        identifier = Identifier[str](value=nil_uuid)
        assert identifier.value == nil_uuid

    @pytest.mark.unit
    def test_identifier_with_max_uuid(self):
        """Test identifier with maximum UUID (all Fs)."""
        max_uuid = UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
        identifier = Identifier[str](value=max_uuid)
        assert identifier.value == max_uuid

    @pytest.mark.unit
    def test_identifier_from_string_with_braces(self):
        """Test creating identifier from UUID string with braces."""
        uuid_str = "{550e8400-e29b-41d4-a716-446655440000}"
        identifier = Identifier[str].from_string(uuid_str)
        assert isinstance(identifier.value, UUID)

    @pytest.mark.unit
    def test_identifier_from_string_with_urn(self):
        """Test creating identifier from UUID URN format."""
        uuid_str = "urn:uuid:550e8400-e29b-41d4-a716-446655440000"
        identifier = Identifier[str].from_string(uuid_str)
        assert isinstance(identifier.value, UUID)


class TestIdentifierBusinessRules:
    """Test Identifier business rules and real-world scenarios."""

    @pytest.mark.unit
    def test_identifier_can_be_serialized(self):
        """Test that identifier UUID can be serialized to string."""
        identifier = Identifier[str].generate()
        uuid_str = str(identifier.value)
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36  # Standard UUID string length with hyphens

    @pytest.mark.unit
    def test_identifier_roundtrip_serialization(self):
        """Test full roundtrip: generate -> serialize -> deserialize."""
        original = Identifier[str].generate()
        serialized = str(original.value)
        deserialized = Identifier[str].from_string(serialized)
        assert original == deserialized

    @pytest.mark.unit
    def test_identifier_different_versions(self):
        """Test identifiers work with different UUID versions."""
        # UUID4 (random)
        uuid4_val = uuid4()
        id4 = Identifier[str](value=uuid4_val)
        assert id4.value == uuid4_val

        # UUID from string (could be any version)
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        id_any = Identifier[str].from_string(uuid_str)
        assert isinstance(id_any.value, UUID)
