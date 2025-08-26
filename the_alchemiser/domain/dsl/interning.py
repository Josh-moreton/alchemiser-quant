"""AST interning system for structural sharing (hash-consing).

Converts AST trees to DAGs by deduplicating identical subtrees,
dramatically reducing memory usage and node traversal work for
strategies with heavy structural reuse.
"""

from __future__ import annotations

import hashlib
from dataclasses import fields, is_dataclass
from typing import Any
from weakref import WeakValueDictionary

from the_alchemiser.domain.dsl.ast import ASTNode

# Global interner pool using weak references for automatic cleanup
_intern_pool: WeakValueDictionary[tuple[Any, ...], ASTNode] = WeakValueDictionary()

# Statistics for telemetry
_intern_stats = {
    "total_requests": 0,
    "cache_hits": 0,
    "unique_nodes": 0,
}


def node_key(node: ASTNode) -> tuple[Any, ...]:
    """Generate a stable, hashable key for an AST node.

    The key includes the class name and all field values, with child nodes
    replaced by their recursive keys to enable structural sharing.
    Only includes fields that are part of the constructor (init=True).

    Args:
        node: AST node to generate key for

    Returns:
        Tuple that uniquely identifies the node structure

    """
    if not is_dataclass(node):
        raise ValueError(f"Expected dataclass, got {type(node)}")

    parts: list[Any] = [node.__class__.__name__]
    for field in fields(node):
        # Only include fields that are part of the constructor
        if field.init:
            value = getattr(node, field.name)
            parts.append(_stable_value(value))

    return tuple(parts)


def _stable_value(value: Any) -> tuple[Any, ...]:
    """Convert a value into a canonical hashable representation.

    Dataclass instances (AST nodes) are represented by their structural key.
    Collections are recursively processed with tagged tuples to avoid collisions.
    """
    if is_dataclass(value):
        # We only expect ASTNode dataclasses here; if an unrelated dataclass
        # appears it will still produce a deterministic structural key.
        return ("NODE",) + node_key(value)  # type: ignore[arg-type]
    if isinstance(value, list):
        return ("LIST", tuple(_stable_value(item) for item in value))
    if isinstance(value, tuple):
        return ("TUPLE", tuple(_stable_value(item) for item in value))
    if isinstance(value, dict):
        items = tuple(sorted((k, _stable_value(v)) for k, v in value.items()))
        return ("DICT", items)
    return ("PRIM", value)


def intern_node(node: ASTNode) -> ASTNode:
    """Intern an AST node, returning a canonical instance.

    If an identical node structure has been seen before, returns the
    existing instance. Otherwise, stores this node and returns it.

    Args:
        node: AST node to intern

    Returns:
        Canonical instance of the node (may be the same object or a cached one)

    """
    global _intern_stats

    _intern_stats["total_requests"] += 1

    key = node_key(node)

    # Check if we already have this structure
    cached = _intern_pool.get(key)
    if cached is not None:
        _intern_stats["cache_hits"] += 1
        return cached

    # New structure - store it and attach a node_id
    _intern_pool[key] = node
    _intern_stats["unique_nodes"] += 1

    # Attach a stable node_id for use in evaluator caching
    # Use a hash of the key for deterministic IDs
    node_id = _compute_node_id(key)
    object.__setattr__(node, "node_id", node_id)

    return node


def _compute_node_id(key: tuple[Any, ...]) -> str:
    """Compute a stable, unique ID for a node key.

    Uses BLAKE2b for fast, cryptographically strong hashing.
    """
    key_str = str(key).encode("utf-8")
    return hashlib.blake2b(key_str, digest_size=16).hexdigest()


def canonicalise_ast(root: ASTNode) -> ASTNode:
    """Canonicalise an entire AST, applying structural sharing throughout.

    Performs post-order traversal to ensure children are canonicalised
    before parents, maximizing sharing opportunities.

    Args:
        root: Root AST node to canonicalise

    Returns:
        Canonicalised AST with structural sharing applied

    """
    return _canonicalise_recursive(root)


def _canonicalise_recursive(node: ASTNode) -> ASTNode:
    """Recursively canonicalise a node and its children."""
    # First, canonicalise all child nodes (post-order)
    canonicalised_fields: dict[str, Any] = {}
    for field in fields(node):
        if not field.init:
            continue
        value = getattr(node, field.name)
        canonicalised_fields[field.name] = _canonicalise_value(value)

    # Create a new node with canonicalised children
    fresh_node = node.__class__(**canonicalised_fields)

    # Intern the node with canonicalised children (ensures node_id assignment)
    return intern_node(fresh_node)


def _canonicalise_value(value: Any) -> Any:
    """Canonicalise nested values (child nodes, collections, primitives)."""
    if is_dataclass(value):
        return _canonicalise_recursive(value)  # type: ignore[arg-type]
    if isinstance(value, list):
        return [_canonicalise_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_canonicalise_value(item) for item in value)
    if isinstance(value, dict):
        return {k: _canonicalise_value(v) for k, v in value.items()}
    return value


def get_intern_stats() -> dict[str, Any]:
    """Get interning statistics for telemetry.

    Returns:
        Dictionary with interning metrics including hit rates

    """
    total = _intern_stats["total_requests"]
    hits = _intern_stats["cache_hits"]
    hit_rate = (hits / total) if total > 0 else 0.0

    return {
        "intern_total_requests": total,
        "intern_cache_hits": hits,
        "intern_unique_nodes": _intern_stats["unique_nodes"],
        "intern_hit_rate": hit_rate,
        "intern_pool_size": len(_intern_pool),
    }


def clear_intern_stats() -> None:
    """Clear interning statistics (for testing)."""
    global _intern_stats
    _intern_stats = {
        "total_requests": 0,
        "cache_hits": 0,
        "unique_nodes": 0,
    }


def clear_intern_pool() -> None:
    """Clear the interning pool (for testing)."""
    global _intern_pool
    _intern_pool.clear()
