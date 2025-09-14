"""Business Unit: utilities; Status: current.

Email utilities module - REFACTORED.

This module now imports from the new modular email system for backward compatibility.
The email functionality has been split into separate modules:

- email/config.py: Email configuration management
- email/client.py: SMTP client operations
- email/templates/: Template builders for different content types
  - base.py: Base template structure
  - portfolio.py: Portfolio content builder
  - performance.py: Performance metrics builder
  - signals.py: Strategy signals builder
  - trading_report.py: Trading report templates
  - multi_strategy.py: Multi-strategy report templates
  - error_report.py: Error notification templates

For new code, import directly from the notifications module:
    from the_alchemiser.shared.notifications import send_email_notification
    from the_alchemiser.shared.notifications.templates import EmailTemplates

This file maintains backward compatibility for existing imports.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO

# Import DTOs for type-safe email rendering
from the_alchemiser.shared.value_objects.core_types import AccountInfo, EnrichedAccountInfo

# Import all functions from the new modular structure
from .client import EmailClient, send_email_notification
from .config import get_email_config, is_neutral_mode_enabled
from .templates import (
    EmailTemplates,
    build_error_email_html,
    build_multi_strategy_email_html,
    build_trading_report_html,
)
from .templates.base import BaseEmailTemplate
from .templates.performance import PerformanceBuilder

# Import specific template builders for advanced usage
from .templates.portfolio import PortfolioBuilder
from .templates.signals import SignalsBuilder


# Backward compatibility aliases for internal functions that might still be referenced
def _build_portfolio_display(
    result: ExecutionResultDTO | MultiStrategyExecutionResultDTO | dict[str, Any],
) -> str:
    """Backward compatibility function supporting both ExecutionResultDTO and MultiStrategy DTO."""
    return PortfolioBuilder.build_portfolio_allocation(result)


def _build_closed_positions_pnl_email_html(account_info: AccountInfo | EnrichedAccountInfo) -> str:
    """Backward compatibility function."""
    return PortfolioBuilder.build_closed_positions_pnl(account_info)


def _build_technical_indicators_email_html(
    strategy_signals: dict[Any, Any],
) -> str:
    """Backward compatibility function."""
    return SignalsBuilder.build_technical_indicators(strategy_signals)


def _build_detailed_strategy_signals_email_html(
    strategy_signals: dict[Any, Any], strategy_summary: dict[str, Any]
) -> str:
    """Backward compatibility function."""
    return SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)


def _build_enhanced_trading_summary_email_html(
    trading_summary: dict[str, Any],
) -> str:
    """Backward compatibility function."""
    return PerformanceBuilder.build_trading_summary(trading_summary)


def _build_enhanced_portfolio_email_html(
    result: ExecutionResultDTO | MultiStrategyExecutionResultDTO | dict[str, Any],
) -> str:
    """Backward compatibility function."""
    return PortfolioBuilder.build_portfolio_allocation(result)


# Export the main public API
__all__ = [
    "BaseEmailTemplate",
    "EmailClient",
    "EmailTemplates",
    "PerformanceBuilder",
    "PortfolioBuilder",
    "SignalsBuilder",
    "build_error_email_html",
    "build_multi_strategy_email_html",
    "build_trading_report_html",
    "get_email_config",
    "is_neutral_mode_enabled",
    "send_email_notification",
]
