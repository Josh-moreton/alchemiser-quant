"""Utility helpers for application-layer boundary serialization.

Provides safe, recursive conversion of Pydantic models, dataclasses, Decimals,
and nested containers into JSON-friendly Python primitives while preserving
semantic meaning (Decimals -> str to avoid precision loss).

NOTE: These helpers are intentionally lightweight and have no side effects.
They MUST NOT be imported inside domain layer code (application / interface
boundaries only).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from typing import Any, Protocol, cast


class _ModelDumpProtocol(Protocol):  # pragma: no cover - structural typing helper
    """Structural protocol for objects exposing model_dump (e.g., Pydantic)."""

    def model_dump(self) -> dict[str, Any]:  # noqa: D401 - concise
        ...


def _is_model_dump_obj(value: Any) -> bool:
    method = getattr(value, "model_dump", None)
    return callable(method)


def to_serializable(value: Any) -> Any:  # noqa: C901 - controlled complexity
    """Recursively convert value into JSON-friendly primitives.

    Policy:
    - Decimal -> str (exact representation)
    - Objects with model_dump() -> recurse over dumped dict
    - Dataclass instances -> asdict() then recurse
    - Mapping -> recurse key/values
    - Sequence/Set (excluding str/bytes) -> list of converted values
    - Other primitives unchanged
    """
    if isinstance(value, Decimal):
        return str(value)

    if _is_model_dump_obj(value):  # Pydantic or similar
        try:
            dumped = cast(_ModelDumpProtocol, value).model_dump()
            return {k: to_serializable(v) for k, v in dumped.items()}
        except Exception:  # pragma: no cover - defensive fallback
            return str(value)

    # Ensure we only treat dataclass *instances* (is_dataclass also True for classes)
    if is_dataclass(value) and not isinstance(value, type):
        return to_serializable(asdict(value))

    if isinstance(value, Mapping):
        return {k: to_serializable(v) for k, v in value.items()}

    if (
        isinstance(value, list | tuple | set) or isinstance(value, Sequence | Set)
    ) and not isinstance(value, str | bytes):
        return [to_serializable(v) for v in list(value)]

    return value


def ensure_serialized_dict(data: Any) -> dict[str, Any]:
    """Convert supported inputs to a serialized dict[str, Any] or raise.

    Supported inputs: dict, dataclass instance, pydantic-like model (model_dump).
    """
    if isinstance(data, dict):
        result = to_serializable(data)
    elif _is_model_dump_obj(data):
        result = to_serializable(data)
    elif is_dataclass(data) and not isinstance(data, type):
        result = to_serializable(asdict(data))
    else:
        raise TypeError(f"Cannot serialize object of type {type(data)!r} to dict")

    if not isinstance(result, dict):  # Narrow for mypy
        raise TypeError("Serialization did not produce a dictionary")
    return cast(dict[str, Any], result)
