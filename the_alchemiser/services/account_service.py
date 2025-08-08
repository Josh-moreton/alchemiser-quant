"""
Account Service

Unified service for account information, positions and portfolio history.
Merges functionality from core.services.account_service and execution.account_service.
"""

import logging
from typing import Any, Protocol

import requests

from the_alchemiser.domain.models.account import AccountModel, PortfolioHistoryModel
from the_alchemiser.domain.models.position import PositionModel
from the_alchemiser.services.trading_client_service import TradingClientService
from the_alchemiser.domain.types import AccountInfo, PositionInfo, PositionsDict
from the_alchemiser.services.account_utils import extract_comprehensive_account_data


class DataProvider(Protocol):
    """Protocol defining the data provider interface needed by AccountService."""

    def get_positions(self) -> Any:
        """Get all positions."""
        ...

    def get_current_price(self, symbol: str) -> float | int | None:
        """Get current price for a symbol."""
        ...


class AccountService:
    """Unified service for account and position management operations."""

    def __init__(
        self,
        trading_client_service: TradingClientService,
        api_key: str,
        secret_key: str,
        api_endpoint: str,
        data_provider: DataProvider = None,
    ) -> None:
        """
        Initialize account service.

        Args:
            trading_client_service: Trading client service
            api_key: API key for direct API calls
            secret_key: Secret key for direct API calls
            api_endpoint: API endpoint for direct calls
            data_provider: Optional data provider for legacy compatibility
        """
        self._trading_client_service = trading_client_service
        self._api_key = api_key
        self._secret_key = secret_key
        self._api_endpoint = api_endpoint
        self._data_provider = data_provider
        
        # Pre-import the utility function to avoid runtime imports
        if data_provider:
            self._extract_account_data = extract_comprehensive_account_data



    def __init__(
        self,
        trading_client_service: TradingClientService,
        api_key: str,
        secret_key: str,
        api_endpoint: str,
    ) -> None:
        