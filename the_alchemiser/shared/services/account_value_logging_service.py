#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Account Value Logging Service for automated daily portfolio value tracking.

This service integrates with the account management system to automatically
log daily portfolio values for performance tracking and visualization.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from ..persistence.account_value_logger_factory import (
    create_account_value_logger,
    is_account_value_logging_enabled,
)
from ..persistence.base_account_value_logger import AccountValueLoggerProtocol
from ..schemas.account_value_logger import AccountValueEntry
from ..types.account import AccountModel

logger = logging.getLogger(__name__)


class AccountValueLoggingService:
    """Service for automated account value logging.

    This service provides a high-level interface for logging daily portfolio
    values with proper error handling and optional behavior based on configuration.
    """

    def __init__(self, value_logger: AccountValueLoggerProtocol | None = None) -> None:
        """Initialize the account value logging service.

        Args:
            value_logger: Optional account value logger instance. If not provided,
                         one will be created using the factory.

        """
        self._value_logger = value_logger or create_account_value_logger()
        self._enabled = is_account_value_logging_enabled()

    def log_current_account_value(self, account: AccountModel) -> bool:
        """Log the current account value.

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
            self._value_logger.log_account_value(entry)

            logger.info(
                f"Logged account value: ${entry.portfolio_value} for account {entry.account_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to log account value: {e}")
            return False

    def get_account_value_history(
        self, account_id: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[AccountValueEntry]:
        """Get account value history for an account.

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
            from ..schemas.account_value_logger import AccountValueQuery

            filters = AccountValueQuery(
                account_id=account_id, start_date=start_date, end_date=end_date
            )

            entries = list(self._value_logger.query_account_values(filters))
            logger.debug(f"Retrieved {len(entries)} account value entries")
            return entries

        except Exception as e:
            logger.error(f"Failed to retrieve account value history: {e}")
            return []

    def get_latest_account_value(self, account_id: str) -> AccountValueEntry | None:
        """Get the latest logged account value for an account.

        Args:
            account_id: Account identifier

        Returns:
            Latest account value entry or None if not found

        """
        if not self._enabled:
            logger.debug("Account value logging is disabled")
            return None

        try:
            entry = self._value_logger.get_latest_value(account_id)
            if entry:
                logger.debug(f"Retrieved latest account value: ${entry.portfolio_value}")
            else:
                logger.debug("No account value entries found")
            return entry

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
            source="account_value_logging_service",
        )
