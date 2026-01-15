"""Business Unit: shared | Status: current.

Alpaca Options API adapter for option chain queries and order placement.

Uses Alpaca's Trading API for options operations:
- /v2/options/contracts - Query option chains
- /v2/orders - Place orders (supports options via OCC symbols)
- /v2/positions - Get positions (includes options)

Note: Alpaca options trading requires enabled options approval on the account.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import requests

from ...errors import TradingClientError
from ...logging import get_logger
from ..schemas.option_contract import OptionContract, OptionType

logger = get_logger(__name__)


class AlpacaOptionsAdapter:
    """Adapter for Alpaca Options API.

    Provides methods for:
    - Option chain queries with filtering
    - Option contract quotes
    - Option order placement and monitoring
    - Option position management
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
    ) -> None:
        """Initialize Alpaca Options adapter.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca API secret key
            paper: If True, use paper trading endpoint

        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper

        # Base URLs
        self._base_url = (
            "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        )
        self._data_url = "https://data.alpaca.markets"

        # Create session with auth headers
        self._session = requests.Session()
        self._session.headers.update(
            {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
                "accept": "application/json",
            }
        )

        logger.info(
            "Initialized Alpaca Options adapter",
            paper=paper,
            base_url=self._base_url,
        )

    def get_option_chain(
        self,
        underlying_symbol: str,
        *,
        expiration_date_gte: date | None = None,
        expiration_date_lte: date | None = None,
        strike_price_gte: Decimal | None = None,
        strike_price_lte: Decimal | None = None,
        option_type: OptionType | None = None,
        limit: int = 100,
    ) -> list[OptionContract]:
        """Get option chain for an underlying symbol.

        Args:
            underlying_symbol: The underlying equity symbol (e.g., "SPY", "QQQ")
            expiration_date_gte: Minimum expiration date (inclusive)
            expiration_date_lte: Maximum expiration date (inclusive)
            strike_price_gte: Minimum strike price
            strike_price_lte: Maximum strike price
            option_type: Filter by PUT or CALL
            limit: Maximum number of contracts to return

        Returns:
            List of OptionContract objects matching the criteria

        Raises:
            TradingClientError: If API request fails

        """
        params: dict[str, Any] = {
            "underlying_symbols": underlying_symbol.upper(),
            "limit": limit,
        }

        if expiration_date_gte:
            params["expiration_date_gte"] = expiration_date_gte.isoformat()
        if expiration_date_lte:
            params["expiration_date_lte"] = expiration_date_lte.isoformat()
        if strike_price_gte:
            params["strike_price_gte"] = str(strike_price_gte)
        if strike_price_lte:
            params["strike_price_lte"] = str(strike_price_lte)
        if option_type:
            params["type"] = option_type.value

        try:
            response = self._session.get(
                f"{self._base_url}/v2/options/contracts",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            contracts = []
            for contract_data in data.get("option_contracts", []):
                contract = self._parse_option_contract(contract_data)
                if contract:
                    contracts.append(contract)

            logger.info(
                "Fetched option chain",
                underlying=underlying_symbol,
                contracts_found=len(contracts),
            )
            return contracts

        except requests.HTTPError as e:
            logger.error(
                "HTTP error fetching option chain",
                underlying=underlying_symbol,
                status_code=e.response.status_code if e.response else None,
                error=str(e),
            )
            raise TradingClientError(f"Option chain query failed: {e}") from e
        except requests.RequestException as e:
            logger.error(
                "Request error fetching option chain",
                underlying=underlying_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Option chain query failed: {e}") from e

    def get_option_quote(self, option_symbol: str) -> OptionContract | None:
        """Get current quote for a specific option contract.

        Args:
            option_symbol: OCC option symbol (e.g., SPY250117P00400000)

        Returns:
            OptionContract with current bid/ask/last, or None if not found

        """
        try:
            response = self._session.get(
                f"{self._base_url}/v2/options/contracts/{option_symbol}",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_option_contract(data)

        except requests.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logger.warning("Option contract not found", symbol=option_symbol)
                return None
            logger.error(
                "HTTP error fetching option quote",
                symbol=option_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Option quote failed: {e}") from e
        except requests.RequestException as e:
            logger.error(
                "Request error fetching option quote",
                symbol=option_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Option quote failed: {e}") from e

    def place_option_order(
        self,
        option_symbol: str,
        quantity: int,
        side: str,
        *,
        order_type: str = "limit",
        limit_price: Decimal | None = None,
        time_in_force: str = "day",
        client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """Place an option order.

        Args:
            option_symbol: OCC option symbol
            quantity: Number of contracts
            side: "buy" or "sell"
            order_type: "market" or "limit"
            limit_price: Required for limit orders
            time_in_force: "day", "gtc", "ioc", "fok"
            client_order_id: Optional client order ID for idempotency

        Returns:
            Order response from Alpaca API

        Raises:
            TradingClientError: If order placement fails
            ValueError: If limit order without limit_price

        """
        if order_type == "limit" and limit_price is None:
            raise ValueError("limit_price required for limit orders")

        order_data: dict[str, Any] = {
            "symbol": option_symbol,
            "qty": str(quantity),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": time_in_force.lower(),
        }

        if limit_price is not None:
            order_data["limit_price"] = str(limit_price)

        if client_order_id:
            order_data["client_order_id"] = client_order_id

        try:
            logger.info(
                "Placing option order",
                symbol=option_symbol,
                side=side,
                qty=quantity,
                order_type=order_type,
                limit_price=str(limit_price) if limit_price else None,
            )

            response = self._session.post(
                f"{self._base_url}/v2/orders",
                json=order_data,
                timeout=30,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()

            logger.info(
                "Option order placed",
                order_id=result.get("id"),
                symbol=option_symbol,
                status=result.get("status"),
            )
            return result

        except requests.HTTPError as e:
            error_body = e.response.json() if e.response else {}
            logger.error(
                "HTTP error placing option order",
                symbol=option_symbol,
                status_code=e.response.status_code if e.response else None,
                error=str(e),
                error_body=error_body,
            )
            raise TradingClientError(f"Option order failed: {e}") from e
        except requests.RequestException as e:
            logger.error(
                "Request error placing option order",
                symbol=option_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Option order failed: {e}") from e

    def get_order(self, order_id: str) -> dict[str, Any]:
        """Get order status by order ID.

        Args:
            order_id: Alpaca order ID

        Returns:
            Order status response

        """
        try:
            response = self._session.get(
                f"{self._base_url}/v2/orders/{order_id}",
                timeout=30,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

        except requests.RequestException as e:
            logger.error("Error fetching order", order_id=order_id, error=str(e))
            raise TradingClientError(f"Order fetch failed: {e}") from e

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order.

        Args:
            order_id: Alpaca order ID

        Returns:
            True if cancellation request accepted

        """
        try:
            response = self._session.delete(
                f"{self._base_url}/v2/orders/{order_id}",
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Order cancelled", order_id=order_id)
            return True

        except requests.HTTPError as e:
            if e.response and e.response.status_code == 422:
                # Order already filled or cancelled
                logger.warning("Order not cancellable", order_id=order_id)
                return False
            raise TradingClientError(f"Order cancel failed: {e}") from e
        except requests.RequestException as e:
            raise TradingClientError(f"Order cancel failed: {e}") from e

    def get_option_positions(self) -> list[dict[str, Any]]:
        """Get all option positions.

        Returns:
            List of option position dictionaries

        """
        try:
            response = self._session.get(
                f"{self._base_url}/v2/positions",
                timeout=30,
            )
            response.raise_for_status()
            positions = response.json()

            # Filter to only option positions (OCC symbol format)
            option_positions = [p for p in positions if self._is_option_symbol(p.get("symbol", ""))]

            logger.info(
                "Fetched option positions",
                total_positions=len(positions),
                option_positions=len(option_positions),
            )
            return option_positions

        except requests.RequestException as e:
            logger.error("Error fetching positions", error=str(e))
            raise TradingClientError(f"Position fetch failed: {e}") from e

    def close_option_position(self, option_symbol: str) -> dict[str, Any]:
        """Close an option position.

        Args:
            option_symbol: OCC option symbol

        Returns:
            Close order response

        """
        try:
            response = self._session.delete(
                f"{self._base_url}/v2/positions/{option_symbol}",
                timeout=30,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()

            logger.info("Closed option position", symbol=option_symbol)
            return result

        except requests.RequestException as e:
            logger.error(
                "Error closing option position",
                symbol=option_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Position close failed: {e}") from e

    def _is_option_symbol(self, symbol: str) -> bool:
        """Check if symbol is an OCC option symbol.

        OCC format: SYMBOL + YYMMDD + C/P + STRIKE*1000
        Example: SPY250117P00400000 (21+ chars for SPY options)
        """
        if len(symbol) < 15:
            return False

        # Check for C/P indicator in expected position
        # For most symbols, it's at position -9 from end
        cp_indicator = symbol[-9:-8] if len(symbol) >= 9 else ""
        return cp_indicator in ("C", "P")

    def _parse_option_contract(self, data: dict[str, Any]) -> OptionContract | None:
        """Parse option contract from API response.

        Args:
            data: Raw contract data from Alpaca API

        Returns:
            OptionContract instance, or None if parsing fails

        """
        try:
            # Parse option type
            raw_type = data.get("type", "").lower()
            option_type = OptionType.PUT if raw_type == "put" else OptionType.CALL

            # Parse expiration date
            exp_str = data.get("expiration_date", "")
            expiration = date.fromisoformat(exp_str) if exp_str else datetime.now(UTC).date()

            return OptionContract(
                symbol=data.get("symbol", ""),
                underlying_symbol=data.get("underlying_symbol", ""),
                option_type=option_type,
                strike_price=Decimal(str(data.get("strike_price", "0"))),
                expiration_date=expiration,
                bid_price=self._parse_decimal(data.get("bid")),
                ask_price=self._parse_decimal(data.get("ask")),
                last_price=self._parse_decimal(data.get("last")),
                volume=int(data.get("volume", 0)),
                open_interest=int(data.get("open_interest", 0)),
                delta=self._parse_decimal(data.get("delta")),
                gamma=self._parse_decimal(data.get("gamma")),
                theta=self._parse_decimal(data.get("theta")),
                vega=self._parse_decimal(data.get("vega")),
                implied_volatility=self._parse_decimal(data.get("implied_volatility")),
            )
        except (ValueError, KeyError) as e:
            logger.warning(
                "Failed to parse option contract",
                error=str(e),
                data=data,
            )
            return None

    @staticmethod
    def _parse_decimal(value: str | float | int | None) -> Decimal | None:
        """Parse value to Decimal, returning None for empty/invalid values."""
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
