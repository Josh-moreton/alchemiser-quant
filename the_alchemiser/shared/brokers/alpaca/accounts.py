"""Business Unit: shared | Status: current.

Alpaca account management.

Handles account information retrieval, portfolio data, and account status operations.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from alpaca.trading.models import TradeAccount

from .exceptions import normalize_alpaca_error
from .models import AccountInfoModel

if TYPE_CHECKING:
    from .client import AlpacaClient

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages account information and portfolio data."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize with Alpaca client.
        
        Args:
            client: AlpacaClient instance

        """
        self._client = client

    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dict (protocol compliance).
        
        Returns:
            Account information as dictionary, None if unavailable

        """
        return self.get_account_dict()

    def get_account_object(self) -> TradeAccount | None:
        """Get account information as SDK object.
        
        Returns:
            TradeAccount object, None if unavailable

        """
        return self._get_account_object()

    def get_account_dict(self) -> dict[str, Any] | None:
        """Get account information as a plain dictionary for convenience.
        
        Returns:
            Account information as dictionary, None if unavailable

        """
        account_obj = self._get_account_object()
        if not account_obj:
            return None
        
        try:
            # Some SDK objects expose __dict__ with serializable fields
            data = account_obj.__dict__ if hasattr(account_obj, "__dict__") else None
            if isinstance(data, dict):
                return data
        except Exception as exc:
            logger.debug(f"Falling back to manual account dict conversion: {exc}")
        
        # Fallback: build dict from known attributes
        return {
            "id": getattr(account_obj, "id", None),
            "account_number": getattr(account_obj, "account_number", None),
            "status": getattr(account_obj, "status", None),
            "currency": getattr(account_obj, "currency", None),
            "buying_power": getattr(account_obj, "buying_power", None),
            "cash": getattr(account_obj, "cash", None),
            "equity": getattr(account_obj, "equity", None),
            "portfolio_value": getattr(account_obj, "portfolio_value", None),
        }

    def get_account_model(self) -> AccountInfoModel | None:
        """Get account information as typed model.
        
        Returns:
            AccountInfoModel instance, None if unavailable

        """
        account_obj = self._get_account_object()
        if not account_obj:
            return None
        
        try:
            return AccountInfoModel(
                id=getattr(account_obj, "id", None),
                account_number=getattr(account_obj, "account_number", None),
                status=getattr(account_obj, "status", None),
                currency=getattr(account_obj, "currency", None),
                buying_power=self._safe_decimal(getattr(account_obj, "buying_power", None)),
                cash=self._safe_decimal(getattr(account_obj, "cash", None)),
                equity=self._safe_decimal(getattr(account_obj, "equity", None)),
                portfolio_value=self._safe_decimal(getattr(account_obj, "portfolio_value", None)),
            )
        except Exception as e:
            logger.error(f"Failed to create account model: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power.
        
        Returns:
            Buying power as float, None if unavailable
            
        Raises:
            AlpacaAccountError: If operation fails

        """
        try:
            account = self._get_account_object()
            if account and hasattr(account, "buying_power") and account.buying_power is not None:
                return float(account.buying_power)
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            raise normalize_alpaca_error(e, "Get buying power") from e

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value.
        
        Returns:
            Portfolio value as float, None if unavailable
            
        Raises:
            AlpacaAccountError: If operation fails

        """
        try:
            account = self._get_account_object()
            if (
                account
                and hasattr(account, "portfolio_value")
                and account.portfolio_value is not None
            ):
                return float(account.portfolio_value)
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            raise normalize_alpaca_error(e, "Get portfolio value") from e

    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working.
        
        Returns:
            True if connection is valid, False otherwise

        """
        try:
            account = self._get_account_object()
            if account:
                logger.info("Alpaca connection validated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Alpaca connection validation failed: {e}")
            return False

    def _get_account_object(self) -> TradeAccount | None:
        """Get account object for internal use.
        
        Returns:
            TradeAccount object, None if unavailable

        """
        try:
            account = self._client.trading_client.get_account()
            logger.debug("Successfully retrieved account information")
            return account if isinstance(account, TradeAccount) else None
        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            return None

    def _safe_decimal(self, value: Any) -> Decimal | None:
        """Safely convert value to Decimal.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value or None if conversion fails

        """
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None