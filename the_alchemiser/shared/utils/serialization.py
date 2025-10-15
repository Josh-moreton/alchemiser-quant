"""Business Unit: shared | Status: current.

Utility helpers for application-layer boundary serialization.

Provides safe, recursive conversion of Pydantic models, dataclasses, Decimals,
datetime, exceptions, and nested containers into JSON-friendly Python primitives
while preserving semantic meaning (Decimals -> str to avoid precision loss,
datetime -> RFC3339Z strings, exceptions -> error dicts).

This module is designed for EventBridge publishing and structured logging where
JSON serialization is required. All functions recursively handle nested structures
and ensure the output is JSON-serializable via json.dumps().

NOTE: These helpers are intentionally lightweight and have no side effects.
They MUST NOT be imported inside domain layer code (application / interface
boundaries only).
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence, Set
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol, cast


class _ModelDumpProtocol(Protocol):  # pragma: no cover - structural typing helper
    """Structural protocol for objects exposing model_dump (e.g., Pydantic)."""

    def model_dump(self) -> dict[str, Any]: ...


def _is_model_dump_obj(value: object) -> bool:
    method = getattr(value, "model_dump", None)
    return callable(method)


def _dt_to_rfc3339z(dt: datetime) -> str:
    """Convert datetime to RFC3339 string with Z suffix (UTC).

    Args:
        dt: Datetime to convert (should be timezone-aware)

    Returns:
        ISO 8601 string with Z suffix (e.g., "2025-10-15T08:13:16.741Z")

    """
    # Ensure datetime is in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    elif dt.tzinfo != UTC:
        dt = dt.astimezone(UTC)

    # Use isoformat and replace +00:00 with Z
    return dt.isoformat().replace("+00:00", "Z")


def to_serializable(value: object) -> object:
    """Recursively convert value into JSON-friendly primitives.

    Policy:
    - Decimal -> str (exact representation)
    - datetime -> RFC3339 string with Z suffix
    - Exception -> dict with error_type and error_message
    - Objects with model_dump() -> recurse over dumped dict (using mode="json")
    - Dataclass instances -> asdict() then recurse
    - Mapping -> recurse key/values
    - Sequence/Set (excluding str/bytes) -> list of converted values
    - Other primitives unchanged

    Note: For Pydantic models, this uses model_dump() without mode="json" to maintain
    backward compatibility with existing code. Use json_sanitise() for EventBridge
    or logging where explicit JSON serialization is required.
    """
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, datetime):
        return _dt_to_rfc3339z(value)

    if isinstance(value, Exception):
        return {
            "error_type": type(value).__name__,
            "error_message": str(value),
        }

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

    if isinstance(value, list | tuple | set | Sequence | Set) and not isinstance(
        value, str | bytes
    ):
        return [to_serializable(v) for v in value]

    return value


def ensure_serialized_dict(data: object) -> dict[str, object]:
    """Convert supported inputs to a serialized dict[str, Any] or raise.

    Supported inputs: dict, dataclass instance, pydantic-like model (model_dump).
    """
    if isinstance(data, dict) or _is_model_dump_obj(data):
        result = to_serializable(data)
    elif is_dataclass(data) and not isinstance(data, type):
        result = to_serializable(asdict(data))
    else:
        raise TypeError(f"Cannot serialize object of type {type(data)!r} to dict")

    if not isinstance(result, dict):  # Narrow for mypy
        raise TypeError("Serialization did not produce a dictionary")
    return cast(dict[str, object], result)


def json_sanitise(obj: Any) -> Any:
    """Recursively convert object to JSON-serializable primitives.

    This function is stricter than to_serializable() and ensures the output
    is fully JSON-serializable by using mode="json" on Pydantic models.

    Policy:
    - Decimal -> str (exact representation)
    - datetime -> RFC3339 string with Z suffix
    - Exception -> dict with error_type and error_message
    - BaseModel -> model_dump(mode="json") with recursive sanitization
    - Dataclass instances -> asdict() then recurse
    - Mapping -> recurse key/values (keys converted to str)
    - Sequence/Set (excluding str/bytes) -> list of converted values
    - Other primitives unchanged

    Args:
        obj: Object to sanitize

    Returns:
        JSON-serializable Python primitives (dict/list/str/int/float/bool/None)

    """
    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, datetime):
        return _dt_to_rfc3339z(obj)

    if isinstance(obj, Exception):
        return {
            "error_type": type(obj).__name__,
            "error_message": str(obj),
        }

    if _is_model_dump_obj(obj):  # Pydantic or similar
        try:
            # Use mode="json" to ensure proper serialization
            dumped = cast(_ModelDumpProtocol, obj).model_dump(mode="json")  # type: ignore[call-arg]
            return {str(k): json_sanitise(v) for k, v in dumped.items()}
        except TypeError:
            # Fallback for models that don't support mode="json"
            dumped = cast(_ModelDumpProtocol, obj).model_dump()
            return {str(k): json_sanitise(v) for k, v in dumped.items()}
        except Exception:  # pragma: no cover - defensive fallback
            return str(obj)

    if is_dataclass(obj) and not isinstance(obj, type):
        return json_sanitise(asdict(obj))

    if isinstance(obj, Mapping):
        return {str(k): json_sanitise(v) for k, v in obj.items()}

    if isinstance(obj, list | tuple | set | Sequence | Set) and not isinstance(
        obj, str | bytes
    ):
        return [json_sanitise(v) for v in obj]

    return obj


def safe_json_dumps(obj: Any, **kwargs: Any) -> str:
    """Safely serialize object to JSON string.

    This wraps json.dumps with json_sanitise to ensure all non-JSON-serializable
    objects (Decimal, datetime, Exception, Pydantic models) are converted.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments to pass to json.dumps (e.g., indent, sort_keys)

    Returns:
        JSON string

    """
    # Set default for ensure_ascii if not provided
    if "ensure_ascii" not in kwargs:
        kwargs["ensure_ascii"] = False

    return json.dumps(json_sanitise(obj), **kwargs)


def event_to_detail_str(event: Any) -> str:
    """Convert event to EventBridge detail string.

    This is the canonical way to serialize events for EventBridge publishing.
    Always use this function instead of json.dumps() when creating EventBridge
    detail payloads.

    Args:
        event: Event object (typically a Pydantic BaseModel)

    Returns:
        JSON string suitable for EventBridge detail field

    """
    return safe_json_dumps(event)


def error_to_payload(error: Exception) -> dict[str, str]:
    """Convert exception to JSON-serializable error payload.

    This is the canonical way to represent errors in event payloads.
    Never put raw Exception objects into events or logs.

    Args:
        error: Exception to convert

    Returns:
        Dict with error_type and error_message keys

    """
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
