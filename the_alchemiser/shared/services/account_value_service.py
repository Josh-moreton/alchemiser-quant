#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Account Value Service using Trade Ledger for simplified account value tracking.

This service integrates with the enhanced trade ledger system to provide
account value logging capabilities, allowing users to disable full trade
tracking while maintaining account value records for performance visualization.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ..persistence.trade_ledger_factory import (
    get_default_trade_ledger,
    is_account_value_logging_enabled,
)
from ..protocols.trade_ledger import TradeLedger
from ..schemas.trade_ledger import AccountValueEntry, AccountValueQuery
from ..types.account import AccountModel

logger = logging.getLogger(__name__)


class AccountValueService:
    """Service for account value logging using the enhanced trade ledger system.
    
    This service provides a high-level interface for logging daily portfolio
    values with proper error handling and optional behavior based on configuration.
    It extends the existing trade ledger rather than creating a separate module.
    """

    def __init__(self, trade_ledger: TradeLedger | None = None) -> None:
        """Initialize the account value service.
        
        Args:
            trade_ledger: Optional trade ledger instance. If not provided,
                         one will be created using the factory.
        """
        self._trade_ledger = trade_ledger or get_default_trade_ledger()
        self._enabled = is_account_value_logging_enabled()

    def log_current_account_value(self, account: AccountModel) -> bool:
        """Log the current account value using the trade ledger.
        
        Args:
            account: Account model with current portfolio values
            
        Returns:
            True if logging was successful, False otherwise
        """
        if not self._enabled:
            logger.debug("Account value logging is disabled")
            return False

        try:
            entry = self._create_account_value_entry(account)
            
            # Use the trade ledger's account value logging capability
            if hasattr(self._trade_ledger, 'log_account_value'):
                self._trade_ledger.log_account_value(entry)
                logger.info(
                    f"Logged account value: ${entry.portfolio_value} for account {entry.account_id}"
                )
                return True
            else:
                logger.warning("Trade ledger does not support account value logging")
                return False

        except Exception as e:
            logger.error(f"Failed to log account value: {e}")
            return False

    def get_account_value_history(
        self, 
        account_id: str, 
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> list[AccountValueEntry]:
        """Get account value history for an account using the trade ledger.
        
        Args:
            account_id: Account identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of account value entries sorted by timestamp
        """
        if not self._enabled:
            logger.debug("Account value logging is disabled")
            return []

        try:
            filters = AccountValueQuery(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Use the trade ledger's account value querying capability
            if hasattr(self._trade_ledger, 'query_account_values'):
                entries: list[AccountValueEntry] = list(self._trade_ledger.query_account_values(filters))
                logger.debug(f"Retrieved {len(entries)} account value entries")
                return entries
            else:
                logger.warning("Trade ledger does not support account value querying")
                return []

        except Exception as e:
            logger.error(f"Failed to retrieve account value history: {e}")
            return []

    def get_latest_account_value(self, account_id: str) -> AccountValueEntry | None:
        """Get the latest logged account value for an account using the trade ledger.
        
        Args:
            account_id: Account identifier
            
        Returns:
            Latest account value entry or None if not found
        """
        if not self._enabled:
            logger.debug("Account value logging is disabled")
            return None

        try:
            # Use the trade ledger's latest account value capability
            if hasattr(self._trade_ledger, 'get_latest_account_value'):
                entry: AccountValueEntry | None = self._trade_ledger.get_latest_account_value(account_id)
                if entry:
                    logger.debug(f"Retrieved latest account value: ${entry.portfolio_value}")
                else:
                    logger.debug("No account value entries found")
                return entry
            else:
                logger.warning("Trade ledger does not support latest account value lookup")
                return None

        except Exception as e:
            logger.error(f"Failed to retrieve latest account value: {e}")
            return None

    def is_enabled(self) -> bool:
        """Check if account value logging is enabled.
        
        Returns:
            True if logging is enabled
        """
        return self._enabled

    def _create_account_value_entry(self, account: AccountModel) -> AccountValueEntry:
        """Create an account value entry from an account model.
        
        Args:
            account: Account model
            
        Returns:
            Account value entry
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).replace(microsecond=0)
        
        return AccountValueEntry(
            entry_id=entry_id,
            account_id=account.account_id,
            portfolio_value=Decimal(str(account.portfolio_value)),
            cash=Decimal(str(account.cash)),
            equity=Decimal(str(account.equity)),
            timestamp=timestamp,
            source="account_value_service"
        )