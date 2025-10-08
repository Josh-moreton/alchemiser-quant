"""Business Unit: shared | Status: current.

Test suite for ASTNode schema.

Comprehensive unit tests for AST node data transfer objects, including
factory methods, type checking, validation, and immutability guarantees.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.ast_node import ASTNode


@pytest.mark.unit
class TestASTNodeFactoryMethods:
    """Test ASTNode factory methods."""

    def test_symbol_factory_creates_symbol_node(self):
        """Test symbol() factory creates correct node."""
        node = ASTNode.symbol("test-symbol")
        
        assert node.node_type == "symbol"
        assert node.value == "test-symbol"
        assert node.children == []
        assert node.metadata is None

    def test_symbol_factory_with_metadata(self):
        """Test symbol() factory with metadata."""
        metadata = {"line": 1, "column": 5}
        node = ASTNode.symbol("test-symbol", metadata=metadata)
        
        assert node.node_type == "symbol"
        assert node.value == "test-symbol"
        assert node.metadata == metadata

    def test_atom_factory_with_string_value(self):
        """Test atom() factory with string value."""
        node = ASTNode.atom("test-string")
        
        assert node.node_type == "atom"
        assert node.value == "test-string"
        assert node.children == []
        assert node.metadata is None

    def test_atom_factory_with_decimal_value(self):
        """Test atom() factory with Decimal value."""
        value = Decimal("42.5")
        node = ASTNode.atom(value)
        
        assert node.node_type == "atom"
        assert node.value == value
        assert node.children == []

    def test_atom_factory_with_negative_decimal(self):
        """Test atom() factory with negative Decimal."""
        value = Decimal("-10.25")
        node = ASTNode.atom(value)
        
        assert node.node_type == "atom"
        assert node.value == value

    def test_list_node_factory_empty(self):
        """Test list_node() factory with empty children."""
        node = ASTNode.list_node([])
        
        assert node.node_type == "list"
        assert node.value is None
        assert node.children == []

    def test_list_node_factory_with_children(self):
        """Test list_node() factory with child nodes."""
        child1 = ASTNode.symbol("child1")
        child2 = ASTNode.atom(Decimal("42"))
        node = ASTNode.list_node([child1, child2])
        
        assert node.node_type == "list"
        assert node.value is None
        assert len(node.children) == 2
        assert node.children[0] == child1
        assert node.children[1] == child2

    def test_list_node_factory_nested(self):
        """Test list_node() factory with nested children."""
        inner_list = ASTNode.list_node([ASTNode.symbol("inner")])
        outer_list = ASTNode.list_node([inner_list])
        
        assert outer_list.node_type == "list"
        assert len(outer_list.children) == 1
        assert outer_list.children[0].node_type == "list"


@pytest.mark.unit
class TestASTNodeTypeChecking:
    """Test ASTNode type checking methods."""

    def test_is_symbol_returns_true_for_symbol(self):
        """Test is_symbol() returns True for symbol nodes."""
        node = ASTNode.symbol("test")
        assert node.is_symbol() is True

    def test_is_symbol_returns_false_for_atom(self):
        """Test is_symbol() returns False for atom nodes."""
        node = ASTNode.atom("test")
        assert node.is_symbol() is False

    def test_is_symbol_returns_false_for_list(self):
        """Test is_symbol() returns False for list nodes."""
        node = ASTNode.list_node([])
        assert node.is_symbol() is False

    def test_is_atom_returns_true_for_atom(self):
        """Test is_atom() returns True for atom nodes."""
        node = ASTNode.atom("test")
        assert node.is_atom() is True

    def test_is_atom_returns_false_for_symbol(self):
        """Test is_atom() returns False for symbol nodes."""
        node = ASTNode.symbol("test")
        assert node.is_atom() is False

    def test_is_atom_returns_false_for_list(self):
        """Test is_atom() returns False for list nodes."""
        node = ASTNode.list_node([])
        assert node.is_atom() is False

    def test_is_list_returns_true_for_list(self):
        """Test is_list() returns True for list nodes."""
        node = ASTNode.list_node([])
        assert node.is_list() is True

    def test_is_list_returns_false_for_symbol(self):
        """Test is_list() returns False for symbol nodes."""
        node = ASTNode.symbol("test")
        assert node.is_list() is False

    def test_is_list_returns_false_for_atom(self):
        """Test is_list() returns False for atom nodes."""
        node = ASTNode.atom("test")
        assert node.is_list() is False


@pytest.mark.unit
class TestASTNodeAccessors:
    """Test ASTNode value accessor methods."""

    def test_get_symbol_name_returns_name_for_symbol(self):
        """Test get_symbol_name() returns name for symbol nodes."""
        node = ASTNode.symbol("test-symbol")
        assert node.get_symbol_name() == "test-symbol"

    def test_get_symbol_name_returns_none_for_atom(self):
        """Test get_symbol_name() returns None for atom nodes."""
        node = ASTNode.atom("test")
        assert node.get_symbol_name() is None

    def test_get_symbol_name_returns_none_for_list(self):
        """Test get_symbol_name() returns None for list nodes."""
        node = ASTNode.list_node([])
        assert node.get_symbol_name() is None

    def test_get_atom_value_returns_string_value(self):
        """Test get_atom_value() returns string value for atom nodes."""
        node = ASTNode.atom("test-string")
        assert node.get_atom_value() == "test-string"

    def test_get_atom_value_returns_decimal_value(self):
        """Test get_atom_value() returns Decimal value for atom nodes."""
        value = Decimal("42.5")
        node = ASTNode.atom(value)
        assert node.get_atom_value() == value

    def test_get_atom_value_returns_none_for_symbol(self):
        """Test get_atom_value() returns None for symbol nodes."""
        node = ASTNode.symbol("test")
        assert node.get_atom_value() is None

    def test_get_atom_value_returns_none_for_list(self):
        """Test get_atom_value() returns None for list nodes."""
        node = ASTNode.list_node([])
        assert node.get_atom_value() is None


@pytest.mark.unit
class TestASTNodeImmutability:
    """Test ASTNode immutability guarantees."""

    def test_cannot_modify_node_type(self):
        """Test that node_type cannot be modified after creation."""
        node = ASTNode.symbol("test")
        
        with pytest.raises(ValidationError):
            node.node_type = "atom"  # type: ignore

    def test_cannot_modify_value(self):
        """Test that value cannot be modified after creation."""
        node = ASTNode.atom("original")
        
        with pytest.raises(ValidationError):
            node.value = "modified"  # type: ignore

    def test_cannot_reassign_children_list(self):
        """Test that children list cannot be reassigned after creation."""
        child = ASTNode.symbol("child")
        node = ASTNode.list_node([child])
        
        with pytest.raises(ValidationError):
            node.children = [ASTNode.symbol("new")]  # type: ignore

    def test_cannot_modify_metadata(self):
        """Test that metadata cannot be modified after creation."""
        metadata = {"line": 1}
        node = ASTNode.symbol("test", metadata=metadata)
        
        with pytest.raises(ValidationError):
            node.metadata = {"line": 2}  # type: ignore


@pytest.mark.unit
class TestASTNodeValidation:
    """Test ASTNode Pydantic validation."""

    def test_rejects_empty_node_type(self):
        """Test that empty node_type is rejected."""
        with pytest.raises(ValidationError):
            ASTNode(node_type="", value="test")

    def test_rejects_invalid_value_type(self):
        """Test that invalid value types are rejected."""
        with pytest.raises(ValidationError):
            ASTNode(node_type="atom", value=42)  # type: ignore  # int not allowed

    def test_rejects_invalid_children_type(self):
        """Test that invalid children types are rejected."""
        with pytest.raises(ValidationError):
            ASTNode(node_type="list", children=["not", "ast", "nodes"])  # type: ignore

    def test_accepts_none_value(self):
        """Test that None value is accepted for list nodes."""
        node = ASTNode(node_type="list", value=None, children=[])
        assert node.value is None

    def test_whitespace_stripped_from_string_values(self):
        """Test that whitespace is stripped from string values."""
        node = ASTNode(node_type="symbol", value="  test  ")
        assert node.value == "test"


@pytest.mark.unit
class TestASTNodeSerialization:
    """Test ASTNode serialization and deserialization."""

    def test_symbol_roundtrip(self):
        """Test symbol node can be serialized and deserialized."""
        original = ASTNode.symbol("test-symbol")
        dumped = original.model_dump()
        restored = ASTNode.model_validate(dumped)
        
        assert restored.node_type == original.node_type
        assert restored.value == original.value
        assert restored.children == original.children

    def test_atom_with_decimal_roundtrip(self):
        """Test atom node with Decimal can be serialized and deserialized."""
        original = ASTNode.atom(Decimal("42.5"))
        dumped = original.model_dump()
        restored = ASTNode.model_validate(dumped)
        
        assert restored.node_type == original.node_type
        assert restored.value == original.value

    def test_list_node_roundtrip(self):
        """Test list node can be serialized and deserialized."""
        child1 = ASTNode.symbol("child1")
        child2 = ASTNode.atom(Decimal("42"))
        original = ASTNode.list_node([child1, child2])
        
        dumped = original.model_dump()
        restored = ASTNode.model_validate(dumped)
        
        assert restored.node_type == original.node_type
        assert len(restored.children) == 2
        assert restored.children[0].get_symbol_name() == "child1"
        assert restored.children[1].get_atom_value() == Decimal("42")

    def test_nested_list_roundtrip(self):
        """Test deeply nested list can be serialized and deserialized."""
        inner = ASTNode.list_node([ASTNode.atom(Decimal("1"))])
        middle = ASTNode.list_node([inner])
        outer = ASTNode.list_node([middle])
        
        dumped = outer.model_dump()
        restored = ASTNode.model_validate(dumped)
        
        assert restored.is_list()
        assert restored.children[0].is_list()
        assert restored.children[0].children[0].is_list()


@pytest.mark.unit
class TestASTNodeEdgeCases:
    """Test ASTNode edge cases and boundary conditions."""

    def test_empty_string_symbol(self):
        """Test that empty string as symbol name is rejected."""
        # Empty strings are rejected by min_length=1 constraint
        with pytest.raises(ValidationError):
            ASTNode(node_type="", value="test")

    def test_very_long_symbol_name(self):
        """Test that very long symbol names are accepted."""
        long_name = "x" * 10000
        node = ASTNode.symbol(long_name)
        assert node.get_symbol_name() == long_name

    def test_special_characters_in_symbol(self):
        """Test that special characters in symbols are preserved."""
        special = "test-symbol_with+special><=!?*chars"
        node = ASTNode.symbol(special)
        assert node.get_symbol_name() == special

    def test_zero_decimal_value(self):
        """Test that zero Decimal values are handled correctly."""
        node = ASTNode.atom(Decimal("0"))
        assert node.get_atom_value() == Decimal("0")

    def test_negative_zero_decimal(self):
        """Test that negative zero Decimal is preserved."""
        value = Decimal("-0.0")
        node = ASTNode.atom(value)
        assert node.get_atom_value() == value

    def test_very_large_decimal(self):
        """Test that very large Decimal values are handled."""
        large = Decimal("999999999999999999999999999.999999")
        node = ASTNode.atom(large)
        assert node.get_atom_value() == large

    def test_empty_metadata_dict(self):
        """Test that empty metadata dict is accepted."""
        node = ASTNode.symbol("test", metadata={})
        assert node.metadata == {}

    def test_nested_metadata_structures(self):
        """Test that nested metadata structures are accepted."""
        metadata = {"info": {"line": 1, "column": 5}}
        node = ASTNode.symbol("test", metadata=metadata)
        assert node.metadata == metadata


@pytest.mark.unit
@pytest.mark.property
class TestASTNodeProperties:
    """Property-based tests for ASTNode invariants."""

    def test_symbol_nodes_have_string_values(self):
        """Test that all symbol nodes have string values."""
        symbols = [
            ASTNode.symbol("test"),
            ASTNode.symbol("another-symbol"),
            ASTNode.symbol(":keyword"),
        ]
        
        for symbol in symbols:
            assert isinstance(symbol.value, str)
            assert symbol.get_symbol_name() is not None

    def test_atom_nodes_have_non_none_values(self):
        """Test that all atom nodes have non-None values."""
        atoms = [
            ASTNode.atom("string"),
            ASTNode.atom(Decimal("42")),
            ASTNode.atom(Decimal("-10.5")),
        ]
        
        for atom in atoms:
            assert atom.value is not None
            assert atom.get_atom_value() is not None

    def test_list_nodes_have_none_values(self):
        """Test that all list nodes have None values."""
        lists = [
            ASTNode.list_node([]),
            ASTNode.list_node([ASTNode.symbol("x")]),
            ASTNode.list_node([ASTNode.atom(Decimal("1")), ASTNode.atom(Decimal("2"))]),
        ]
        
        for list_node in lists:
            assert list_node.value is None

    def test_only_one_type_check_returns_true(self):
        """Test that exactly one type check method returns True."""
        nodes = [
            ASTNode.symbol("test"),
            ASTNode.atom("test"),
            ASTNode.list_node([]),
        ]
        
        for node in nodes:
            type_checks = [node.is_symbol(), node.is_atom(), node.is_list()]
            assert sum(type_checks) == 1  # Exactly one should be True

    def test_tree_structure_preserved_through_serialization(self):
        """Test that tree structure is preserved through serialization."""
        # Build a tree: (+ (- 5 3) 2)
        inner = ASTNode.list_node([
            ASTNode.symbol("-"),
            ASTNode.atom(Decimal("5")),
            ASTNode.atom(Decimal("3")),
        ])
        outer = ASTNode.list_node([
            ASTNode.symbol("+"),
            inner,
            ASTNode.atom(Decimal("2")),
        ])
        
        # Serialize and deserialize
        restored = ASTNode.model_validate(outer.model_dump())
        
        # Verify structure is preserved
        assert restored.is_list()
        assert len(restored.children) == 3
        assert restored.children[0].get_symbol_name() == "+"
        assert restored.children[1].is_list()
        assert len(restored.children[1].children) == 3
        assert restored.children[1].children[0].get_symbol_name() == "-"
        assert restored.children[2].get_atom_value() == Decimal("2")
