"""Core trading components for The Alchemiser Quantitative Trading System.

This package contains the fundamental building blocks for the trading system,
including data providers, trading strategies, configuration management,
technical indicators, and utility functions.

Modules:
    config: Configuration management and settings
    data: Market data providers and real-time data streaming
    trading: Strategy engines and portfolio management
    indicators: Technical analysis indicators
    utils: Common utilities and helper functions
    secrets: Secure credential management
    logging: Centralized logging utilities
    ui: User interface components and formatters
    alerts: Alert and notification systems

Exported Components:
    ActionType: Enumeration of trading actions (BUY, SELL, HOLD)
"""

from typing import Any

from the_alchemiser.core.utils.common import ActionType

__all__ = ["ActionType"]
