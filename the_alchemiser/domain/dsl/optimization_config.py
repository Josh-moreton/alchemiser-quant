"""
Configuration system for DSL optimization features.

Provides environment variable and programmatic configuration for
enabling/disabling AST interning, evaluator memoisation, and parallel execution.
"""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class DSLOptimizationConfig:
    """Configuration for DSL optimization features."""
    
    # AST Interning (Structural Sharing)
    enable_interning: bool = False
    
    # Evaluator Memoisation
    enable_memoisation: bool = False
    memo_cache_maxsize: int = 100_000
    
    # Parallel Evaluation
    enable_parallel: bool = False
    parallel_mode: str = "threads"  # "threads" or "processes"
    parallel_max_workers: int | None = None
    
    @classmethod
    def from_environment(cls) -> "DSLOptimizationConfig":
        """Create configuration from environment variables.
        
        Environment variables:
        - ALCH_DSL_CSE: Enable AST interning/canonical shared expressions
        - ALCH_DSL_MEMO: Enable evaluator memoisation
        - ALCH_DSL_CACHE_MAXSIZE: Maximum cache size for memoisation
        - ALCH_DSL_PARALLEL: Parallel execution mode ("threads", "processes", "off")
        - ALCH_DSL_WORKERS: Maximum number of parallel workers
        
        Returns:
            Configuration instance with environment settings
        """
        return cls(
            enable_interning=_env_bool("ALCH_DSL_CSE", False),
            enable_memoisation=_env_bool("ALCH_DSL_MEMO", False),
            memo_cache_maxsize=_env_int("ALCH_DSL_CACHE_MAXSIZE", 100_000),
            enable_parallel=_env_parallel_enabled("ALCH_DSL_PARALLEL", "off"),
            parallel_mode=_env_parallel_mode("ALCH_DSL_PARALLEL", "threads"),
            parallel_max_workers=_env_int("ALCH_DSL_WORKERS", None),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for logging/telemetry."""
        return {
            "interning_enabled": self.enable_interning,
            "memoisation_enabled": self.enable_memoisation,
            "memo_cache_maxsize": self.memo_cache_maxsize,
            "parallel_enabled": self.enable_parallel,
            "parallel_mode": self.parallel_mode,
            "parallel_max_workers": self.parallel_max_workers,
        }


def _env_bool(var_name: str, default: bool) -> bool:
    """Get boolean value from environment variable."""
    value = os.environ.get(var_name, "").lower()
    if value in ("1", "true", "yes", "on", "enabled"):
        return True
    elif value in ("0", "false", "no", "off", "disabled"):
        return False
    else:
        return default


def _env_int(var_name: str, default: int | None) -> int | None:
    """Get integer value from environment variable."""
    value = os.environ.get(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_parallel_enabled(var_name: str, default: str) -> bool:
    """Check if parallel execution is enabled from environment."""
    value = os.environ.get(var_name, default).lower()
    return value in ("threads", "processes")


def _env_parallel_mode(var_name: str, default: str) -> str:
    """Get parallel execution mode from environment."""
    value = os.environ.get(var_name, default).lower()
    if value in ("threads", "processes"):
        return value
    return "threads"  # default to threads if invalid value


# Global default configuration instance
_default_config = DSLOptimizationConfig()


def get_default_config() -> DSLOptimizationConfig:
    """Get the default configuration instance."""
    return _default_config


def set_default_config(config: DSLOptimizationConfig) -> None:
    """Set the default configuration instance."""
    global _default_config
    _default_config = config


def configure_from_environment() -> DSLOptimizationConfig:
    """Configure optimization from environment variables and set as default.
    
    Returns:
        The configured instance (also set as default)
    """
    config = DSLOptimizationConfig.from_environment()
    set_default_config(config)
    return config


def get_optimization_stats() -> dict[str, Any]:
    """Get comprehensive optimization statistics.
    
    Combines statistics from interning, memoisation, and parallel execution
    to provide a complete picture of optimization effectiveness.
    
    Returns:
        Dictionary with all optimization metrics
    """
    stats = {"config": get_default_config().to_dict()}
    
    # Add interning stats if available
    try:
        from the_alchemiser.domain.dsl.interning import get_intern_stats
        stats["interning"] = get_intern_stats()
    except ImportError:
        pass
    
    # Add memoisation stats if available
    try:
        from the_alchemiser.domain.dsl.evaluator_cache import get_memo_stats
        stats["memoisation"] = get_memo_stats()
    except ImportError:
        pass
    
    return stats