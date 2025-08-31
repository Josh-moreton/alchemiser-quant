"""Business Unit: strategy & signal generation; Status: current.

Strategy application contracts for cross-context communication.

This package provides versioned application-layer contracts that enable
clean communication from Strategy context to other bounded contexts without
exposing internal domain objects.
"""

from __future__ import annotations

from .signal_contract_v1 import SignalContractV1, signal_from_domain

__all__ = [
    "SignalContractV1",
    "signal_from_domain",
]
