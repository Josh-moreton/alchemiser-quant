"""Trading execution CLI module.

Handles trading execution with comprehensive error handling and notifications.
"""

from the_alchemiser.application.execution.smart_execution import is_market_open
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    map_signals_dict as _map_signals_to_typed,
)
from the_alchemiser.application.engine_service import TradingEngine
from the_alchemiser.application.types import MultiStrategyExecutionResult
from the_alchemiser.application.types import MultiStrategyExecutionResult
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger
from the_alchemiser.interface.cli.cli_formatter import (
    render_enriched_order_summaries,
    render_footer,
    render_header,
    render_strategy_signals,
)
from the_alchemiser.services.errors.exceptions import (
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.utils.feature_flags import type_system_v2_enabled


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

        # Ensure DI container respects requested trading mode before instantiation
        try:
            desired_paper_mode = not self.live_trading
            # Override the paper_trading provider so downstream providers pick the right keys/endpoints
            container.config.paper_trading.override(desired_paper_mode)
        except Exception:
            # Non-fatal; fallback will still set trader.paper_trading later for UI, but endpoints may remain default
            pass

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
        if type_system_v2_enabled():
            try:
                # Visible indicator in logs when typed path is active
                self.logger.info(
                    "TYPES_V2_ENABLED detected: using typed StrategySignal mapping for execution"
                )
                strategy_signals = _map_signals_to_typed(strategy_signals)  # type: ignore[assignment]
            except Exception:
                pass

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
        result: MultiStrategyExecutionResult = trader.execute_multi_strategy()

        # Display results
        trader.display_multi_strategy_summary(result)

        # Optional: show enriched open orders using the new typed path under feature flag
        try:
            if type_system_v2_enabled():
                # Acquire TradingServiceManager from DI container credentials
                import the_alchemiser.main as app_main

                container = app_main._di_container
                if container is not None:
                    api_key = container.config.alpaca_api_key()
                    secret_key = container.config.alpaca_secret_key()
                    paper = container.config.paper_trading()
                    from the_alchemiser.services.trading.trading_service_manager import (
                        TradingServiceManager,
                    )

                    tsm = TradingServiceManager(api_key, secret_key, paper=paper)
                    open_orders = tsm.get_open_orders()
                    if open_orders:
                        render_enriched_order_summaries(open_orders)
        except Exception:
            # Non-fatal UI enhancement; ignore errors here
            pass

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

            # Indicate typed mode in console if enabled
            if type_system_v2_enabled():
                try:
                    from rich.console import Console

                    Console().print(
                        "[dim]TYPES_V2_ENABLED: typed StrategySignal path is ACTIVE[/dim]"
                    )
                except Exception:
                    self.logger.info("TYPES_V2_ENABLED: typed StrategySignal path is ACTIVE")

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
