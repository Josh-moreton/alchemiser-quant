"""Business Unit: data | Status: current.

Service for fetching P&L history from Alpaca and storing in DynamoDB.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.pnl_history_repository import (
    PnLHistoryRepository,
)
from the_alchemiser.shared.schemas.pnl_history import PnLHistoryRecord
from the_alchemiser.shared.services.pnl_service import PnLService

logger = get_logger(__name__)


class PnLDataService:
    """Service for capturing and storing P&L history."""

    def __init__(self) -> None:
        """Initialize service with PnLService and DynamoDB repository."""
        self.pnl_service = PnLService()
        self.repository = PnLHistoryRepository()

    def capture_pnl_history(
        self,
        period: str = "1A",
        account_id: str | None = None,
    ) -> int:
        """Capture P&L history from Alpaca and store in DynamoDB.
        
        Fetches all daily P&L records with intelligent deposit/withdrawal matching
        and stores them in DynamoDB for fast dashboard access.
        
        Args:
            period: Time period to fetch (1W, 1M, 3M, 1A). Default: 1A (1 year).
            account_id: Alpaca account ID. If None, reads from environment.
            
        Returns:
            Number of records saved.
        """
        try:
            # Fetch P&L data from Alpaca with deposit adjustments
            daily_records, _ = self.pnl_service.get_all_daily_records(period=period)
            
            if not daily_records:
                logger.warning("No P&L records returned from Alpaca")
                return 0
            
            # Get account ID from environment if not provided
            if account_id is None:
                # Try to get from Alpaca manager
                from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
                alpaca = AlpacaManager()
                account = alpaca.get_account()
                account_id = account.get("account_number", "unknown")
            
            # Current timestamp
            timestamp_str = datetime.now(UTC).isoformat()
            
            # Convert to PnLHistoryRecord objects
            records = []
            for rec in daily_records:
                record = PnLHistoryRecord(
                    account_id=account_id,
                    date=rec.date.strftime("%Y-%m-%d"),
                    equity=rec.equity,
                    profit_loss=rec.profit_loss,
                    profit_loss_pct=rec.profit_loss_pct,
                    deposit=rec.deposit if rec.deposit else Decimal("0"),
                    withdrawal=rec.withdrawal if rec.withdrawal else Decimal("0"),
                    base_value=rec.base_value if hasattr(rec, "base_value") else None,
                    cumulative_pnl=None,  # Will be calculated if needed
                    timestamp=timestamp_str,
                )
                records.append(record)
            
            # Save batch to DynamoDB
            self.repository.save_batch(records)
            
            logger.info(
                "P&L history captured successfully",
                extra={
                    "account_id": account_id,
                    "record_count": len(records),
                    "period": period,
                },
            )
            
            return len(records)
            
        except Exception as e:
            logger.error(
                "Failed to capture P&L history",
                extra={"error": str(e), "period": period},
                exc_info=True,
            )
            return 0

    def get_pnl_for_period(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
    ) -> list[PnLHistoryRecord]:
        """Get P&L history for a date range from DynamoDB.
        
        Args:
            account_id: Alpaca account number.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            
        Returns:
            List of PnLHistoryRecord objects.
        """
        return self.repository.get_records_for_period(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_all_pnl(self, account_id: str) -> list[PnLHistoryRecord]:
        """Get all P&L history for an account from DynamoDB.
        
        Args:
            account_id: Alpaca account number.
            
        Returns:
            List of PnLHistoryRecord objects.
        """
        return self.repository.get_all_records(account_id)

    def get_latest_pnl(self, account_id: str) -> PnLHistoryRecord | None:
        """Get the most recent P&L record from DynamoDB.
        
        Args:
            account_id: Alpaca account number.
            
        Returns:
            Latest PnLHistoryRecord or None if not found.
        """
        return self.repository.get_latest_record(account_id)
