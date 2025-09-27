#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Monthly Summary Service for Portfolio and Strategy Performance Reporting.

This service computes monthly portfolio P&L from account value snapshots and
per-strategy realized P&L from trade ledger entries for email reporting.
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
from ..services.account_value_service import AccountValueService

logger = logging.getLogger(__name__)


class MonthlySummaryService:
    """Service for computing monthly portfolio and strategy performance summaries."""

    def __init__(
        self,
        trade_ledger: TradeLedger | None = None,
        account_value_service: AccountValueService | None = None,
    ) -> None:
        """Initialize the monthly summary service.

        Args:
            trade_ledger: Optional trade ledger instance
            account_value_service: Optional account value service instance

        """
        self._trade_ledger = trade_ledger or get_default_trade_ledger()
        self._account_value_service = account_value_service or AccountValueService(
            self._trade_ledger
        )

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

        # Compute portfolio P&L from account value snapshots
        portfolio_pnl = self._compute_portfolio_pnl(account_id, start_date, end_date)

        # Compute strategy P&L from trade ledger entries
        strategy_rows = self._compute_strategy_pnl(start_date, end_date)

        # Collect any notes or warnings
        notes = []
        if portfolio_pnl["first_value"] is None and portfolio_pnl["last_value"] is None:
            notes.append("No account value snapshots found for this month")
        elif portfolio_pnl["first_value"] is None or portfolio_pnl["last_value"] is None:
            notes.append("Only one account value snapshot found - percentage change not calculated")

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
        """Get the latest account ID from account value entries.

        Returns:
            Latest account ID or None if no entries found

        """
        try:
            # Try to get the latest account value entry
            latest_entry = self._account_value_service.get_latest_account_value("")
            if latest_entry:
                return latest_entry.account_id

            # If that fails, try to get any account value entries
            all_entries = self._account_value_service.get_account_value_history("")
            if all_entries:
                return all_entries[-1].account_id

            return None
        except Exception as e:
            logger.error(f"Failed to get latest account ID: {e}")
            return None

    def _compute_portfolio_pnl(
        self, account_id: str | None, start_date: datetime, end_date: datetime
    ) -> dict[str, Decimal | None]:
        """Compute portfolio P&L from account value snapshots.

        Args:
            account_id: Account ID to query (may be None)
            start_date: Start of month window
            end_date: End of month window

        Returns:
            Dict with first_value, last_value, abs_change, pct_change

        """
        try:
            if account_id is None:
                return {
                    "first_value": None,
                    "last_value": None,
                    "abs_change": None,
                    "pct_change": None,
                }

            # Get account value history for the month
            entries = self._account_value_service.get_account_value_history(
                account_id, start_date, end_date
            )

            if not entries:
                return {
                    "first_value": None,
                    "last_value": None,
                    "abs_change": None,
                    "pct_change": None,
                }

            # Sort by timestamp to ensure proper ordering
            entries.sort(key=lambda x: x.timestamp)

            first_value = entries[0].portfolio_value
            last_value = entries[-1].portfolio_value

            # Calculate absolute change
            abs_change = last_value - first_value

            # Calculate percentage change if possible
            pct_change = None
            if first_value > 0:
                pct_change = (abs_change / first_value) * Decimal("100")

            return {
                "first_value": first_value,
                "last_value": last_value,
                "abs_change": abs_change,
                "pct_change": pct_change,
            }

        except Exception as e:
            logger.error(f"Failed to compute portfolio P&L: {e}")
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
            # Query trade ledger entries for the month
            query = TradeLedgerQuery(
                start_date=start_date,
                end_date=end_date,
                order_by="timestamp",
                ascending=True,
            )

            entries = list(self._trade_ledger.query(query))
            if not entries:
                return []

            # Calculate performance summaries
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
