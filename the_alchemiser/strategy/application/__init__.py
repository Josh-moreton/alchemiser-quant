"""Business Unit: strategy & signal generation; Status: current.

Strategy application layer.

Contains application services and workflows for strategy execution,
signal processing, and strategy orchestration.
"""

from __future__ import annotations

from .contracts import SignalContractV1, signal_from_domain

__all__ = [
    "SignalContractV1",
    "signal_from_domain",
]
