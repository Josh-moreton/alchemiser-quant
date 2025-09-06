"""Business Unit: shared | Status: current

Broker abstractions and utilities.

This package provides broker-agnostic interfaces and utilities that allow
the rest of the system to work with trading operations without being tied
to specific broker implementations.

The AlpacaManager was moved here from execution module to resolve
architectural boundary violations.
"""

from __future__ import annotations

from .alpaca_manager import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
