"""Business Unit: shared | Status: current.

Alpaca account operations adapter implementing AccountRepository protocol.

This adapter focuses specifically on account-related operations including
account information retrieval, buying power queries, and position lookups.
It delegates to the Alpaca TradingClient for account operations.
"""

from __future__ import annotations

import logging
from typing import Any

from alpaca.trading.client import TradingClient
from alpaca.trading.models import Position, TradeAccount

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_client
from the_alchemiser.shared.protocols.repository import AccountRepository

logger = logging.getLogger(__name__)


class AlpacaAccountAdapter(AccountRepository):
    """Alpaca account operations adapter.
    
    Implements the AccountRepository protocol for all account-related operations
    including account information, buying power, and position queries.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
    ) -> None:
        """Initialize the account adapter.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True)
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        
        # Initialize trading client for account operations
        self._trading_client = create_trading_client(
            api_key=api_key, secret_key=secret_key, paper=paper
        )
        
        logger.info(f"AlpacaAccountAdapter initialized - Paper: {paper}")

    def get_account(self) -> dict[str, Any] | None:
        """Get account information as dictionary."""
        account_obj = self._get_account_object()
        if not account_obj:
            return None
            
        try:
            # Try to get dict representation
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
            "portfolio_value": getattr(account_obj, "portfolio_value", None),
            "equity": getattr(account_obj, "equity", None),
            "last_equity": getattr(account_obj, "last_equity", None),
            "multiplier": getattr(account_obj, "multiplier", None),
            "created_at": getattr(account_obj, "created_at", None),
            "trading_blocked": getattr(account_obj, "trading_blocked", None),
            "transfers_blocked": getattr(account_obj, "transfers_blocked", None),
            "account_blocked": getattr(account_obj, "account_blocked", None),
            "pattern_day_trader": getattr(account_obj, "pattern_day_trader", None),
            "day_trading_buying_power": getattr(account_obj, "day_trading_buying_power", None),
            "regt_buying_power": getattr(account_obj, "regt_buying_power", None),
        }

    def _get_account_object(self) -> TradeAccount | None:
        """Get account object for internal use."""
        try:
            account = self._trading_client.get_account()
            logger.debug("Successfully retrieved account information")
            return account if isinstance(account, TradeAccount) else None
        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        try:
            account = self._get_account_object()
            if account and hasattr(account, "buying_power"):
                bp_raw = getattr(account, "buying_power", None)
                return float(bp_raw) if bp_raw is not None else None
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            return None

    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity."""
        from the_alchemiser.shared.brokers.alpaca_mappers import filter_non_zero_positions
        
        try:
            positions = self._trading_client.get_all_positions()
            return filter_non_zero_positions(list(positions))
            
        except Exception as e:
            logger.error(f"Failed to get positions dict: {e}")
            return {}

    def get_positions(self) -> list[Any]:
        """Get all positions as list of position objects.
        
        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.
        """
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            return list(positions)
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_position(self, symbol: str) -> Position | None:
        """Get position for a specific symbol.
        
        Args:
            symbol: Stock symbol to get position for
            
        Returns:
            Position object or None if no position exists
        """
        try:
            position = self._trading_client.get_open_position(symbol)
            logger.debug(f"Retrieved position for {symbol}")
            return position
        except Exception as e:
            # Not having a position is normal, so log as debug rather than error
            logger.debug(f"No position found for {symbol}: {e}")
            return None