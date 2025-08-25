"""
Evaluation context and caching system for DSL evaluator memoisation.

Provides evaluation context fingerprinting and bounded LRU caching
for pure expression evaluation to eliminate redundant computation.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Hashable

from the_alchemiser.domain.dsl.ast import ASTNode

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
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d")
    
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
    """Bounded LRU cache for node evaluation results.
    
    Caches pure node evaluation results keyed by (node_id, eval_context)
    to eliminate redundant computation across identical sub-expressions.
    """
    
    def __init__(self, maxsize: int = 100_000) -> None:
        """Initialize cache with bounded size.
        
        Args:
            maxsize: Maximum number of cached entries
        """
        self._maxsize = maxsize
        # Create the actual cache function with LRU
        self._cache_func = lru_cache(maxsize=maxsize)(self._dummy_func)
        
    def _dummy_func(self, cache_key: Hashable) -> Any:
        """Dummy function for LRU cache - not used directly."""
        pass
    
    def get(self, node_id: str, context: EvalContext) -> tuple[bool, Any]:
        """Get cached result for a node evaluation.
        
        Args:
            node_id: Unique identifier for the AST node
            context: Evaluation context
            
        Returns:
            Tuple of (found, result) where found indicates if result was cached
        """
        global _memo_stats
        _memo_stats["requests"] += 1
        
        cache_key = (node_id, context.cache_key())
        
        # Check if we have this in the LRU cache
        try:
            # Use the cache_info to check if this key exists
            # We'll store results in a separate dict and use LRU for key tracking
            result = self._cache_func.cache_info()  # This just tracks access patterns
            
            # For now, implement a simple dict-based cache
            # In production, this should be more sophisticated
            if not hasattr(self, '_results'):
                self._results = {}
                
            if cache_key in self._results:
                _memo_stats["hits"] += 1
                # Update LRU by calling the dummy function
                self._cache_func(cache_key)
                return True, self._results[cache_key]
            else:
                _memo_stats["misses"] += 1
                return False, None
                
        except Exception:
            _memo_stats["misses"] += 1
            return False, None
    
    def set(self, node_id: str, context: EvalContext, result: Any) -> None:
        """Cache a node evaluation result.
        
        Args:
            node_id: Unique identifier for the AST node
            context: Evaluation context
            result: Evaluation result to cache
        """
        cache_key = (node_id, context.cache_key())
        
        if not hasattr(self, '_results'):
            self._results = {}
            
        # Store the result
        self._results[cache_key] = result
        
        # Update LRU tracking
        self._cache_func(cache_key)
        
        # Handle evictions if we exceed maxsize
        if len(self._results) > self._maxsize:
            # Simple eviction - remove oldest entries
            # In production, this should use proper LRU eviction
            keys_to_remove = list(self._results.keys())[:-self._maxsize]
            for key in keys_to_remove:
                del self._results[key]
                _memo_stats["evictions"] += 1
    
    def clear(self) -> None:
        """Clear all cached results."""
        if hasattr(self, '_results'):
            self._results.clear()
        self._cache_func.cache_clear()
    
    def get_info(self) -> dict[str, Any]:
        """Get cache statistics."""
        size = len(getattr(self, '_results', {}))
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
    from the_alchemiser.domain.dsl.ast import (
        Asset, CumulativeReturn, CurrentPrice, Filter, Group, GreaterThan,
        If, LessThan, MovingAveragePrice, MovingAverageReturn, NumberLiteral,
        RSI, SelectBottom, SelectTop, StdevReturn, Strategy, Symbol,
        WeightEqual, WeightInverseVolatility, WeightSpecified
    )
    
    # Most DSL nodes are pure - they depend only on market data and parameters
    pure_node_types = (
        NumberLiteral, Symbol, GreaterThan, LessThan, If,
        RSI, MovingAveragePrice, MovingAverageReturn, CumulativeReturn,
        CurrentPrice, StdevReturn, Asset, Group, WeightEqual, WeightSpecified,
        WeightInverseVolatility, Filter, SelectTop, SelectBottom, Strategy
    )
    
    return isinstance(node, pure_node_types)