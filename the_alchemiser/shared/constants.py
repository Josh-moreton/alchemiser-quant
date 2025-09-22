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

# Module identifiers
CLI_DEPLOY_COMPONENT = "cli.deploy"
DSL_ENGINE_MODULE = "strategy_v2.engines.dsl"

# Event schema descriptions
EVENT_SCHEMA_VERSION_DESCRIPTION = "Event schema version"
EVENT_TYPE_DESCRIPTION = "Type of event"

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

# Validation constants
CONFIDENCE_RANGE = (Decimal("0"), Decimal("1"))
PERCENTAGE_RANGE = (Decimal("0"), Decimal("1"))
SIGNAL_ACTIONS = {"BUY", "SELL", "HOLD"}
ALERT_SEVERITIES = {"INFO", "WARNING", "ERROR"}
ORDER_TYPES = {"market", "limit"}
ORDER_SIDES = {"buy", "sell"}

# AWS configuration
DEFAULT_AWS_REGION = "eu-west-2"