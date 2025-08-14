"""Trading execution CLI module.

Handles trading execution with comprehensive error handling and notifications.
"""

from the_alchemiser.application.execution.smart_execution import is_market_open
from the_alchemiser.application.trading.trading_engine import TradingEngine
from the_alchemiser.application.types import MultiStrategyExecutionResult
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger
from the_alchemiser.interface.cli.cli_formatter import (
    render_footer,
    render_header,
    render_strategy_signals,
)
from the_alchemiser.services.errors.exceptions import (
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)


class TradingExecutor:
    """Handles trading execution and reporting."""

    def __init__(
        self,
        settings: Settings,
        live_trading: bool = False,
        ignore_market_hours: bool = False,
    ):
        self.settings = settings
        self.live_trading = live_trading
        self.ignore_market_hours = ignore_market_hours
        self.logger = get_logger(__name__)

    def _get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Extract strategy allocations from configuration."""
        return {
            StrategyType.NUCLEAR: self.settings.strategy.default_strategy_allocations.get(
                "nuclear", 0.3
            ),
            StrategyType.TECL: self.settings.strategy.default_strategy_allocations.get("tecl", 0.5),
            StrategyType.KLM: self.settings.strategy.default_strategy_allocations.get("klm", 0.2),
        }

    def _create_trading_engine(self) -> TradingEngine:
        """Create and configure the trading engine using DI."""
        strategy_allocations = self._get_strategy_allocations()

        # Use DI mode - import module to allow MyPy to narrow attribute types
        import the_alchemiser.main as app_main

        # Check and use container in one step to avoid MyPy unreachable code issues
        container = app_main._di_container
        if container is None:
            raise RuntimeError("DI container not available - ensure system is properly initialized")

        trader = TradingEngine.create_with_di(
            container=container,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=self.ignore_market_hours,
        )
        trader.paper_trading = not self.live_trading
        return trader

    def _check_market_hours(self, trader: TradingEngine) -> bool:
        """Check if market is open for trading."""
        if self.ignore_market_hours:
            return True

        if not is_market_open(trader.trading_client):
            self.logger.warning("Market is closed. No trades will be placed.")
            self._send_market_closed_notification()
            return False

        return True

    def _send_market_closed_notification(self) -> None:
        """Send market closed notification."""
        try:
            from the_alchemiser.interface.email.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            html_content = build_error_email_html(
                "Market Closed Alert", "Market is currently closed. No trades will be placed."
            )
            send_email_notification(
                subject="📈 The Alchemiser - Market Closed Alert",
                html_content=html_content,
                text_content="Market is CLOSED. No trades will be placed.",
            )
        except NotificationError as e:
            self.logger.warning(f"Failed to send market closed notification: {e}")

    def _execute_strategy(self, trader: TradingEngine) -> MultiStrategyExecutionResult:
        """Execute the trading strategy."""
        # Generate and display strategy signals
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")
        strategy_signals, consolidated_portfolio, strategy_attribution = (
            trader.strategy_manager.run_all_strategies()
        )

        render_strategy_signals(strategy_signals)

        # Display portfolio rebalancing summary
        try:
            account_info = trader.get_account_info()
            current_positions = trader.get_positions_dict()
            if account_info and consolidated_portfolio:
                trader.display_target_vs_current_allocations(
                    consolidated_portfolio, account_info, current_positions
                )
        except Exception as e:
            self.logger.warning(f"Could not display portfolio summary: {e}")

        # Execute trading
        self._show_execution_progress()
        result = trader.execute_multi_strategy()

        # Display results
        trader.display_multi_strategy_summary(result)

        return result

    def _show_execution_progress(self) -> None:
        """Show trading execution progress."""
        try:
            from rich.console import Console

            console = Console()
            console.print("[dim]🔄 Executing trading strategy...[/dim]")
        except ImportError:
            self.logger.info("🔄 Executing trading strategy...")

    def _send_trading_notification(
        self, result: MultiStrategyExecutionResult, mode_str: str
    ) -> None:
        """Send trading completion notification."""
        try:
            from the_alchemiser.interface.email.email_utils import send_email_notification
            from the_alchemiser.interface.email.templates import EmailTemplates

            # Enrich result with fresh position data
            try:
                # This is a bit of a hack, but we need fresh positions for email
                trader = self._create_trading_engine()
                fresh_positions = trader.get_positions_dict()

                if hasattr(result, "final_portfolio_state") and result.final_portfolio_state:
                    result.final_portfolio_state["current_positions"] = fresh_positions
                else:
                    result.final_portfolio_state = {"current_positions": fresh_positions}
            except Exception as e:
                self.logger.warning(f"Could not add fresh position data: {e}")

            # Generate email content
            html_content = EmailTemplates.build_multi_strategy_report_neutral(result, mode_str)

            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Multi-Strategy Report",
                html_content=html_content,
                text_content=f"Multi-strategy execution completed. Success: {result.success}",
            )

        except NotificationError as e:
            self.logger.warning(f"Email notification failed: {e}")
        except Exception as e:
            self.logger.warning(f"Email formatting/connection error: {e}")

    def _handle_trading_error(self, error: Exception, mode_str: str) -> None:
        """Handle trading execution errors."""
        try:
            from the_alchemiser.services.errors.error_handler import (
                handle_trading_error,
                send_error_notification_if_needed,
            )

            handle_trading_error(
                error=error,
                context="multi-strategy trading execution",
                component="TradingExecutor.run",
                additional_data={
                    "mode": mode_str,
                    "live_trading": self.live_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )

            send_error_notification_if_needed()

        except NotificationError as notification_error:
            self.logger.warning(f"Failed to send error notification: {notification_error}")

    def run(self) -> bool:
        """Execute trading strategy."""
        mode_str = "LIVE" if self.live_trading else "PAPER"

        try:
            # Create trading engine
            trader = self._create_trading_engine()

            # Check market hours
            if not self._check_market_hours(trader):
                render_footer("Market closed - no action taken")
                return True  # Not an error, just market closed

            # Execute strategy
            result = self._execute_strategy(trader)

            # Send notification
            self._send_trading_notification(result, mode_str)

            return result.success

        except (TradingClientError, StrategyExecutionError) as e:
            self.logger.error(f"Trading execution failed: {e}")
            self._handle_trading_error(e, mode_str)
            return False

        except Exception as e:
            self.logger.error(f"Unexpected error in trading execution: {e}")
            self._handle_trading_error(e, mode_str)
            return False
