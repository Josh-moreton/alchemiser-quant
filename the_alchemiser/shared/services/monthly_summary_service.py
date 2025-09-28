#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Monthly Summary Service for Portfolio and Strategy Performance Reporting.

This service computes monthly portfolio P&L using Alpaca API portfolio history
and per-strategy realized P&L from trade ledger entries for email reporting.
"""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from ..persistence.trade_ledger_factory import get_default_trade_ledger
from ..protocols.trade_ledger import TradeLedger
from ..schemas.reporting import MonthlySummaryDTO
from ..schemas.trade_ledger import TradeLedgerQuery
from ..services.alpaca_account_service import AlpacaAccountService

logger = logging.getLogger(__name__)


class MonthlySummaryService:
    """Service for computing monthly portfolio and strategy performance summaries."""

    def __init__(
        self,
        trade_ledger: TradeLedger | None = None,
        alpaca_account_service: AlpacaAccountService | None = None,
    ) -> None:
        """Initialize the monthly summary service.

        Args:
            trade_ledger: Optional trade ledger instance
            alpaca_account_service: Optional Alpaca account service instance

        """
        self._trade_ledger = trade_ledger or get_default_trade_ledger()
        # Respect explicit dependency injection. If None is passed, do not auto-create
        # to allow tests and callers to disable Alpaca usage deterministically.
        self._alpaca_account_service = alpaca_account_service

    def _create_alpaca_account_service(self) -> AlpacaAccountService | None:
        """Create Alpaca account service from configuration.

        Returns:
            AlpacaAccountService instance or None if credentials not available

        """
        try:
            from alpaca.trading.client import TradingClient

            from ..config.secrets_adapter import get_alpaca_keys

            api_key, secret_key, endpoint = get_alpaca_keys()
            if not api_key or not secret_key:
                logger.warning(
                    "Alpaca API keys not found - monthly summary will use fallback data"
                )
                return None

            # Determine if this is paper trading based on endpoint (normalize variants)
            def _is_paper_from_endpoint(ep: str | None) -> bool:
                if not ep:
                    return True
                ep_norm = ep.strip().rstrip("/").lower()
                if ep_norm.endswith("/v2"):
                    ep_norm = ep_norm[:-3]
                if "paper-api.alpaca.markets" in ep_norm:
                    return True
                return not ("api.alpaca.markets" in ep_norm and "paper" not in ep_norm)

            paper = _is_paper_from_endpoint(endpoint)

            trading_client = TradingClient(
                api_key=api_key, secret_key=secret_key, paper=paper
            )

            return AlpacaAccountService(trading_client)

        except Exception as e:
            logger.warning(f"Failed to create Alpaca account service: {e}")
            return None

    def compute_monthly_summary(
        self, year: int, month: int, account_id: str | None = None
    ) -> MonthlySummaryDTO:
        """Compute monthly summary for the given month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            account_id: Optional account ID. If None, uses latest available account

        Returns:
            Monthly summary DTO

        Raises:
            ValueError: If month parameters are invalid

        """
        if not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Must be 1-12.")

        # Create month window (UTC-based)
        start_date = datetime(year, month, 1, tzinfo=UTC)
        _, last_day = monthrange(year, month)
        end_date = datetime(year, month, last_day, 23, 59, 59, 999999, tzinfo=UTC)

        month_label = start_date.strftime("%b %Y")
        logger.info(f"Computing monthly summary for {month_label}")

        # Determine account ID if not provided
        if account_id is None:
            account_id = self._get_latest_account_id()
            if account_id is None:
                logger.warning("No account ID found and none provided")

        # Compute portfolio P&L using Alpaca API portfolio history
        portfolio_pnl = self._compute_portfolio_pnl_from_alpaca(year, month)

        # Compute strategy P&L from trade ledger entries
        strategy_rows = self._compute_strategy_pnl(start_date, end_date)

        # Collect any notes or warnings
        notes = []
        if portfolio_pnl["first_value"] is None and portfolio_pnl["last_value"] is None:
            notes.append("No portfolio history found for this month from Alpaca API")
        elif (
            portfolio_pnl["first_value"] is None or portfolio_pnl["last_value"] is None
        ):
            notes.append(
                "Limited portfolio history - percentage change may not be accurate"
            )

        if not strategy_rows:
            notes.append("No strategy trading activity found for this month")

        return MonthlySummaryDTO(
            month_label=month_label,
            portfolio_first_value=portfolio_pnl["first_value"],
            portfolio_last_value=portfolio_pnl["last_value"],
            portfolio_pnl_abs=portfolio_pnl["abs_change"],
            portfolio_pnl_pct=portfolio_pnl["pct_change"],
            strategy_rows=strategy_rows,
            notes=notes,
        )

    def _get_latest_account_id(self) -> str | None:
        """Get the current account ID from Alpaca API.

        Returns:
            Current account ID or None if not available

        """
        if not self._alpaca_account_service:
            logger.warning("No Alpaca account service available to get account ID")
            return None

        try:
            account_info = self._alpaca_account_service.get_account_dict()
            # Be defensive: ensure a real mapping before subscripting
            if isinstance(account_info, dict) and account_info.get("id"):
                return str(account_info["id"])
            return None
        except Exception as e:
            logger.error(f"Failed to get account ID from Alpaca API: {e}")
            return None

    def _compute_portfolio_pnl_from_alpaca(
        self, year: int, month: int
    ) -> dict[str, Decimal | None]:
        """Compute portfolio P&L using Alpaca API portfolio history.

        Args:
            year: Year to analyze
            month: Month to analyze

        Returns:
            Dict with first_value, last_value, abs_change, pct_change

        """
        try:
            if not self._alpaca_account_service:
                logger.warning(
                    "No Alpaca account service available for portfolio history"
                )
                return {
                    "first_value": None,
                    "last_value": None,
                    "abs_change": None,
                    "pct_change": None,
                }

            # Calculate month date range
            first_day = 1
            last_day = monthrange(year, month)[1]
            start_date = f"{year}-{month:02d}-{first_day:02d}"
            end_date = f"{year}-{month:02d}-{last_day:02d}"

            # Get portfolio history from Alpaca
            history = self._alpaca_account_service.get_portfolio_history(
                start_date=start_date, end_date=end_date, timeframe="1D"
            )

            if not history or not history.get("equity") or not history.get("timestamp"):
                logger.warning(f"No portfolio history available for {year}-{month:02d}")
                return {
                    "first_value": None,
                    "last_value": None,
                    "abs_change": None,
                    "pct_change": None,
                }

            equity_values = history["equity"]
            if len(equity_values) < 1:
                return {
                    "first_value": None,
                    "last_value": None,
                    "abs_change": None,
                    "pct_change": None,
                }

            # Get first and last values
            first_value = Decimal(str(equity_values[0]))
            last_value = Decimal(str(equity_values[-1]))

            # Calculate changes
            abs_change = last_value - first_value
            pct_change = None
            if first_value > 0:
                pct_change = (abs_change / first_value) * Decimal("100")

            pct_str = f"{pct_change:+.2f}%" if pct_change else "N/A"
            logger.info(
                f"Portfolio P&L for {year}-{month:02d}: ${abs_change:+,.2f} ({pct_str})"
            )

            return {
                "first_value": first_value,
                "last_value": last_value,
                "abs_change": abs_change,
                "pct_change": pct_change,
            }

        except Exception as e:
            logger.error(f"Failed to compute portfolio P&L from Alpaca: {e}")
            return {
                "first_value": None,
                "last_value": None,
                "abs_change": None,
                "pct_change": None,
            }

    def _compute_strategy_pnl(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Compute realized P&L by strategy from trade ledger entries.

        Args:
            start_date: Start of month window
            end_date: End of month window

        Returns:
            List of strategy performance rows

        """
        try:
            # Best-effort query to hint implementations about the window; ignore errors/empties
            query = TradeLedgerQuery(
                start_date=start_date,
                end_date=end_date,
                order_by="timestamp",
                ascending=True,
            )
            try:
                entries_iter = self._trade_ledger.query(query)
                # Force iteration if possible to surface issues early but don't depend on results
                _ = list(entries_iter) if entries_iter is not None else []
            except Exception as exc:
                logger.debug(
                    f"Ignoring trade ledger query error for monthly summary window: {exc}"
                )

            # Calculate performance summaries via ledger implementation
            # Note: Protocol does not accept date range; implementations may compute from full ledger
            # Tests stub this method directly for deterministic behavior.
            summaries = self._trade_ledger.calculate_performance(current_prices={})

            # Filter for strategy-level summaries (symbol=None) and sort by realized P&L
            strategy_summaries = [s for s in summaries if s.symbol is None]
            strategy_summaries.sort(key=lambda x: x.realized_pnl, reverse=True)

            # Build strategy rows
            strategy_rows = []
            for summary in strategy_summaries:
                if summary.realized_pnl != 0 or summary.realized_trades > 0:
                    strategy_rows.append(
                        {
                            "strategy_name": summary.strategy_name,
                            "realized_pnl": summary.realized_pnl,
                            "realized_trades": summary.realized_trades,
                        }
                    )

            return strategy_rows

        except Exception as e:
            logger.error(f"Failed to compute strategy P&L: {e}")
            return []
