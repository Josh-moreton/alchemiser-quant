"""Business Unit: shared | Status: current

Trading execution CLI module.

Handles trading execution with comprehensive error handling and notifications.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.infrastructure.dependency_injection.application_container import (
        ApplicationContainer,
    )

from the_alchemiser.execution.strategies.smart_execution import is_market_open
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    convert_signals_dict_to_domain,
    typed_strategy_signal_to_validated_order,
)
from the_alchemiser.application.mapping.strategy_signal_mapping import (
    map_signals_dict as _map_signals_to_typed,
)
from the_alchemiser.application.trading.bootstrap import bootstrap_from_container
from the_alchemiser.strategy.engines.core.trading_engine import TradingEngine
from the_alchemiser.domain.registry import StrategyType
from the_alchemiser.strategy.signals.strategy_signal import (
    StrategySignal as TypedStrategySignal,
)
from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.shared.utils.logging_utils import get_logger
from the_alchemiser.shared.cli.cli_formatter import (
    render_enriched_order_summaries,
    render_footer,
    render_header,
    render_multi_strategy_summary,
    render_strategy_signals,
    render_target_vs_current_allocations,
)
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.execution.orders.order_schemas import ValidatedOrderDTO
from the_alchemiser.shared.utils.exceptions import (
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)


class TradingExecutor:
    """Handles trading execution and reporting."""

    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer,
        live_trading: bool = False,
        ignore_market_hours: bool = False,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> None:
        self.settings = settings
        self.container = container
        self.live_trading = live_trading
        self.ignore_market_hours = ignore_market_hours
        self.show_tracking = show_tracking
        self.export_tracking_json = export_tracking_json
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
        """Create and configure the trading engine using modern bootstrap approach."""
        strategy_allocations = self._get_strategy_allocations()

        # Ensure DI container respects requested trading mode before instantiation
        try:
            desired_paper_mode = not self.live_trading
            # Override the paper_trading provider so downstream providers pick the right keys/endpoints
            self.container.config.paper_trading.override(desired_paper_mode)
        except Exception:
            # Non-fatal; fallback will still set trader.paper_trading later for UI, but endpoints may remain default
            pass

        # Use modern bootstrap approach instead of deprecated create_with_di
        bootstrap_context = bootstrap_from_container(self.container)
        trader = TradingEngine(
            bootstrap_context=bootstrap_context,
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
            from the_alchemiser.infrastructure.notifications.email_utils import (
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

    def _execute_strategy(self, trader: TradingEngine) -> MultiStrategyExecutionResultDTO:
        """Execute the trading strategy."""
        # Generate and display strategy signals
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")
        strategy_signals, consolidated_portfolio, _ = trader.strategy_manager.run_all_strategies()

        # Use typed StrategySignal mapping
        try:
            typed_signals = _map_signals_to_typed(strategy_signals)  # dict -> TypedDict
            typed_domain_signals = convert_signals_dict_to_domain(
                typed_signals
            )  # TypedDict -> domain

            # Debug: Log all signals being processed
            for strategy_type, signal in typed_domain_signals.items():
                self.logger.info(
                    f"Processing signal: {strategy_type} -> {signal.symbol.value} {signal.action}"
                )

            validated_orders = self._convert_signals_to_validated_orders(
                typed_domain_signals, trader
            )
            if validated_orders:
                self.logger.info(
                    f"Generated {len(validated_orders)} validated orders from typed signals"
                )
                for order in validated_orders:
                    self.logger.info(
                        f"Order: {order.symbol} {order.side} {order.quantity} @ {order.order_type}"
                    )
        except Exception as e:
            self.logger.warning(f"Failed to convert signals to validated orders: {e}")

        render_strategy_signals(strategy_signals)

        # Display portfolio rebalancing summary
        try:
            account_info = trader.get_account_info()
            current_positions = trader.get_positions_dict()
            if account_info and consolidated_portfolio:
                # Convert TypedDict to regular dict for the renderer
                from typing import cast

                account_dict = cast(dict[str, Any], account_info)
                render_target_vs_current_allocations(
                    consolidated_portfolio, account_dict, current_positions
                )
        except Exception as e:
            self.logger.warning(f"Could not display portfolio summary: {e}")

        # Execute trading
        self._show_execution_progress()
        result: MultiStrategyExecutionResultDTO = trader.execute_multi_strategy()

        # Display results
        try:
            enriched_account = trader.get_enriched_account_info()
            enriched_account_dict = dict(enriched_account) if enriched_account else None
        except Exception:
            enriched_account_dict = None

        render_multi_strategy_summary(result, enriched_account_dict)

        # Show enriched open orders using typed domain model
        try:
            # Use injected container instead of global access
            api_key = self.container.config.alpaca_api_key()
            secret_key = self.container.config.alpaca_secret_key()
            paper = self.container.config.paper_trading()
            from the_alchemiser.execution.services.trading_service_manager import (
                TradingServiceManager,
            )

            tsm = TradingServiceManager(api_key, secret_key, paper=paper)
            open_orders = tsm.get_open_orders()
            if open_orders and open_orders.orders:
                # Convert DTO to expected format
                orders_list = [order.summary for order in open_orders.orders]
                render_enriched_order_summaries(orders_list)
        except Exception:
            # Non-fatal UI enhancement; ignore errors here
            pass

        return result

    def _convert_signals_to_validated_orders(
        self,
        strategy_signals: dict[StrategyType, TypedStrategySignal],
        trader: TradingEngine,
    ) -> list[ValidatedOrderDTO]:
        """Convert typed strategy signals to validated orders.

        Args:
            strategy_signals: Dict of strategy signals by strategy type
            trader: Trading engine instance for getting portfolio value

        Returns:
            List of ValidatedOrderDTO instances ready for execution

        """
        validated_orders = []

        try:
            # Get portfolio value for quantity calculations
            account_info = trader.get_account_info()

            # Extract portfolio value (use equity as total portfolio value)
            portfolio_value = float(account_info.get("equity", 0))
            if portfolio_value <= 0:
                self.logger.warning(f"Invalid portfolio value: {portfolio_value}")
                return []

            from decimal import Decimal

            portfolio_decimal = Decimal(str(portfolio_value))

            # Convert each signal to validated order
            for strategy_type, signal in strategy_signals.items():
                try:
                    # Skip HOLD signals
                    if signal.action == "HOLD":
                        self.logger.info(f"Skipping HOLD signal from {strategy_type}")
                        continue

                    # Skip portfolio symbols that need expansion (handled by main execution engine)
                    if signal.symbol.value in [
                        "NUCLEAR_PORTFOLIO",
                        "BEAR_PORTFOLIO",
                        "UVXY_BTAL_PORTFOLIO",
                    ]:
                        self.logger.info(
                            f"Skipping portfolio signal {signal.symbol.value} - handled by execution engine"
                        )
                        continue

                    # Convert signal to validated order
                    validated_order = typed_strategy_signal_to_validated_order(
                        signal=signal,
                        portfolio_value=portfolio_decimal,
                        order_type="market",  # Default to market orders
                        time_in_force="day",
                        client_order_id=f"{strategy_type.value}_{signal.symbol.value}_{int(signal.timestamp.timestamp())}",
                    )

                    validated_orders.append(validated_order)
                    self.logger.info(
                        f"Converted {strategy_type} signal to order: {validated_order.symbol} "
                        f"{validated_order.side} {validated_order.quantity}"
                    )

                except ValueError as e:
                    self.logger.warning(f"Failed to convert {strategy_type} signal to order: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"Unexpected error converting {strategy_type} signal: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Failed to convert strategy signals to validated orders: {e}")

        return validated_orders

    def _show_execution_progress(self) -> None:
        """Show trading execution progress."""
        try:
            from rich.console import Console

            console = Console()
            console.print("[dim]🔄 Executing trading strategy...[/dim]")
        except ImportError:
            self.logger.info("🔄 Executing trading strategy...")

    def _send_trading_notification(
        self, result: MultiStrategyExecutionResultDTO, mode_str: str
    ) -> None:
        """Send trading completion notification.

        Enriches the result with fresh position data for email rendering.
        Only supports PortfolioStateDTO for final_portfolio_state - legacy dict
        paths are intentionally ignored per No Legacy Fallback Policy.

        Args:
            result: The execution result DTO
            mode_str: Trading mode string for display

        """
        try:
            from the_alchemiser.infrastructure.notifications.email_utils import (
                send_email_notification,
            )
            from the_alchemiser.infrastructure.notifications.templates import EmailTemplates

            # Enrich result with fresh position data without mutating the frozen DTO
            try:
                trader = self._create_trading_engine()
                fresh_positions = trader.get_positions_dict()
                # Safely construct an updated copy for email rendering
                try:
                    # Handle DTO case for final_portfolio_state
                    state_dict: dict[str, Any] = {}
                    if result.final_portfolio_state and hasattr(
                        result.final_portfolio_state, "model_dump"
                    ):
                        # Convert DTO to dict
                        state_dict = result.final_portfolio_state.model_dump()
                    elif result.final_portfolio_state and isinstance(
                        result.final_portfolio_state, dict
                    ):
                        # Legacy dict case: Per No Legacy Fallback Policy, this path is
                        # intentionally unsupported. We do not merge legacy dict state.
                        # This avoids hidden legacy execution paths in production.
                        self.logger.warning(
                            "final_portfolio_state is a legacy dict - ignoring per No Legacy Fallback Policy"
                        )
                        # Continue with empty state_dict to avoid legacy fallback

                    updated_state = {
                        **state_dict,
                        "current_positions": fresh_positions,
                    }
                    email_result: MultiStrategyExecutionResultDTO | Any = result.model_copy(
                        update={"final_portfolio_state": updated_state}, deep=True
                    )
                except Exception:
                    # If model_copy is unavailable, fall back to passing a tuple of (result, state)
                    email_result = result
            except Exception as e:
                self.logger.warning(f"Could not enrich result with fresh position data: {e}")
                email_result = result
                self.logger.warning(f"Could not enrich result with fresh position data: {e}")
                email_result = result

            # Generate email content
            html_content = EmailTemplates.build_multi_strategy_report_neutral(
                email_result, mode_str
            )

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
            from the_alchemiser.shared.utils.error_handler import (
                TradingSystemErrorHandler,
                send_error_notification_if_needed,
            )

            # Use TradingSystemErrorHandler directly for consistency
            error_handler = TradingSystemErrorHandler()
            error_handler.handle_error(
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

            # System now uses fully typed domain model
            try:
                from rich.console import Console

                Console().print("[dim]Using typed StrategySignal domain model[/dim]")
            except Exception:
                self.logger.info("Using typed StrategySignal domain model")

            # Check market hours
            if not self._check_market_hours(trader):
                render_footer("Market closed - no action taken")
                return True  # Not an error, just market closed

            # Execute strategy
            result = self._execute_strategy(trader)

            # Display tracking if requested
            if self.show_tracking:
                self._display_post_execution_tracking()

            # Export tracking summary if requested
            if self.export_tracking_json:
                self._export_tracking_summary()

            # Send notification
            self._send_trading_notification(result, mode_str)

            return result.success

        except (TradingClientError, StrategyExecutionError) as e:
            self._handle_trading_error(e, mode_str)
            return False

        except Exception as e:
            self._handle_trading_error(e, mode_str)
            return False

    def _display_post_execution_tracking(self) -> None:
        """Display strategy performance tracking after execution."""
        try:
            from rich.console import Console
            from rich.panel import Panel

            from the_alchemiser.shared.cli.signal_analyzer import SignalAnalyzer

            console = Console()
            console.print("\n")

            # Create a signal analyzer instance to reuse the tracking display logic
            analyzer = SignalAnalyzer(self.settings, self.container)
            analyzer._display_strategy_tracking()

        except Exception as e:
            self.logger.warning(f"Failed to display post-execution tracking: {e}")
            try:
                from rich.console import Console

                Console().print(
                    Panel(
                        f"[dim yellow]Strategy tracking display unavailable: {e}[/dim yellow]",
                        title="Strategy Performance Tracking",
                        border_style="yellow",
                    )
                )
            except ImportError:
                self.logger.warning("Strategy tracking display unavailable (rich not available)")

    def _export_tracking_summary(self) -> None:
        """Export tracking summary to JSON file."""
        try:
            import json
            from pathlib import Path

            from the_alchemiser.portfolio.pnl.strategy_order_tracker import (
                StrategyOrderTracker,
            )

            # Create tracker using same mode as execution
            tracker = StrategyOrderTracker(paper_trading=not self.live_trading)

            # Get summary data for all strategies
            summary_data = []
            strategies = ["nuclear", "tecl", "klm"]

            for strategy_name in strategies:
                try:
                    positions = tracker.get_positions_summary()
                    if strategy_name.lower() in [pos.strategy.lower() for pos in positions]:
                        pnl_summary = tracker.get_pnl_summary(strategy_name)
                        recent_orders = tracker.get_orders_for_strategy(strategy_name)

                        # Calculate position count
                        strategy_positions = [
                            pos
                            for pos in positions
                            if pos.strategy.lower() == strategy_name.lower()
                        ]
                        position_count = len(strategy_positions)

                        # Calculate return percentage
                        total_pnl = float(pnl_summary.total_pnl)
                        if hasattr(pnl_summary, "cost_basis") and float(pnl_summary.cost_basis) > 0:
                            return_pct = (total_pnl / float(pnl_summary.cost_basis)) * 100
                        else:
                            return_pct = 0.0

                        summary_data.append(
                            {
                                "strategy": strategy_name,
                                "position_count": position_count,
                                "total_pnl": total_pnl,
                                "return_pct": return_pct,
                                "recent_orders_count": len(recent_orders[-10:]),  # Last 10 orders
                                "updated_at": pnl_summary.last_updated.isoformat()
                                if hasattr(pnl_summary, "last_updated") and pnl_summary.last_updated
                                else None,
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"Error gathering tracking data for {strategy_name}: {e}")
                    summary_data.append(
                        {
                            "strategy": strategy_name,
                            "position_count": 0,
                            "total_pnl": 0.0,
                            "return_pct": 0.0,
                            "recent_orders_count": 0,
                            "updated_at": None,
                            "error": str(e),
                        }
                    )

            # Write to file
            if self.export_tracking_json is None:
                raise ValueError("Export path is None")

            output_path = Path(self.export_tracking_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w") as f:
                json.dump(
                    {
                        "summary": summary_data,
                        "export_timestamp": datetime.now(UTC).isoformat(),
                        "trading_mode": "live" if self.live_trading else "paper",
                    },
                    f,
                    indent=2,
                )

            self.logger.info(f"Tracking summary exported to {output_path}")

            try:
                from rich.console import Console

                Console().print(f"[dim]📄 Tracking summary exported to {output_path}[/dim]")
            except ImportError:
                pass

        except Exception as e:
            self.logger.error(f"Failed to export tracking summary: {e}")
            try:
                from rich.console import Console

                Console().print(
                    f"[bold red]Failed to export tracking summary to {self.export_tracking_json}: {e}[/bold red]"
                )
            except ImportError:
                pass
