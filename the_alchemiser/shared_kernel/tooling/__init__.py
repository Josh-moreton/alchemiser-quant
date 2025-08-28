"""Business Unit: utilities (shared kernel / cross-cutting) | Status: current.

Shared tooling utilities.
"""

from .retry import retry_with_backoff

__all__ = ["retry_with_backoff"]
