"""Business Unit: utilities; Status: current.

Evaluation context & caching utilities for DSL evaluator memoisation.

Changes (post review hardening):
 - Replaced hybrid functools.lru_cache approach with a true thread-safe
     OrderedDict-based LRU implementation.
 - Added helper to safely assign stable node IDs when interning is disabled
     so memoisation can still function (structural hashing fallback).
 - Added internal locking for concurrent access from parallel evaluation.
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass, fields, is_dataclass
from threading import RLock
from typing import Any

from the_alchemiser.strategy.dsl.ast import (
    RSI,
    Asset,
    ASTNode,
    CumulativeReturn,
    CurrentPrice,
    Filter,
    GreaterThan,
    Group,
    If,
    LessThan,
    MovingAveragePrice,
    MovingAverageReturn,
    NumberLiteral,
    SelectBottom,
    SelectTop,
    StdevReturn,
    Strategy,
    Symbol,
    WeightEqual,
    WeightInverseVolatility,
    WeightSpecified,
)

# Statistics for telemetry
_memo_stats = {
    "requests": 0,
    "hits": 0,
    "misses": 0,
    "evictions": 0,
}


@dataclass(frozen=True)
class EvalContext:
    """Evaluation context that captures all state affecting node evaluation results.

    This must include all dimensions that can change evaluation results:
    - Time bucket (trading day or timestamp)
    - Universe fingerprint (what symbols are available)
    - Environment parameters (lookback windows, etc.)
    """

    time_bucket: str  # e.g., "2024-01-15" or timestamp
    universe_fingerprint: str  # hash of sorted symbol list
    env_fingerprint: str  # hash of environment parameters

    def cache_key(self) -> tuple[str, str, str]:
        """Get a hashable cache key for this context."""
        return (self.time_bucket, self.universe_fingerprint, self.env_fingerprint)


def create_eval_context(
    timestamp: str | None = None,
    symbols: list[str] | None = None,
    env_params: dict[str, Any] | None = None,
) -> EvalContext:
    """Create an evaluation context from current state.

    Args:
        timestamp: Current evaluation timestamp (defaults to current time bucket)
        symbols: Available symbols (defaults to empty)
        env_params: Environment parameters like windows, thresholds, etc.

    Returns:
        Evaluation context for cache keying

    """
    # Default time bucket to current trading day
    if timestamp is None:
        # Use current date as time bucket for now
        # In production, this should be the actual market time
        from datetime import UTC, datetime

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d")

    # Create universe fingerprint from sorted symbols
    if symbols is None:
        symbols = []
    universe_key = ",".join(sorted(symbols))
    universe_fingerprint = hashlib.blake2b(universe_key.encode()).hexdigest()[:16]

    # Create environment fingerprint from parameters
    if env_params is None:
        env_params = {}

    # Sort parameters for stable fingerprinting
    env_items = sorted(env_params.items())
    env_key = str(env_items)
    env_fingerprint = hashlib.blake2b(env_key.encode()).hexdigest()[:16]

    return EvalContext(
        time_bucket=timestamp,
        universe_fingerprint=universe_fingerprint,
        env_fingerprint=env_fingerprint,
    )


class NodeEvaluationCache:
    """Thread-safe bounded LRU cache for pure node evaluation results."""

    def __init__(self, maxsize: int = 100_000) -> None:
        self._maxsize = maxsize
        self._store: OrderedDict[tuple[str, tuple[str, str, str]], Any] = OrderedDict()
        self._lock = RLock()

    def get(self, node_id: str, context: EvalContext) -> tuple[bool, Any]:
        """Retrieve cached evaluation result for a node.

        Args:
            node_id: Unique identifier for the DSL node
            context: Evaluation context containing cache key components

        Returns:
            Tuple of (cache_hit: bool, result: Any). If cache_hit is False,
            result will be None.
        """
        global _memo_stats
        cache_key = (node_id, context.cache_key())
        with self._lock:
            _memo_stats["requests"] += 1
            if cache_key in self._store:
                _memo_stats["hits"] += 1
                # LRU promotion
                self._store.move_to_end(cache_key)
                return True, self._store[cache_key]
            _memo_stats["misses"] += 1
            return False, None

    def set(self, node_id: str, context: EvalContext, result: Any) -> None:
        """Store evaluation result in cache with LRU eviction.

        Args:
            node_id: Unique identifier for the DSL node
            context: Evaluation context containing cache key components  
            result: Evaluation result to cache
        """
        cache_key = (node_id, context.cache_key())
        with self._lock:
            self._store[cache_key] = result
            self._store.move_to_end(cache_key)
            if len(self._store) > self._maxsize:
                # Evict oldest
                self._store.popitem(last=False)
                _memo_stats["evictions"] += 1

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()

    def get_info(self) -> dict[str, Any]:
        """Get cache utilization information.

        Returns:
            Dictionary containing cache size, maximum size, and utilization percentage.
        """
        with self._lock:
            size = len(self._store)
            return {
                "size": size,
                "maxsize": self._maxsize,
                "utilization": size / self._maxsize if self._maxsize > 0 else 0.0,
            }


def get_memo_stats() -> dict[str, Any]:
    """Get memoisation statistics for telemetry.

    Returns:
        Dictionary with memoisation metrics including hit rates

    """
    total = _memo_stats["requests"]
    hits = _memo_stats["hits"]
    hit_rate = (hits / total) if total > 0 else 0.0

    return {
        "memo_requests": total,
        "memo_hits": hits,
        "memo_misses": _memo_stats["misses"],
        "memo_hit_rate": hit_rate,
        "memo_evictions": _memo_stats["evictions"],
    }


def clear_memo_stats() -> None:
    """Clear memoisation statistics (for testing)."""
    global _memo_stats
    _memo_stats = {
        "requests": 0,
        "hits": 0,
        "misses": 0,
        "evictions": 0,
    }


def is_pure_node(node: ASTNode) -> bool:
    """Check if a node represents a pure computation.

    Pure nodes are those whose evaluation depends only on their structure
    and the evaluation context, with no side effects or non-deterministic
    behavior. These are safe to memoize.

    Args:
        node: AST node to check

    Returns:
        True if the node is pure and safe to memoize

    """
    # Most DSL nodes are pure - they depend only on market data and parameters
    pure_node_types = (
        NumberLiteral,
        Symbol,
        GreaterThan,
        LessThan,
        If,
        RSI,
        MovingAveragePrice,
        MovingAverageReturn,
        CumulativeReturn,
        CurrentPrice,
        StdevReturn,
        Asset,
        Group,
        WeightEqual,
        WeightSpecified,
        WeightInverseVolatility,
        Filter,
        SelectTop,
        SelectBottom,
        Strategy,
    )

    return isinstance(node, pure_node_types)


# -------- Node ID helpers (for memo without parser interning) ---------


def _structural_key(node: ASTNode) -> tuple[Any, ...]:
    """Produce a structural tuple key for an AST node.

    Excludes non-init fields (like auto-assigned IDs) so that equivalent
    structures map to identical keys. Non-dataclass objects are represented
    by a RAW tuple with their repr.
    """
    parts: list[Any] = [node.__class__.__name__]
    for f in fields(node):
        if f.init:
            parts.append(_stable_value(getattr(node, f.name)))
    return tuple(parts)


def _stable_value(value: Any) -> Any:
    """Return a stable, hashable representation for arbitrary values.

    Child AST nodes are reduced to their structural key; collections are
    converted recursively to tuples with tagged prefixes to avoid collisions.
    """
    if is_dataclass(value):
        return ("NODE", _structural_key(value))  # type: ignore[arg-type]
    if isinstance(value, list):
        return ("LIST", tuple(_stable_value(v) for v in value))
    if isinstance(value, tuple):
        return ("TUPLE", tuple(_stable_value(v) for v in value))
    if isinstance(value, dict):
        return ("DICT", tuple(sorted((k, _stable_value(v)) for k, v in value.items())))
    return ("PRIM", value)


def ensure_node_id(node: ASTNode) -> None:
    """Assign a stable node_id if missing (for memoisation without interning)."""
    if getattr(node, "node_id", None) is not None:
        return
    key = str(_structural_key(node)).encode()
    node_id = hashlib.blake2b(key, digest_size=16).hexdigest()
    # Bypass frozen dataclass
    object.__setattr__(node, "node_id", node_id)
