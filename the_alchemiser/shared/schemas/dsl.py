#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

AST node data transfer objects for DSL engine.

Provides typed DTOs for Abstract Syntax Tree nodes used by the DSL engine
to represent parsed S-expressions with proper validation and type safety.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware


class ASTNode(BaseModel):
    """DTO for Abstract Syntax Tree nodes from S-expression parsing.

    Represents parsed S-expressions as a tree structure with typed nodes
    for evaluation by the DSL engine.
    """

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
    def list_node(
        cls, children: list[ASTNode], metadata: dict[str, Any] | None = None
    ) -> ASTNode:
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


class TraceEntry(BaseModel):
    """Single trace entry in strategy evaluation."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    step_id: str = Field(..., min_length=1, description="Unique step identifier")
    step_type: str = Field(..., min_length=1, description="Type of evaluation step")
    timestamp: datetime = Field(..., description="When this step occurred")
    description: str = Field(..., min_length=1, description="Human-readable step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Step inputs")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Step outputs")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional step metadata")

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)


class Trace(BaseModel):
    """DTO for complete strategy evaluation trace.

    Contains structured trace log for audit and observability purposes.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Trace identification
    trace_id: str = Field(..., min_length=1, description="Unique trace identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for request tracking")
    causation_id: str = Field(..., min_length=1, description="Causation ID for traceability")

    # Trace metadata
    strategy_name: str = Field(..., min_length=1, description="Strategy that was evaluated")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    start_timestamp: datetime = Field(..., description="When trace started")
    end_timestamp: datetime | None = Field(default=None, description="When trace completed")

    # Trace entries
    entries: list[TraceEntry] = Field(default_factory=list, description="Trace entries")

    # Summary
    total_steps: int = Field(default=0, ge=0, description="Total number of steps")
    duration_ms: int | None = Field(default=None, ge=0, description="Total duration in milliseconds")
    success: bool = Field(default=True, description="Whether evaluation succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("start_timestamp", "end_timestamp")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware."""
        if v is None:
            return v
        return ensure_timezone_aware(v)

    def add_entry(self, entry: TraceEntry) -> None:
        """Add a trace entry (if model wasn't frozen)."""
        # Note: This would not work with frozen=True, but provided for interface compatibility
        raise RuntimeError("Cannot modify frozen model - create new instance with updated entries")

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization."""
        data = self.model_dump()

        # Convert datetime fields to ISO strings
        datetime_fields = ["start_timestamp", "end_timestamp"]
        for field_name in datetime_fields:
            if data.get(field_name):
                data[field_name] = data[field_name].isoformat()

        # Convert nested entries
        if "entries" in data:
            entries_data = []
            for entry in data["entries"]:
                entry_dict = dict(entry)
                if entry_dict.get("timestamp"):
                    entry_dict["timestamp"] = entry_dict["timestamp"].isoformat()
                entries_data.append(entry_dict)
            data["entries"] = entries_data

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trace:
        """Create DTO from dictionary."""
        # Convert datetime strings back to datetime objects
        datetime_fields = ["start_timestamp", "end_timestamp"]
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    timestamp_str = data[field_name]
                    if timestamp_str.endswith("Z"):
                        timestamp_str = timestamp_str[:-1] + "+00:00"
                    data[field_name] = datetime.fromisoformat(timestamp_str)
                except ValueError as e:
                    raise ValueError(f"Invalid {field_name} format: {data[field_name]}") from e

        # Convert entries back to TraceEntryDTO objects
        if "entries" in data and isinstance(data["entries"], list):
            entries_data = []
            for entry_data in data["entries"]:
                if isinstance(entry_data, dict):
                    # Convert timestamp in entry
                    if "timestamp" in entry_data and isinstance(entry_data["timestamp"], str):
                        try:
                            timestamp_str = entry_data["timestamp"]
                            if timestamp_str.endswith("Z"):
                                timestamp_str = timestamp_str[:-1] + "+00:00"
                            entry_data["timestamp"] = datetime.fromisoformat(timestamp_str)
                        except ValueError as e:
                            raise ValueError(f"Invalid entry timestamp: {entry_data['timestamp']}") from e
                    entries_data.append(TraceEntry(**entry_data))
                else:
                    entries_data.append(entry_data)  # Assume already TraceEntry
            data["entries"] = entries_data

        return cls(**data)
