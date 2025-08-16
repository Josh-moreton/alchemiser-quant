"""Compatibility wrapper for TradingEngine.

This module now simply re-exports :class:`TradingEngine` from
``the_alchemiser.application.engine_service`` so existing imports continue to
work during the refactor.
"""

from the_alchemiser.application.engine_service import TradingEngine

__all__ = ["TradingEngine"]
