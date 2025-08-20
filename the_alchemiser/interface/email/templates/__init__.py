"""Email templates module for The Alchemiser.

This module provides email template builders with clean separation of concerns.
Each template type has its own dedicated module for better organization.

Usage:
    from the_alchemiser.interface.email.templates import EmailTemplates

    # Build a neutral multi-strategy report
    html = EmailTemplates.build_multi_strategy_report_neutral(...)

    # Build an error report
    html = EmailTemplates.build_error_report(...)
"""

from typing import Any

# Import the specialized builders
from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO

from .base import BaseEmailTemplate
from .error_report import ErrorReportBuilder
from .multi_strategy import MultiStrategyReportBuilder
from .performance import PerformanceBuilder
from .portfolio import PortfolioBuilder
from .signals import SignalsBuilder

__all__ = [
    "BaseEmailTemplate",
    "ErrorReportBuilder",
    "MultiStrategyReportBuilder",
    "PerformanceBuilder",
    "PortfolioBuilder",
    "SignalsBuilder",
    "EmailTemplates",
]


class EmailTemplates:
    """Main email template facade that delegates to specialized builders."""

    # Multi-strategy reports (neutral mode only)
    @staticmethod
    def build_multi_strategy_report_neutral(
        result: MultiStrategyExecutionResultDTO | Any, mode: str
    ) -> str:
        """Build a neutral multi-strategy report email without financial values."""
        return MultiStrategyReportBuilder.build_multi_strategy_report_neutral(result, mode)

    # Error reports
    @staticmethod
    def build_error_report(*args: Any, **kwargs: Any) -> str:
        """Build an error notification email."""
        return ErrorReportBuilder.build_error_report(*args, **kwargs)


# Backward compatibility functions
def build_trading_report_html(*args: Any, **kwargs: Any) -> str:
    """Backward compatibility function for build_trading_report_html."""
    return str(EmailTemplates.build_multi_strategy_report_neutral(*args, **kwargs))


def build_multi_strategy_email_html(*args: Any, **kwargs: Any) -> str:
    """Backward compatibility function for build_multi_strategy_email_html."""
    return str(EmailTemplates.build_multi_strategy_report_neutral(*args, **kwargs))


def build_multi_strategy_email_html_neutral(*args: Any, **kwargs: Any) -> str:
    """Backward compatibility function for build_multi_strategy_email_html_neutral."""
    return str(EmailTemplates.build_multi_strategy_report_neutral(*args, **kwargs))


def build_error_email_html(*args: Any, **kwargs: Any) -> str:
    """Backward compatibility function for build_error_email_html."""
    return str(EmailTemplates.build_error_report(*args, **kwargs))
