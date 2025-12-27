"""Business Unit: aggregator_v2 | Status: current.

Signal Aggregator Lambda module for multi-node signal aggregation.

This module aggregates partial signals from parallel Strategy Lambda
invocations into a single consolidated SignalGenerated event that
triggers Portfolio Lambda (preserving the existing workflow).
"""

from __future__ import annotations

__all__: list[str] = []
