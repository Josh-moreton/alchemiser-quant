"""Compatibility wrapper for :class:`TradingEngine`.

This module re-exports :class:`TradingEngine` from
``the_alchemiser.application.trading.engine_service`` so existing imports
continue to work during the refactor.
"""

from .engine_service import TradingEngine

__all__ = ["TradingEngine"]
