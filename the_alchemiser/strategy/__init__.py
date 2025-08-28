"""Business Unit: strategy & signal generation; Status: current.

Strategy bounded context package.

This bounded context is responsible for:
- Strategy signal generation and indicators
- Multi-strategy orchestration and scoring
- Market regime detection and classification
- Pure strategy calculations and policies
"""

from __future__ import annotations

__all__ = [
    "application",
    "domain", 
    "infrastructure",
    "interfaces",
]