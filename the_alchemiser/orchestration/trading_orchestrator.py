"""Business Unit: orchestration | Status: current

Trading execution orchestration workflow.

Coordinates the complete trading execution workflow including signal generation,
portfolio rebalancing, order execution, and result reporting. Uses the new
orchestration and execution_v2 modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.orchestration.signal_orchestrator import SignalOrchestrator
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.types.exceptions import (
    NotificationError,
    TradingClientError,
)


class TradingOrchestrator:
    """Orchestrates trading execution workflow."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        live_trading: bool = False,  # DEPRECATED - determined by stage
        ignore_market_hours: bool = False,
    ) -> None:
        self.settings = settings
        self.container = container
        # Get trading mode from container (ignore deprecated parameter)
        self.live_trading = not self.container.config.paper_trading()

        if live_trading != self.live_trading:
            self.logger.warning(
                f"live_trading parameter ({live_trading}) ignored. "
                f"Using endpoint-determined mode: {'live' if self.live_trading else 'paper'}"
            )

        self.ignore_market_hours = ignore_market_hours
        self.logger = get_logger(__name__)

        # Create signal orchestrator for signal generation
        self.signal_orchestrator = SignalOrchestrator(settings, container)

    def check_market_hours(self) -> bool:
        """Check if market is open for trading."""
        if self.ignore_market_hours:
            return True

        # Use AlpacaManager's is_market_open method
        alpaca_manager = self.container.infrastructure.alpaca_manager()
        if not alpaca_manager.is_market_open():
            self.logger.warning("Market is closed. No trades will be placed.")
            self._send_market_closed_notification()
            return False

        return True

    def _send_market_closed_notification(self) -> None:
        """Send market closed notification."""
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            html_content = build_error_email_html(
                "Market Closed Alert",
                "Market is currently closed. No trades will be placed.",
            )
            send_email_notification(
                subject="📈 The Alchemiser - Market Closed Alert",
                html_content=html_content,
                text_content="Market is CLOSED. No trades will be placed.",
            )
        except NotificationError as e:
            self.logger.warning(f"Failed to send market closed notification: {e}")

    def execute_strategy_signals(self) -> dict[str, Any] | None:
        """Generate strategy signals and return execution data."""
        try:
            # Generate signals using signal orchestrator
            result = self.signal_orchestrator.analyze_signals()
            if result is None:
                self.logger.error("Failed to generate strategy signals")
                return None

            strategy_signals, consolidated_portfolio = result

            # For now, return a simplified execution result
            # TODO: Integrate with execution_v2 for actual order placement
            return {
                "strategy_signals": strategy_signals,
                "consolidated_portfolio": consolidated_portfolio,
                "success": True,
                "message": "Signal generation completed successfully",
            }

        except Exception as e:
            self.logger.error(f"Strategy signal execution failed: {e}")
            return None

    def send_trading_notification(self, result: dict[str, Any], mode_str: str) -> None:
        """Send trading completion notification.

        Args:
            result: The execution result dictionary
            mode_str: Trading mode string for display

        """
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            # Create simple HTML content for the result
            success = result.get("success", False)
            message = result.get("message", "Trading execution completed")

            if success:
                html_content = f"""
                <h2>Trading Execution Report - {mode_str.upper()}</h2>
                <p><strong>Status:</strong> Success</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Timestamp:</strong> {datetime.now(UTC)}</p>
                """
            else:
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    message,
                )

            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Trading Report",
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {success}",
            )

        except NotificationError as e:
            self.logger.warning(f"Email notification failed: {e}")
        except Exception as e:
            self.logger.warning(f"Email formatting/connection error: {e}")

    def handle_trading_error(self, error: Exception, mode_str: str) -> None:
        """Handle trading execution errors."""
        try:
            from the_alchemiser.shared.errors.error_handler import (
                TradingSystemErrorHandler,
                send_error_notification_if_needed,
            )

            # Use TradingSystemErrorHandler directly for consistency
            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
                error=error,
                context="multi-strategy trading execution",
                component="TradingOrchestrator.execute",
                additional_data={
                    "mode": mode_str,
                    "live_trading": self.live_trading,
                    "ignore_market_hours": self.ignore_market_hours,
                },
            )

            send_error_notification_if_needed()

        except NotificationError as notification_error:
            self.logger.warning(f"Failed to send error notification: {notification_error}")

    def execute_trading_workflow(self) -> bool:
        """Execute complete trading workflow.

        Returns:
            True if trading succeeded, False otherwise

        """
        mode_str = "LIVE" if self.live_trading else "PAPER"

        try:
            # System now uses fully typed domain model
            self.logger.info("Using typed StrategySignal domain model")

            # Check market hours
            if not self.check_market_hours():
                self.logger.info("Market closed - no action taken")
                return True  # Not an error, just market closed

            # Execute strategy signals
            result = self.execute_strategy_signals()
            if result is None:
                self.logger.error("Strategy execution failed")
                return False

            # Send notification
            self.send_trading_notification(result, mode_str)

            return result.get("success", False)

        except TradingClientError as e:
            self.handle_trading_error(e, mode_str)
            return False

        except Exception as e:
            self.handle_trading_error(e, mode_str)
            return False

    def execute_trading_workflow_with_details(self) -> dict[str, Any] | None:
        """Execute complete trading workflow and return detailed results.

        Returns:
            Dictionary with strategy signals, portfolio, and success status, or None if failed

        """
        mode_str = "LIVE" if self.live_trading else "PAPER"

        try:
            # System now uses fully typed domain model
            self.logger.info("Using typed StrategySignal domain model")

            # Check market hours
            if not self.check_market_hours():
                self.logger.info("Market closed - no action taken")
                return {
                    "strategy_signals": {},
                    "consolidated_portfolio": {},
                    "success": True,
                    "message": "Market closed - no action taken",
                }

            # Execute strategy signals
            result = self.execute_strategy_signals()
            if result is None:
                self.logger.error("Strategy execution failed")
                return None

            # Send notification
            self.send_trading_notification(result, mode_str)

            return result

        except TradingClientError as e:
            self.handle_trading_error(e, mode_str)
            return None

        except Exception as e:
            self.handle_trading_error(e, mode_str)
            return None
