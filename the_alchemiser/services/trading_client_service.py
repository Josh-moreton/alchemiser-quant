#!/usr/bin/env python3
"""
Trading Client Service

Handles trading operations via Alpaca API.
Focused on order placement, account data, and positions.
"""

import logging
from typing import Any

from alpaca.trading.client import TradingClient as AlpacaTradingClient


class TradingClientService:
    """Service for trading operations via Alpaca API."""

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """
        Initialize trading client service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading
        self._client = AlpacaTradingClient(api_key, secret_key, paper=paper_trading)

    @property
    def client(self) -> AlpacaTradingClient:
        """Get the underlying Alpaca trading client."""
        return self._client

    def get_account_info(self) -> dict[str, Any] | None:
        """
        Get account information.

        Returns:
            Account information as dict or None if error

        Raises:
            TradingClientError: If account retrieval fails
        """
        try:
            account = self._client.get_account()
            # Convert account object to dict for consistency
            if hasattr(account, "model_dump"):
                return account.model_dump()
            elif hasattr(account, "__dict__"):
                return account.__dict__
            else:
                # Fallback: return as Any and cast
                return dict(account) if account else None

        except Exception as e:
            logging.error(f"Failed to fetch account info: {e}")
            return None

    def get_all_positions(self) -> list[dict[str, Any]]:
        """
        Get all positions.

        Returns:
            List of position dicts

        Raises:
            TradingClientError: If positions retrieval fails
        """
        try:
            positions = self._client.get_all_positions()
            # Convert positions to list of dicts for consistency
            if isinstance(positions, list):
                result: list[dict[str, Any]] = []
                for pos in positions:
                    if hasattr(pos, "model_dump"):
                        result.append(pos.model_dump())
                    elif hasattr(pos, "__dict__"):
                        result.append(pos.__dict__)
                    else:
                        result.append(dict(pos))
                return result
            else:
                # Handle RawData case - return empty list if not a list
                return []

        except Exception as e:
            logging.error(f"Failed to fetch positions: {e}")
            return []
