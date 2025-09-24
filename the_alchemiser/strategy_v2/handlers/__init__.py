#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Event handlers for strategy signal generation.

Provides event-driven handlers for processing strategy-related events
in the event-driven architecture.
"""

from __future__ import annotations

from .signal_generation_handler import SignalGenerationHandler

__all__ = [
    "SignalGenerationHandler",
]
