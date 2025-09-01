"""Core execution functionality.

Contains the main execution managers and orchestrators.
"""

from __future__ import annotations

__all__: list[str] = [
    "ExecutionManager", 
    "CanonicalOrderExecutor"
]

from .executor import ExecutionManager
from .canonical_executor import CanonicalOrderExecutor