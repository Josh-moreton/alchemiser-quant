"""Business Unit: strategy_v2 | Status: current.

Single-file signal generation handler for multi-node strategy execution.

This handler generates signals for a single DSL strategy file, producing
a partial portfolio allocation that will be aggregated by the Aggregator Lambda.
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
from the_alchemiser.shared.schemas.consolidated_portfolio import (
    ConsolidatedPortfolio,
)

logger = get_logger(__name__)


class SingleFileSignalHandler:
    """Handler for generating signals from a single DSL strategy file.

    Used in multi-node mode where each strategy file runs in its own
    Lambda invocation. The allocation weight is already applied by the
    Coordinator, so this handler produces a partial portfolio.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        dsl_file: str,
        allocation: Decimal,
    ) -> None:
        """Initialize the single-file signal handler.

        Args:
            container: Application container for dependency injection.
            dsl_file: DSL strategy file name (e.g., '1-KMLM.clj').
            allocation: Weight allocation for this file (0-1).

        """
        self.container = container
        self.dsl_file = dsl_file
        self.allocation = allocation
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
        )

        self.logger.info(
            "SingleFileSignalHandler initialized",
            extra={
                "dsl_file": dsl_file,
                "allocation": str(allocation),
            },
        )

    def generate_signals(self, correlation_id: str) -> dict[str, Any] | None:
        """Generate signals for the single DSL file.

        Returns a partial portfolio with allocations scaled by this file's
        weight allocation.

        Args:
            correlation_id: Workflow correlation ID for tracing.

        Returns:
            Dictionary with signals_data, consolidated_portfolio, and signal_count.
            Returns None if signal generation fails.

        """
        self.logger.info(
            f"Generating signals for single file: {self.dsl_file}",
            extra={
                "correlation_id": correlation_id,
                "dsl_file": self.dsl_file,
                "allocation": str(self.allocation),
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

            # Scale allocations by this file's weight
            scaled_allocations: dict[str, Decimal] = {}
            for symbol, weight in target_allocation.target_weights.items():
                # Each symbol's allocation is scaled by the file's allocation
                scaled_weight = Decimal(str(weight)) * self.allocation
                if scaled_weight > Decimal("0"):
                    scaled_allocations[symbol] = scaled_weight

            if not scaled_allocations:
                self.logger.warning(
                    f"No positive allocations after scaling for {self.dsl_file}",
                    extra={"correlation_id": correlation_id},
                )
                return None

            # Build consolidated portfolio (partial - allocations < 1.0)
            # Use is_partial=True to skip sum-to-1.0 validation for multi-node mode
            # Track strategy contributions for P&L attribution
            strategy_id = Path(self.dsl_file).stem
            strategy_contributions = {strategy_id: scaled_allocations.copy()}

            consolidated_portfolio = ConsolidatedPortfolio(
                target_allocations=scaled_allocations,
                strategy_contributions=strategy_contributions,
                correlation_id=correlation_id,
                timestamp=datetime.now(UTC),
                strategy_count=1,
                source_strategies=[self.dsl_file],
                is_partial=True,
            )

            # Build signals data for this file
            strategy_name = Path(self.dsl_file).stem
            decision_path = trace.metadata.get("decision_path") if trace.metadata else None
            signals_data: dict[str, Any] = {
                strategy_name: {
                    "symbols": list(scaled_allocations.keys()),
                    "action": "REBALANCE",
                    "reasoning": decision_path or f"DSL strategy {strategy_name}",
                    "total_allocation": float(sum(scaled_allocations.values())),
                    "raw_allocations": {
                        k: float(v) for k, v in target_allocation.target_weights.items()
                    },
                    "file_weight": float(self.allocation),
                }
            }

            signal_count = len(scaled_allocations)

            self.logger.info(
                f"Generated {signal_count} signals from {self.dsl_file}",
                extra={
                    "correlation_id": correlation_id,
                    "dsl_file": self.dsl_file,
                    "signal_count": signal_count,
                    "symbols": list(scaled_allocations.keys()),
                    "total_scaled_allocation": str(sum(scaled_allocations.values())),
                },
            )

            return {
                "signals_data": signals_data,
                "consolidated_portfolio": consolidated_portfolio.model_dump(mode="json"),
                "signal_count": signal_count,
                "data_freshness": self._capture_data_freshness(
                    symbols=list(scaled_allocations.keys()),
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
                - last_data_timestamp: ISO timestamp of most recent data
                - data_age_hours: Age of data in hours
                - freshness_status: "PASS" or "FAIL"
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

            # Calculate data age in hours
            data_age_hours = 0.0
            if oldest_timestamp:
                data_age_hours = (now - oldest_timestamp).total_seconds() / 3600.0

            freshness_status = "FAIL" if stale_symbols else "PASS"

            freshness_info: dict[str, Any] = {
                "last_data_timestamp": oldest_timestamp.isoformat() if oldest_timestamp else None,
                "data_age_hours": round(data_age_hours, 1),
                "freshness_status": freshness_status,
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
                        "freshness_status": freshness_status,
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
                "last_data_timestamp": None,
                "data_age_hours": 0.0,
                "freshness_status": "UNKNOWN",
                "symbols_checked": len(symbols),
                "stale_symbols": [],
            }
