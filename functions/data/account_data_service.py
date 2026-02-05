"""Business Unit: data | Status: current.

Service for fetching account data from Alpaca and storing in DynamoDB.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)
from the_alchemiser.shared.schemas.account_snapshot import AccountSnapshot

logger = get_logger(__name__)


class AccountDataService:
    """Service for capturing and storing account snapshots."""

    def __init__(self) -> None:
        """Initialize service with Alpaca manager and DynamoDB repository."""
        self.alpaca = AlpacaManager()
        self.repository = AccountSnapshotRepository()

    def capture_account_snapshot(self) -> AccountSnapshot | None:
        """Capture current account state from Alpaca and store in DynamoDB.
        
        Returns:
            AccountSnapshot object if successful, None otherwise.
        """
        try:
            # Fetch account info from Alpaca
            account_info = self.alpaca.get_account_info()
            
            # Get account object for additional fields
            account = self.alpaca.get_account()
            
            # Current timestamp
            now = datetime.now(UTC)
            timestamp_str = now.isoformat()
            
            # Calculate TTL (1 year from now)
            ttl = int((now + timedelta(days=365)).timestamp())
            
            # Convert account info to snapshot
            snapshot = AccountSnapshot(
                snapshot_id="ACCOUNT",
                timestamp=timestamp_str,
                account_number=account.get("account_number", "unknown"),
                status=account.get("status", "UNKNOWN"),
                cash=account_info.cash,
                equity=account_info.equity,
                portfolio_value=account_info.portfolio_value,
                buying_power=account_info.buying_power,
                regt_buying_power=account_info.regt_buying_power,
                daytrading_buying_power=account_info.daytrading_buying_power,
                initial_margin=account_info.initial_margin,
                maintenance_margin=account_info.maintenance_margin,
                multiplier=str(account_info.multiplier),
                last_equity=Decimal(str(account.get("last_equity", "0"))),
                long_market_value=Decimal(str(account.get("long_market_value", "0"))),
                short_market_value=Decimal(str(account.get("short_market_value", "0"))),
                pattern_day_trader=account.get("pattern_day_trader", False),
                trading_blocked=account.get("trading_blocked", False),
                transfers_blocked=account.get("transfers_blocked", False),
                account_blocked=account.get("account_blocked", False),
                currency=account.get("currency", "USD"),
                created_at=account.get("created_at"),
                ttl=ttl,
            )
            
            # Save to DynamoDB
            self.repository.save_snapshot(snapshot)
            
            logger.info(
                "Account snapshot captured successfully",
                extra={
                    "timestamp": timestamp_str,
                    "equity": str(snapshot.equity),
                    "cash": str(snapshot.cash),
                },
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(
                "Failed to capture account snapshot",
                extra={"error": str(e)},
                exc_info=True,
            )
            return None

    def get_latest_snapshot(self) -> AccountSnapshot | None:
        """Get the most recent account snapshot from DynamoDB.
        
        Returns:
            Latest AccountSnapshot or None if not found.
        """
        return self.repository.get_latest_snapshot()

    def get_snapshots_for_period(
        self,
        start_timestamp: str,
        end_timestamp: str | None = None,
    ) -> list[AccountSnapshot]:
        """Get all account snapshots for a time period.
        
        Args:
            start_timestamp: ISO 8601 timestamp to start from.
            end_timestamp: ISO 8601 timestamp to end at (optional).
            
        Returns:
            List of AccountSnapshot objects in chronological order.
        """
        snapshots = self.repository.get_snapshots_since(start_timestamp)
        
        if end_timestamp:
            # Filter out snapshots after end_timestamp
            snapshots = [s for s in snapshots if s.timestamp <= end_timestamp]
        
        return snapshots
