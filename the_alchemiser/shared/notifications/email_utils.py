"""Business Unit: shared | Status: current.."""
    return PortfolioBuilder.build_portfolio_allocation(result)


def _build_closed_positions_pnl_email_html(account_info: AccountInfo | EnrichedAccountInfo) -> str:
    """Backward compatibility function."""
    return PortfolioBuilder.build_closed_positions_pnl(account_info)


def _build_technical_indicators_email_html(
    strategy_signals: Any,
) -> str:  # TODO: Phase 10 - Add proper signal types
    """Backward compatibility function."""
    return SignalsBuilder.build_technical_indicators(strategy_signals)


def _build_detailed_strategy_signals_email_html(
    strategy_signals: Any, strategy_summary: Any
) -> str:  # TODO: Phase 10 - Add proper types
    """Backward compatibility function."""
    return SignalsBuilder.build_detailed_strategy_signals(strategy_signals, strategy_summary)


def _build_enhanced_trading_summary_email_html(
    trading_summary: Any,
) -> str:  # TODO: Phase 10 - Add proper trading summary type
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
