#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

AST node data transfer objects for DSL engine.

Provides typed schemas for Abstract Syntax Tree nodes used by the DSL engine
to represent parsed S-expressions with proper validation and type safety.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..constants import CONTRACT_VERSION


class ASTNode(BaseModel):
    """DTO for Abstract Syntax Tree nodes from S-expression parsing.

    Represents parsed S-expressions as a tree structure with typed nodes
    for evaluation by the DSL engine.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Node identification
    node_type: str = Field(..., min_length=1, description="Type of AST node (symbol, list, atom)")
    value: str | Decimal | None = Field(default=None, description="Node value for atoms")

    # Tree structure
    children: list[ASTNode] = Field(default_factory=list, description="Child nodes")

    # Metadata
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional node metadata for evaluation"
    )

    @classmethod
    def symbol(cls, name: str, metadata: dict[str, Any] | None = None) -> ASTNode:
        """Create a symbol node.

        Args:
            name: Symbol name
            metadata: Optional metadata

        Returns:
            ASTNode representing a symbol

        """
        return cls(node_type="symbol", value=name, metadata=metadata)

    @classmethod
    def atom(cls, value: str | Decimal, metadata: dict[str, Any] | None = None) -> ASTNode:
        """Create an atom node.

        Args:
            value: Atom value
            metadata: Optional metadata

        Returns:
            ASTNode representing an atom

        """
        return cls(node_type="atom", value=value, metadata=metadata)

    @classmethod
    def list_node(cls, children: list[ASTNode], metadata: dict[str, Any] | None = None) -> ASTNode:
        """Create a list node.

        Args:
            children: Child nodes
            metadata: Optional metadata

        Returns:
            ASTNode representing a list

        """
        return cls(node_type="list", children=children, metadata=metadata)

    def is_symbol(self) -> bool:
        """Check if node is a symbol."""
        return self.node_type == "symbol"

    def is_atom(self) -> bool:
        """Check if node is an atom."""
        return self.node_type == "atom"

    def is_list(self) -> bool:
        """Check if node is a list."""
        return self.node_type == "list"

    def get_symbol_name(self) -> str | None:
        """Get symbol name if this is a symbol node."""
        if self.is_symbol() and isinstance(self.value, str):
            return self.value
        return None

    def get_atom_value(self) -> str | Decimal | None:
        """Get atom value if this is an atom node."""
        if self.is_atom():
            return self.value
        return None
