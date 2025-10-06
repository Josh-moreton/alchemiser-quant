"""Business Unit: shared | Status: current.

Shared constants for The Alchemiser Quantitative Trading System.

This module centralizes frequently used string literals and constants
to improve maintainability and reduce the risk of inconsistency.
"""

from __future__ import annotations

from decimal import Decimal

# Application branding
APPLICATION_NAME = "The Alchemiser"

# Date and time formats
DEFAULT_DATE_FORMAT = "%Y/%m/%d"
UTC_TIMEZONE_SUFFIX = "+00:00"

# UI messages for trading operations
REBALANCE_PLAN_GENERATED = "📋 Rebalance plan generated:"
NO_TRADES_REQUIRED = "📋 No trades required (portfolio balanced)"

# Account value logging messages
ACCOUNT_VALUE_LOGGING_DISABLED = "Account value logging is disabled"

# Module identifiers
CLI_DEPLOY_COMPONENT = "cli.deploy"
DSL_ENGINE_MODULE = "strategy_v2.engines.dsl"
EXECUTION_HANDLERS_MODULE = "execution_v2.handlers"

# Event schema descriptions
EVENT_SCHEMA_VERSION_DESCRIPTION = "Event schema version"
EVENT_TYPE_DESCRIPTION = "Type of event"
RECIPIENT_OVERRIDE_DESCRIPTION = "Optional recipient email override"

# UI/CLI styling constants
STYLE_BOLD_CYAN = "bold cyan"
STYLE_ITALIC = "italic"
STYLE_BOLD_BLUE = "bold blue"
STYLE_BOLD_GREEN = "bold green"
STYLE_BOLD_RED = "bold red"
STYLE_BOLD_YELLOW = "bold yellow"
STYLE_BOLD_MAGENTA = "bold magenta"
PROGRESS_DESCRIPTION_FORMAT = "[progress.description]{task.description}"

# Business logic constants
DECIMAL_ZERO = Decimal("0")
MIN_TRADE_AMOUNT_USD = Decimal("5")
MINIMUM_PRICE = Decimal("0.01")  # Minimum trading price (1 cent)

# Validation constants
CONFIDENCE_RANGE = (Decimal("0"), Decimal("1"))
PERCENTAGE_RANGE = (Decimal("0"), Decimal("1"))
SIGNAL_ACTIONS = {"BUY", "SELL", "HOLD"}
ALERT_SEVERITIES = {"INFO", "WARNING", "ERROR"}
ORDER_TYPES = {"market", "limit"}
ORDER_SIDES = {"buy", "sell"}

# AWS configuration
DEFAULT_AWS_REGION = "eu-west-2"

# Public API
__all__ = [
    "ACCOUNT_VALUE_LOGGING_DISABLED",
    "ALERT_SEVERITIES",
    "APPLICATION_NAME",
    "CLI_DEPLOY_COMPONENT",
    "CONFIDENCE_RANGE",
    "DECIMAL_ZERO",
    "DEFAULT_AWS_REGION",
    "DEFAULT_DATE_FORMAT",
    "DSL_ENGINE_MODULE",
    "EVENT_SCHEMA_VERSION_DESCRIPTION",
    "EVENT_TYPE_DESCRIPTION",
    "EXECUTION_HANDLERS_MODULE",
    "MINIMUM_PRICE",
    "MIN_TRADE_AMOUNT_USD",
    "NO_TRADES_REQUIRED",
    "ORDER_SIDES",
    "ORDER_TYPES",
    "PERCENTAGE_RANGE",
    "PROGRESS_DESCRIPTION_FORMAT",
    "REBALANCE_PLAN_GENERATED",
    "RECIPIENT_OVERRIDE_DESCRIPTION",
    "SIGNAL_ACTIONS",
    "STYLE_BOLD_BLUE",
    "STYLE_BOLD_CYAN",
    "STYLE_BOLD_GREEN",
    "STYLE_BOLD_MAGENTA",
    "STYLE_BOLD_RED",
    "STYLE_BOLD_YELLOW",
    "STYLE_ITALIC",
    "UTC_TIMEZONE_SUFFIX",
]
