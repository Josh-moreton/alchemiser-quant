#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Trading Client Service.

Handles trading operations via Alpaca API.
Focused on order placement, account data, and positions.

MIGRATION NOTE: This service now uses AlpacaManager for consolidated Alpaca access.
This provides better error handling, logging, and testing capabilities.
"""

import logging
from typing import Any

from the_alchemiser.services.repository.alpaca_manager import AlpacaManager


class TradingClientService:
    """Service for trading operations via Alpaca API."""

    def __init__(self, api_key: str, secret_key: str, paper_trading: bool = True) -> None:
        """Initialize trading client service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to use paper trading

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_trading = paper_trading
        self._alpaca_manager = AlpacaManager(api_key, secret_key, paper=paper_trading)

    @property
    def client(self) -> AlpacaManager:
        """Get the underlying Alpaca manager."""
        return self._alpaca_manager

    def get_account_info(self) -> dict[str, Any] | None:
        """Get account information.

        Returns:
            Account information as dict or None if error

        Raises:
            TradingClientError: If account retrieval fails

        """
        try:
            account = self._alpaca_manager.get_account()
            # Convert account object to a plain dict first
            if hasattr(account, "model_dump"):
                raw: dict[str, Any] = dict(account.model_dump())
            elif hasattr(account, "__dict__"):
                raw = dict(account.__dict__)
            else:
                raw = dict(account) if account else {}

            if not raw:
                return None

            # Map Alpaca fields to our AccountInfo schema keys
            status_raw = str(raw.get("status", "INACTIVE")).upper()
            status = "ACTIVE" if status_raw == "ACTIVE" else "INACTIVE"

            mapped: dict[str, Any] = {
                "account_id": str(raw.get("account_number") or raw.get("id") or "unknown"),
                "equity": float(raw.get("equity", 0) or 0),
                "cash": float(raw.get("cash", 0) or 0),
                "buying_power": float(raw.get("buying_power", 0) or 0),
                # Alpaca uses daytrade_count
                "day_trades_remaining": int(
                    raw.get("daytrade_count", raw.get("day_trades_remaining", 0)) or 0
                ),
                "portfolio_value": float(raw.get("portfolio_value", 0) or 0),
                "last_equity": float((raw.get("last_equity", raw.get("equity", 0))) or 0),
                "daytrading_buying_power": float(raw.get("daytrading_buying_power", 0) or 0),
                "regt_buying_power": float(
                    raw.get("regt_buying_power", raw.get("buying_power", 0)) or 0
                ),
                "status": status,
            }

            return mapped

        except Exception as e:
            logging.error(f"Failed to fetch account info: {e}")
            return None

    def get_all_positions(self) -> list[dict[str, Any]]:
        """Get all positions.

        Returns:
            List of position dicts

        Raises:
            TradingClientError: If positions retrieval fails

        """
        try:
            positions = self._alpaca_manager.get_positions()
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

        except Exception as e:
            logging.error(f"Failed to fetch positions: {e}")
            return []
