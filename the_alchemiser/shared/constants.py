"""Business Unit: shared | Status: current.

Shared constants for The Alchemiser Quantitative Trading System.

This module centralizes frequently used string literals and constants
to improve maintainability and reduce the risk of inconsistency.
"""

from __future__ import annotations

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