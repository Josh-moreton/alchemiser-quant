"""Business Unit: execution_v2 | Status: current.

Broker adapters and integrations for execution.

This package provides broker-specific adapters and utilities for trading
operations. Previously located in shared/brokers, moved here as these are
execution-specific concerns rather than shared utilities.

Contains:
- AlpacaManager: Primary broker integration for Alpaca trading
- alpaca_utils: Utility functions for Alpaca integration
"""

from __future__ import annotations

from .alpaca_manager import AlpacaManager, create_alpaca_manager

__all__ = ["AlpacaManager", "create_alpaca_manager"]
