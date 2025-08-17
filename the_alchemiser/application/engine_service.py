"""Compatibility wrapper for TradingEngine.

Re-exports :class:`TradingEngine` from
``the_alchemiser.application.trading.engine_service`` so existing imports remain
valid during the refactor.
"""

from the_alchemiser.application.trading.engine_service import TradingEngine

__all__ = ["TradingEngine"]
