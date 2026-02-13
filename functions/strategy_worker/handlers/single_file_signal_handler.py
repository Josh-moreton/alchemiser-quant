"""Business Unit: strategy | Status: current.

Single-file signal generation handler for per-strategy execution.

This handler evaluates a single DSL strategy file and returns the raw
target weights for the StrategyRebalancer to execute independently.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from importlib import resources as importlib_resources
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from engines.dsl.engine import DslEngine

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class SingleFileSignalHandler:
    """Handler for generating signals from a single DSL strategy file.

    Evaluates the DSL file and returns raw target weights. Capital
    allocation and rebalance planning are handled by the StrategyRebalancer.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        dsl_file: str,
        *,
        debug_mode: bool = False,
    ) -> None:
        """Initialize the single-file signal handler.

        Args:
            container: Application container for dependency injection.
            dsl_file: DSL strategy file name (e.g., '1-KMLM.clj').
            debug_mode: If True, enables detailed condition tracing for debugging.

        """
        self.container = container
        self.dsl_file = dsl_file
        self.debug_mode = debug_mode
        self.logger = logger

        # Resolve strategies directory using importlib.resources (Lambda layer)
        try:
            strategies_path = importlib_resources.files("the_alchemiser.shared.strategies")
        except (ModuleNotFoundError, AttributeError):
            # Fallback for local development - navigate from functions/strategy_worker/handlers/
            # to project root, then to layer path
            strategies_path = (
                Path(__file__).parent.parent.parent.parent
                / "layers"
                / "shared"
                / "the_alchemiser"
                / "shared"
                / "strategies"
            )
            if not strategies_path.exists():
                raise FileNotFoundError(
                    f"Strategies directory not found at: {strategies_path}. "
                    "Ensure the layer structure exists."
                )
            logger.warning("Using local strategies path (not Lambda layer)")

        # Get market data adapter from container (with live bar injection if configured)
        self.market_data_adapter = container.strategy_market_data_adapter()

        # Pass Traversable object directly (don't convert to string)
        self.dsl_engine = DslEngine(
            strategy_config_path=strategies_path,
            market_data_adapter=self.market_data_adapter,
            debug_mode=self.debug_mode,
        )

        self.logger.info(
            "SingleFileSignalHandler initialized",
            extra={
                "dsl_file": dsl_file,
                "debug_mode": debug_mode,
            },
        )

    def generate_signals(self, correlation_id: str) -> dict[str, Any] | None:
        """Generate signals for the single DSL file.

        Returns the raw target weights from DSL evaluation. The caller
        (StrategyRebalancer) handles capital allocation and rebalance planning.

        Args:
            correlation_id: Workflow correlation ID for tracing.

        Returns:
            Dictionary with target_weights, data_freshness, and signal metadata.
            Returns None if signal generation fails.

        """
        self.logger.info(
            f"Generating signals for single file: {self.dsl_file}",
            extra={
                "correlation_id": correlation_id,
                "dsl_file": self.dsl_file,
            },
        )

        try:
            # Evaluate the single DSL file
            target_allocation, trace = self.dsl_engine.evaluate_strategy(
                strategy_config_path=self.dsl_file,
                correlation_id=correlation_id,
            )

            if not target_allocation or not target_allocation.target_weights:
                self.logger.warning(
                    f"No target weights returned from {self.dsl_file}",
                    extra={"correlation_id": correlation_id},
                )
                return None

            # Return raw weights -- the rebalancer handles capital allocation
            target_weights: dict[str, Decimal] = {
                symbol: Decimal(str(weight))
                for symbol, weight in target_allocation.target_weights.items()
                if Decimal(str(weight)) > Decimal("0")
            }

            if not target_weights:
                self.logger.warning(
                    f"No positive weights from {self.dsl_file}",
                    extra={"correlation_id": correlation_id},
                )
                return None

            symbols = list(target_weights.keys())
            signal_count = len(target_weights)

            # Capture decision path from trace for logging
            strategy_name = Path(self.dsl_file).stem
            decision_path = trace.metadata.get("decision_path") if trace.metadata else None

            self.logger.info(
                f"Generated {signal_count} signals from {self.dsl_file}",
                extra={
                    "correlation_id": correlation_id,
                    "dsl_file": self.dsl_file,
                    "signal_count": signal_count,
                    "symbols": symbols,
                    "total_weight": str(sum(target_weights.values())),
                    "decision_path": decision_path,
                },
            )

            return {
                "target_weights": target_weights,
                "signal_count": signal_count,
                "strategy_name": strategy_name,
                "data_freshness": self._capture_data_freshness(
                    symbols=symbols,
                    correlation_id=correlation_id,
                ),
            }

        except Exception as e:
            self.logger.error(
                f"Failed to generate signals for {self.dsl_file}",
                extra={
                    "correlation_id": correlation_id,
                    "dsl_file": self.dsl_file,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def _capture_data_freshness(
        self,
        symbols: list[str],
        correlation_id: str,
    ) -> dict[str, Any]:
        """Capture data freshness information for the symbols used.

        Args:
            symbols: List of symbols to check freshness for.
            correlation_id: Workflow correlation ID for logging.

        Returns:
            Dictionary with data freshness info:
                - latest_timestamp: ISO timestamp of most recent data
                - age_days: Age of data in days
                - gate_status: "PASS" or "FAIL"
                - symbols_checked: Number of symbols checked
                - stale_symbols: List of symbols with stale data

        """
        try:
            now = datetime.now(UTC)
            max_stale_days = 3
            oldest_timestamp: datetime | None = None
            stale_symbols: list[str] = []

            for symbol in symbols:
                metadata = self.market_data_adapter.market_data_store.get_metadata(symbol)
                if metadata is None:
                    stale_symbols.append(symbol)
                    continue

                try:
                    last_bar_date = datetime.strptime(metadata.last_bar_date, "%Y-%m-%d").replace(
                        tzinfo=UTC
                    )
                    days_since = (now - last_bar_date).days

                    if days_since > max_stale_days:
                        stale_symbols.append(symbol)

                    if oldest_timestamp is None or last_bar_date < oldest_timestamp:
                        oldest_timestamp = last_bar_date

                except Exception:
                    stale_symbols.append(symbol)

            # Calculate data age in days
            age_days = 0
            if oldest_timestamp:
                age_days = (now - oldest_timestamp).days

            gate_status = "FAIL" if stale_symbols else "PASS"

            freshness_info: dict[str, Any] = {
                "latest_timestamp": oldest_timestamp.isoformat() if oldest_timestamp else None,
                "age_days": age_days,
                "gate_status": gate_status,
                "symbols_checked": len(symbols),
                "stale_symbols": stale_symbols,
            }

            if stale_symbols:
                self.logger.warning(
                    f"Data freshness check: {len(stale_symbols)} stale symbols",
                    extra={
                        "correlation_id": correlation_id,
                        "dsl_file": self.dsl_file,
                        "stale_symbols": stale_symbols,
                        "gate_status": gate_status,
                    },
                )

            return freshness_info

        except Exception as e:
            self.logger.warning(
                "Failed to capture data freshness",
                extra={
                    "correlation_id": correlation_id,
                    "dsl_file": self.dsl_file,
                    "error": str(e),
                },
            )
            return {
                "latest_timestamp": None,
                "age_days": 0,
                "gate_status": "UNKNOWN",
                "symbols_checked": len(symbols),
                "stale_symbols": [],
            }
