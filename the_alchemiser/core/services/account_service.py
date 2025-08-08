"""
Account Service

Dedicated service for account information, positions and portfolio history.
Separates account operations from market data responsibilities.
"""

import logging
from typing import Any

import requests

from the_alchemiser.domain.models.account import AccountModel, PortfolioHistoryModel
from the_alchemiser.domain.models.position import PositionModel
from the_alchemiser.services.trading_client_service import TradingClientService


class AccountService:
    """Service for account and position management operations."""

    def __init__(
        self,
        trading_client_service: TradingClientService,
        api_key: str,
        secret_key: str,
        api_endpoint: str,
    ) -> None:
        """
        Initialize account service.

        Args:
            trading_client_service: Trading client service
            api_key: API key for direct API calls
            secret_key: Secret key for direct API calls
            api_endpoint: API endpoint for direct calls
        """
        self._trading_client_service = trading_client_service
        self._api_key = api_key
        self._secret_key = secret_key
        self._api_endpoint = api_endpoint

    def get_account_info(self) -> AccountModel | None:
        """
        Get account information as a typed model.

        Returns:
            AccountModel or None if error
        """
        try:
            account_data = self._trading_client_service.get_account_info()
            if account_data:
                return AccountModel.from_dict(account_data)
            return None
        except Exception as e:
            logging.error(f"Error getting account info: {e}")
            return None

    def get_account_info_dict(self) -> dict[str, Any] | None:
        """
        Get account information as dictionary (backward compatibility).

        Returns:
            Account information as dict or None if error
        """
        return self._trading_client_service.get_account_info()

    def get_all_positions(self) -> list[PositionModel]:
        """
        Get all positions as typed models.

        Returns:
            List of PositionModel objects
        """
        try:
            positions_data = self._trading_client_service.get_all_positions()
            return [PositionModel.from_dict(pos) for pos in positions_data]
        except Exception as e:
            logging.error(f"Error getting positions: {e}")
            return []

    def get_all_positions_dict(self) -> list[dict[str, Any]]:
        """
        Get all positions as dictionaries (backward compatibility).

        Returns:
            List of position dictionaries
        """
        return self._trading_client_service.get_all_positions()

    def get_position_by_symbol(self, symbol: str) -> PositionModel | None:
        """
        Get position for a specific symbol.

        Args:
            symbol: Stock symbol

        Returns:
            PositionModel or None if not found
        """
        positions = self.get_all_positions()
        for position in positions:
            if position.symbol == symbol:
                return position
        return None

    def get_open_positions(self) -> list[PositionModel]:
        """
        Get only open positions (non-zero quantity).

        Returns:
            List of open PositionModel objects
        """
        all_positions = self.get_all_positions()
        return [pos for pos in all_positions if pos.qty != 0]

    def get_profitable_positions(self) -> list[PositionModel]:
        """
        Get positions that are currently profitable.

        Returns:
            List of profitable PositionModel objects
        """
        positions = self.get_all_positions()
        return [pos for pos in positions if pos.is_profitable]

    def get_losing_positions(self) -> list[PositionModel]:
        """
        Get positions that are currently losing money.

        Returns:
            List of losing PositionModel objects
        """
        positions = self.get_all_positions()
        return [pos for pos in positions if not pos.is_profitable and pos.qty != 0]

    def get_portfolio_history(
        self,
        intraday_reporting: str = "market_hours",
        pnl_reset: str = "per_day",
        timeframe: str = "1D",
    ) -> PortfolioHistoryModel | None:
        """
        Get portfolio history as a typed model.

        Args:
            intraday_reporting: Intraday reporting mode
            pnl_reset: P&L reset mode
            timeframe: Time frame

        Returns:
            PortfolioHistoryModel or None if error
        """
        try:
            history_data = self._get_portfolio_history_raw(intraday_reporting, pnl_reset, timeframe)
            if history_data:
                return PortfolioHistoryModel.from_dict(history_data)
            return None
        except Exception as e:
            logging.error(f"Error getting portfolio history: {e}")
            return None

    def get_portfolio_history_dict(
        self,
        intraday_reporting: str = "market_hours",
        pnl_reset: str = "per_day",
        timeframe: str = "1D",
    ) -> dict[str, Any]:
        """
        Get portfolio history as dictionary (backward compatibility).

        Args:
            intraday_reporting: Intraday reporting mode
            pnl_reset: P&L reset mode
            timeframe: Time frame

        Returns:
            Portfolio history dictionary
        """
        try:
            return self._get_portfolio_history_raw(intraday_reporting, pnl_reset, timeframe) or {}
        except Exception as e:
            logging.error(f"Error getting portfolio history: {e}")
            return {}

    def _get_portfolio_history_raw(
        self, intraday_reporting: str, pnl_reset: str, timeframe: str
    ) -> dict[str, Any] | None:
        """Get raw portfolio history data via direct API call."""
        url = f"{self._api_endpoint}/account/portfolio/history"
        params = {
            "intraday_reporting": intraday_reporting,
            "pnl_reset": pnl_reset,
            "timeframe": timeframe,
        }
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching portfolio history: {e}")
            return None

    def get_account_activities(
        self, activity_type: str = "FILL", direction: str = "desc", page_size: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get account activities.

        Args:
            activity_type: Type of activity to retrieve
            direction: Sort direction
            page_size: Number of results per page

        Returns:
            List of activity dictionaries
        """
        url = f"{self._api_endpoint}/account/activities/{activity_type}"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
        }
        params = {"direction": direction, "page_size": min(page_size, 100)}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching account activities: {e}")
            return []

    def get_total_portfolio_value(self) -> float:
        """
        Get total portfolio value.

        Returns:
            Total portfolio value or 0.0 if error
        """
        account = self.get_account_info()
        return account.portfolio_value if account else 0.0

    def get_cash_balance(self) -> float:
        """
        Get cash balance.

        Returns:
            Cash balance or 0.0 if error
        """
        account = self.get_account_info()
        return account.cash if account else 0.0

    def get_buying_power(self) -> float:
        """
        Get buying power.

        Returns:
            Buying power or 0.0 if error
        """
        account = self.get_account_info()
        return account.buying_power if account else 0.0

    def get_day_trades_remaining(self) -> int:
        """
        Get remaining day trades.

        Returns:
            Number of day trades remaining
        """
        account = self.get_account_info()
        return account.day_trades_remaining if account else 0

    def is_account_active(self) -> bool:
        """
        Check if account is active.

        Returns:
            True if account is active
        """
        account = self.get_account_info()
        return account.status == "ACTIVE" if account else False

    def get_positions_summary(self) -> dict[str, Any]:
        """
        Get summary of positions.

        Returns:
            Summary dictionary with position statistics
        """
        positions = self.get_all_positions()

        if not positions:
            return {
                "total_positions": 0,
                "profitable_positions": 0,
                "losing_positions": 0,
                "total_unrealized_pnl": 0.0,
                "largest_position_value": 0.0,
                "smallest_position_value": 0.0,
            }

        profitable = [pos for pos in positions if pos.is_profitable and pos.qty != 0]
        losing = [pos for pos in positions if not pos.is_profitable and pos.qty != 0]

        total_unrealized_pnl = sum(pos.unrealized_pl for pos in positions)
        position_values = [abs(pos.market_value) for pos in positions if pos.qty != 0]

        return {
            "total_positions": len([pos for pos in positions if pos.qty != 0]),
            "profitable_positions": len(profitable),
            "losing_positions": len(losing),
            "total_unrealized_pnl": total_unrealized_pnl,
            "largest_position_value": max(position_values) if position_values else 0.0,
            "smallest_position_value": min(position_values) if position_values else 0.0,
        }
