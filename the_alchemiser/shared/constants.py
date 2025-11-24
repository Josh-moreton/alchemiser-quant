"""Business Unit: shared | Status: current.

Shared constants for The Alchemiser Quantitative Trading System.

This module centralizes frequently used string literals and constants
to improve maintainability and reduce the risk of inconsistency.

All financial constants use Decimal for precision. Validation constants
use immutable types (frozenset, tuple) to prevent accidental modification.

Type Annotations:
    All module-level constants include explicit type annotations for
    clarity and type-checker support (mypy, pyright).
"""

from __future__ import annotations

from decimal import Decimal

# Application branding
APPLICATION_NAME: str = "The Alchemiser"

# Date and time formats
DEFAULT_DATE_FORMAT: str = "%Y/%m/%d"
"""Default date format string (YYYY/MM/DD)."""

UTC_TIMEZONE_SUFFIX: str = "+00:00"
"""UTC timezone offset suffix for ISO 8601 timestamps."""

# UI messages for trading operations
REBALANCE_PLAN_GENERATED: str = "📋 Rebalance plan generated:"
"""Message displayed when a rebalance plan is successfully generated."""

NO_TRADES_REQUIRED: str = "📋 No trades required (portfolio balanced)"
"""Message displayed when portfolio is already balanced."""

# Account value logging messages
ACCOUNT_VALUE_LOGGING_DISABLED: str = "Account value logging is disabled"
"""Message displayed when account value logging is disabled in config."""

# Module identifiers
CLI_DEPLOY_COMPONENT: str = "cli.deploy"
"""Identifier for CLI deployment component in structured logging."""

DSL_ENGINE_MODULE: str = "strategy_v2.engines.dsl"
"""Module identifier for DSL strategy engine in structured logging."""

EXECUTION_HANDLERS_MODULE: str = "execution_v2.handlers"
"""Module identifier for execution handlers in structured logging."""

# Event schema descriptions
EVENT_SCHEMA_VERSION_DESCRIPTION: str = "Event schema version"
"""Description text for event schema version field in Pydantic models."""

EVENT_TYPE_DESCRIPTION: str = "Type of event"
"""Description text for event type field in Pydantic models."""

RECIPIENT_OVERRIDE_DESCRIPTION: str = "Optional recipient email override"
"""Description text for recipient override field in notification events."""

# DTO schema descriptions
DTO_SCHEMA_VERSION_DESCRIPTION: str = "DTO schema version"
"""Description text for DTO schema version field in Pydantic models."""

# UI/CLI styling constants
STYLE_BOLD_CYAN: str = "bold cyan"
"""Rich text style: bold cyan color."""

STYLE_ITALIC: str = "italic"
"""Rich text style: italic formatting."""

STYLE_BOLD_BLUE: str = "bold blue"
"""Rich text style: bold blue color."""

STYLE_BOLD_GREEN: str = "bold green"
"""Rich text style: bold green color."""

STYLE_BOLD_RED: str = "bold red"
"""Rich text style: bold red color (errors/warnings)."""

STYLE_BOLD_YELLOW: str = "bold yellow"
"""Rich text style: bold yellow color (warnings)."""

STYLE_BOLD_MAGENTA: str = "bold magenta"
"""Rich text style: bold magenta color."""

PROGRESS_DESCRIPTION_FORMAT: str = "[progress.description]{task.description}"
"""Rich progress bar description format string."""

# Business logic constants
DECIMAL_ZERO: Decimal = Decimal("0")
"""Zero value as Decimal for financial calculations (exact precision)."""

MIN_TRADE_AMOUNT_USD: Decimal = Decimal("5")
"""Minimum trade amount in USD to avoid dust trades and broker rejection."""

MINIMUM_PRICE: Decimal = Decimal("0.01")
"""Minimum trading price (1 cent) for validation and sanity checks."""

# Order size safety limits - prevents catastrophic bugs from deploying excessive capital
MAX_SINGLE_ORDER_USD: Decimal = Decimal("100000")
"""Maximum single order value in USD. Orders exceeding this are rejected as a safety measure."""

MAX_ORDER_PORTFOLIO_PCT: Decimal = Decimal("0.25")
"""Maximum single order as percentage of portfolio (0.25 = 25%). Safety limit to prevent
a single trade from representing an outsized portfolio concentration."""

MAX_DAILY_TRADE_VALUE_USD: Decimal = Decimal("500000")
"""Maximum total trade value per day in USD. Circuit breaker to prevent runaway execution."""

# Validation constants (immutable collections)
CONFIDENCE_RANGE: tuple[Decimal, Decimal] = (Decimal("0"), Decimal("1"))
"""Valid range for confidence values: [0.0, 1.0] inclusive."""

PERCENTAGE_RANGE: tuple[Decimal, Decimal] = (Decimal("0"), Decimal("1"))
"""Valid range for percentage values: [0.0, 1.0] where 1.0 = 100%."""

SIGNAL_ACTIONS: frozenset[str] = frozenset({"BUY", "SELL", "HOLD"})
"""Valid signal action types (immutable set)."""

ALERT_SEVERITIES: frozenset[str] = frozenset({"INFO", "WARNING", "ERROR"})
"""Valid alert severity levels (immutable set)."""

ORDER_TYPES: frozenset[str] = frozenset({"market", "limit"})
"""Valid order types for trading (immutable set)."""

ORDER_SIDES: frozenset[str] = frozenset({"buy", "sell"})
"""Valid order sides for trading (immutable set)."""

# AWS configuration
DEFAULT_AWS_REGION: str = "eu-west-2"
"""Default AWS region for Lambda deployment and AWS service calls."""

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
    "DTO_SCHEMA_VERSION_DESCRIPTION",
    "EVENT_SCHEMA_VERSION_DESCRIPTION",
    "EVENT_TYPE_DESCRIPTION",
    "EXECUTION_HANDLERS_MODULE",
    "MAX_DAILY_TRADE_VALUE_USD",
    "MAX_ORDER_PORTFOLIO_PCT",
    "MAX_SINGLE_ORDER_USD",
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
