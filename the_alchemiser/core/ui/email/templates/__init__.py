"""Email templates module for The Alchemiser.

This module provides email template builders with clean separation of concerns.
Each template type has its own dedicated module for better organization.

Usage:
    from the_alchemiser.core.ui.email.templates import EmailTemplates
    
    # Build a trading report
    html = EmailTemplates.build_trading_report(...)
    
    # Build a neutral trading report
    html = EmailTemplates.build_trading_report_neutral(...)
"""

# Import the specialized builders
from .trading_report import TradingReportBuilder
from .multi_strategy import MultiStrategyReportBuilder
from .error_report import ErrorReportBuilder

# Import content builders for advanced usage
from .base import BaseEmailTemplate
from .portfolio import PortfolioBuilder
from .performance import PerformanceBuilder
from .signals import SignalsBuilder


class EmailTemplates:
    """Main email template facade that delegates to specialized builders."""
    
    # Trading reports
    @staticmethod
    def build_trading_report(*args, **kwargs):
        """Build a regular trading report email."""
        return TradingReportBuilder.build_regular_report(*args, **kwargs)
    
    @staticmethod
    def build_trading_report_neutral(*args, **kwargs):
        """Build a neutral trading report email without financial values."""
        return TradingReportBuilder.build_neutral_report(*args, **kwargs)
    
    # Multi-strategy reports
    @staticmethod
    def build_multi_strategy_report(*args, **kwargs):
        """Build a multi-strategy report email."""
        return MultiStrategyReportBuilder.build_multi_strategy_report(*args, **kwargs)
    
    # Error reports
    @staticmethod
    def build_error_report(*args, **kwargs):
        """Build an error notification email."""
        return ErrorReportBuilder.build_error_report(*args, **kwargs)


# Backward compatibility functions
def build_trading_report_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_trading_report_html."""
    return EmailTemplates.build_trading_report(*args, **kwargs)

def build_multi_strategy_email_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_multi_strategy_email_html."""
    return EmailTemplates.build_multi_strategy_report(*args, **kwargs)

def build_error_email_html(*args, **kwargs) -> str:
    """Backward compatibility function for build_error_email_html."""
    return EmailTemplates.build_error_report(*args, **kwargs)
