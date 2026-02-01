"""Business Unit: shared | Status: current.

Alpaca Options API adapter for option chain queries and order placement.

Uses Alpaca's Trading API for options operations:
- /v2/options/contracts - Query option chains
- /v2/orders - Place orders (supports options via OCC symbols)
- /v2/positions - Get positions (includes options)

Note: Alpaca options trading requires enabled options approval on the account.
"""

from __future__ import annotations

import time
from datetime import UTC, date, datetime
from decimal import Decimal
from secrets import randbelow
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

    # Rate limiting constants for options quote fetching
    _QUOTE_BATCH_SIZE = 50  # Conservative batch size (API max is 100)
    _INTER_BATCH_DELAY_SECONDS = 0.3  # Delay between batches to avoid rate limits
    _MAX_QUOTE_RETRIES = 3  # Retry attempts for transient failures
    _BASE_RETRY_DELAY_SECONDS = 1.0  # Base delay for exponential backoff
    _JITTER_FACTOR = 0.2  # ±20% jitter to avoid thundering herd

    def get_option_quotes_batch(
        self, option_symbols: list[str]
    ) -> dict[str, dict[str, Decimal | None]]:
        """Get quotes for multiple option contracts with rate limiting.

        Uses the Alpaca Market Data API for batch quote fetching with
        defensive rate limiting:
        - Smaller batch sizes (50 vs 100 max)
        - Inter-batch delays to stay under rate limits
        - Automatic retry with exponential backoff on 429/5xx

        Args:
            option_symbols: List of OCC option symbols

        Returns:
            Dict mapping symbol to quote data:
            {
                "SPY250117P00400000": {
                    "bid_price": Decimal("1.23"),
                    "ask_price": Decimal("1.25"),
                },
                ...
            }

        """
        if not option_symbols:
            return {}

        quotes: dict[str, dict[str, Decimal | None]] = {}
        total_batches = (len(option_symbols) + self._QUOTE_BATCH_SIZE - 1) // self._QUOTE_BATCH_SIZE

        for batch_idx, i in enumerate(range(0, len(option_symbols), self._QUOTE_BATCH_SIZE)):
            batch = option_symbols[i : i + self._QUOTE_BATCH_SIZE]
            batch_quotes = self._fetch_quotes_batch_with_retry(batch)
            quotes.update(batch_quotes)

            # Add inter-batch delay (except after last batch)
            if batch_idx < total_batches - 1:
                time.sleep(self._INTER_BATCH_DELAY_SECONDS)

        logger.info(
            "Completed batch quote fetching",
            total_symbols=len(option_symbols),
            quotes_received=len(quotes),
            batches=total_batches,
        )
        return quotes

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied

        """
        base_delay: float = self._BASE_RETRY_DELAY_SECONDS * (2**attempt)
        # Add ±20% jitter using cryptographic randomness
        jitter_range = int(base_delay * self._JITTER_FACTOR * 1000)
        jitter: float = (
            (randbelow(jitter_range * 2) - jitter_range) / 1000 if jitter_range > 0 else 0.0
        )
        return base_delay + jitter

    def _is_retryable_error(self, response: requests.Response | None) -> bool:
        """Check if HTTP response indicates a retryable error.

        Args:
            response: HTTP response object (may be None)

        Returns:
            True if error is retryable (429 or 5xx)

        """
        if response is None:
            return True  # Network errors are retryable
        return response.status_code == 429 or response.status_code >= 500

    def _get_retry_after(self, response: requests.Response | None) -> float | None:
        """Extract Retry-After header value if present.

        Args:
            response: HTTP response object

        Returns:
            Retry delay in seconds, or None if not specified

        """
        if response is None:
            return None
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                return None
        return None

    def _fetch_quotes_batch_with_retry(
        self, symbols: list[str]
    ) -> dict[str, dict[str, Decimal | None]]:
        """Fetch option quotes with automatic retry on transient failures.

        Implements exponential backoff with jitter for rate limit (429)
        and server errors (5xx). Respects Retry-After header if present.

        Args:
            symbols: List of option symbols (max 50 recommended)

        Returns:
            Dict mapping symbol to quote data (empty dict on persistent failure)

        """
        last_error: Exception | None = None

        for attempt in range(self._MAX_QUOTE_RETRIES):
            try:
                response = self._session.get(
                    f"{self._data_url}/v1beta1/options/quotes/latest",
                    params={"symbols": ",".join(symbols)},
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                quotes: dict[str, dict[str, Decimal | None]] = {}
                for symbol, quote_data in data.get("quotes", {}).items():
                    quotes[symbol] = {
                        "bid_price": self._parse_decimal(quote_data.get("bp")),
                        "ask_price": self._parse_decimal(quote_data.get("ap")),
                    }

                logger.debug(
                    "Fetched option quotes batch",
                    requested=len(symbols),
                    received=len(quotes),
                    attempt=attempt + 1,
                )
                return quotes

            except requests.HTTPError as e:
                last_error = e
                response = e.response

                if not self._is_retryable_error(response):
                    # Non-retryable error (4xx except 429) - fail immediately
                    logger.warning(
                        "Non-retryable HTTP error fetching quotes",
                        symbols_count=len(symbols),
                        status_code=response.status_code if response else None,
                        error=str(e),
                    )
                    return {}

                if attempt < self._MAX_QUOTE_RETRIES - 1:
                    # Calculate delay: prefer Retry-After header, else use backoff
                    retry_after = self._get_retry_after(response)
                    delay = retry_after if retry_after else self._calculate_retry_delay(attempt)

                    logger.warning(
                        "Retryable HTTP error, backing off",
                        symbols_count=len(symbols),
                        status_code=response.status_code if response else None,
                        attempt=attempt + 1,
                        max_retries=self._MAX_QUOTE_RETRIES,
                        delay_seconds=round(delay, 2),
                        retry_after_header=retry_after,
                    )
                    time.sleep(delay)

            except requests.RequestException as e:
                last_error = e

                if attempt < self._MAX_QUOTE_RETRIES - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Network error fetching quotes, retrying",
                        symbols_count=len(symbols),
                        attempt=attempt + 1,
                        max_retries=self._MAX_QUOTE_RETRIES,
                        delay_seconds=round(delay, 2),
                        error=str(e),
                    )
                    time.sleep(delay)

        # All retries exhausted
        logger.error(
            "Failed to fetch option quotes after all retries",
            symbols_count=len(symbols),
            max_retries=self._MAX_QUOTE_RETRIES,
            last_error=str(last_error) if last_error else "unknown",
        )
        return {}

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
            # Options prices must be rounded to 2 decimal places
            rounded_price = limit_price.quantize(Decimal("0.01"))
            order_data["limit_price"] = str(rounded_price)

        if client_order_id:
            order_data["client_order_id"] = client_order_id

        try:
            logger.info(
                "Placing option order",
                symbol=option_symbol,
                side=side,
                qty=quantity,
                order_type=order_type,
                limit_price=str(order_data.get("limit_price")) if limit_price else None,
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
            # Capture full error response for debugging
            error_body: dict[str, Any] = {}
            error_text: str = ""
            if e.response is not None:
                error_text = e.response.text
                try:
                    error_body = e.response.json()
                except (ValueError, requests.exceptions.JSONDecodeError):
                    error_body = {"raw_response": error_text}
            logger.error(
                "HTTP error placing option order",
                symbol=option_symbol,
                status_code=e.response.status_code if e.response else None,
                error=str(e),
                error_body=error_body,
                error_text=error_text,
                request_data=order_data,
            )
            raise TradingClientError(
                f"Option order failed: {e} - Response: {error_text or 'No response body'}"
            ) from e
        except requests.RequestException as e:
            logger.error(
                "Request error placing option order",
                symbol=option_symbol,
                error=str(e),
            )
            raise TradingClientError(f"Option order failed: {e}") from e

    def place_spread_order(
        self,
        long_leg_symbol: str,
        short_leg_symbol: str,
        quantity: int,
        *,
        long_leg_limit_price: Decimal | None = None,
        short_leg_limit_price: Decimal | None = None,
        time_in_force: str = "day",
        client_order_id: str | None = None,
        max_retries: int = 5,
        base_retry_delay: float = 0.5,
        max_execution_time_seconds: int = 180,
    ) -> dict[str, Any]:
        """Place a put spread order (buy long leg, sell short leg).

        Note: Alpaca does not support native multi-leg orders via API.
        This method executes legs sequentially with robust retry logic:
        1. Place long leg (buy)
        2. Attempt short leg with limit order (up to 3 retries with backoff)
        3. If limit retries exhausted, escalate to market order (2 more attempts)
        4. If all retries fail, attempt compensating close of long leg

        RISK WARNING: If all short leg retries fail AND the compensating close
        of the long leg also fails, the account will be left with a naked long
        option position. This requires manual reconciliation. Monitor for
        "manual reconciliation required" log messages.

        Args:
            long_leg_symbol: OCC symbol for the long put (e.g., 30-delta)
            short_leg_symbol: OCC symbol for the short put (e.g., 10-delta)
            quantity: Number of spreads (contracts per leg)
            long_leg_limit_price: Limit price for long leg (if None, uses market)
            short_leg_limit_price: Limit price for short leg (if None, uses market)
            time_in_force: "day", "gtc", "ioc", "fok"
            client_order_id: Base client order ID for idempotency (derives -L/-S suffixes)
            max_retries: Maximum total retry attempts for short leg (default: 5)
            base_retry_delay: Base delay in seconds for exponential backoff (default: 0.5)
            max_execution_time_seconds: Maximum time to complete spread (default: 180)

        Returns:
            Dictionary with both order responses

        Raises:
            TradingClientError: If either leg fails to execute (after retries and compensating)

        """
        import time as time_module

        # Derive per-leg client order IDs for idempotency
        long_client_id = f"{client_order_id}-L" if client_order_id else None
        short_client_id = f"{client_order_id}-S" if client_order_id else None

        logger.info(
            "Placing put spread order with enhanced retry logic",
            long_leg=long_leg_symbol,
            short_leg=short_leg_symbol,
            quantity=quantity,
            client_order_id=client_order_id,
            max_retries=max_retries,
            max_execution_time_seconds=max_execution_time_seconds,
        )

        long_order = None
        start_time = time_module.time()

        # Constants for retry escalation
        LIMIT_ORDER_RETRIES = 3  # First 3 attempts use limit orders
        COMPENSATING_CLOSE_RETRIES = 3  # Retry compensating close up to 3 times

        try:
            # Execute long leg first (buy)
            long_order = self.place_option_order(
                option_symbol=long_leg_symbol,
                quantity=quantity,
                side="buy",
                order_type="limit" if long_leg_limit_price else "market",
                limit_price=long_leg_limit_price,
                time_in_force=time_in_force,
                client_order_id=long_client_id,
            )

            # Execute short leg (sell) with enhanced retry logic
            short_order = None
            last_short_error: TradingClientError | None = None

            for attempt in range(max_retries):
                # Check total execution time
                elapsed = time_module.time() - start_time
                if elapsed > max_execution_time_seconds:
                    logger.error(
                        "Spread execution timeout - aborting short leg attempts",
                        long_leg=long_leg_symbol,
                        short_leg=short_leg_symbol,
                        elapsed_seconds=elapsed,
                        max_execution_time_seconds=max_execution_time_seconds,
                        alert_required=True,
                    )
                    raise TradingClientError(f"Spread execution timeout after {elapsed:.1f}s")

                # Determine order type: limit for first 3 attempts, market for remaining
                use_market_order = attempt >= LIMIT_ORDER_RETRIES
                order_type = (
                    "market"
                    if use_market_order
                    else ("limit" if short_leg_limit_price else "market")
                )
                current_limit_price = None if use_market_order else short_leg_limit_price

                if use_market_order and attempt == LIMIT_ORDER_RETRIES:
                    logger.warning(
                        "Escalating to market order after limit order failures",
                        short_leg=short_leg_symbol,
                        attempt=attempt + 1,
                        limit_attempts_exhausted=LIMIT_ORDER_RETRIES,
                    )

                try:
                    short_order = self.place_option_order(
                        option_symbol=short_leg_symbol,
                        quantity=quantity,
                        side="sell",
                        order_type=order_type,
                        limit_price=current_limit_price,
                        time_in_force=time_in_force,
                        client_order_id=f"{short_client_id}-{attempt}" if short_client_id else None,
                    )
                    break  # Success, exit retry loop
                except TradingClientError as e:
                    last_short_error = e
                    if attempt < max_retries - 1:
                        delay = base_retry_delay * (2 ** min(attempt, 3))  # Cap backoff at 8x base
                        logger.warning(
                            "Short leg failed, retrying with backoff",
                            short_leg=short_leg_symbol,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay_seconds=delay,
                            order_type=order_type,
                            error=str(e),
                        )
                        time_module.sleep(delay)

            # If all retries failed, raise to trigger compensating close
            if short_order is None:
                if last_short_error is not None:
                    raise last_short_error
                raise TradingClientError("Short leg order failed without error captured")

            logger.info(
                "Put spread order placed successfully",
                long_order_id=long_order.get("id"),
                short_order_id=short_order.get("id"),
                long_leg=long_leg_symbol,
                short_leg=short_leg_symbol,
                total_execution_time_seconds=time_module.time() - start_time,
            )

            return {
                "long_leg": long_order,
                "short_leg": short_order,
                "spread_type": "put_spread",
            }

        except TradingClientError as e:
            # If long leg succeeded but short leg failed, attempt compensating close
            if long_order is not None:
                logger.warning(
                    "Short leg failed after long leg succeeded, attempting compensating close",
                    long_leg=long_leg_symbol,
                    long_order_id=long_order.get("id"),
                    error=str(e),
                )

                # Retry compensating close with bounded attempts
                compensating_success = False
                for close_attempt in range(COMPENSATING_CLOSE_RETRIES):
                    try:
                        self.close_option_position(long_leg_symbol)
                        logger.info(
                            "Compensating close succeeded for long leg",
                            long_leg=long_leg_symbol,
                            close_attempt=close_attempt + 1,
                        )
                        compensating_success = True
                        break
                    except TradingClientError as close_error:
                        if close_attempt < COMPENSATING_CLOSE_RETRIES - 1:
                            delay = base_retry_delay * (2**close_attempt)
                            logger.warning(
                                "Compensating close failed, retrying",
                                long_leg=long_leg_symbol,
                                close_attempt=close_attempt + 1,
                                max_close_retries=COMPENSATING_CLOSE_RETRIES,
                                delay_seconds=delay,
                                error=str(close_error),
                            )
                            time_module.sleep(delay)
                        else:
                            logger.error(
                                "Compensating close FAILED after all retries - "
                                "MANUAL RECONCILIATION REQUIRED",
                                long_leg=long_leg_symbol,
                                long_order_id=long_order.get("id"),
                                close_error=str(close_error),
                                close_attempts=COMPENSATING_CLOSE_RETRIES,
                                alert_required=True,
                            )

                if not compensating_success:
                    logger.error(
                        "CRITICAL: Spread incomplete with naked long position",
                        long_leg=long_leg_symbol,
                        short_leg=short_leg_symbol,
                        long_order_id=long_order.get("id"),
                        alert_required=True,
                    )

            logger.error(
                "Failed to place spread order",
                long_leg=long_leg_symbol,
                short_leg=short_leg_symbol,
                long_leg_placed=long_order is not None,
                error=str(e),
            )
            raise

    def close_spread_position(
        self,
        long_leg_symbol: str,
        short_leg_symbol: str,
    ) -> dict[str, Any]:
        """Close a spread position (both legs).

        Closes the short leg first (buy-to-close) to avoid leaving
        the account temporarily naked short if failures occur.

        Args:
            long_leg_symbol: OCC symbol for the long put
            short_leg_symbol: OCC symbol for the short put

        Returns:
            Dictionary with both close order responses

        Raises:
            TradingClientError: If either leg fails to close

        """
        logger.info(
            "Closing put spread position",
            long_leg=long_leg_symbol,
            short_leg=short_leg_symbol,
        )

        short_close = None
        long_close = None

        try:
            # Close short leg FIRST (buy to close) to avoid naked short exposure
            short_close = self.close_option_position(short_leg_symbol)

            # Close long leg (sell to close)
            long_close = self.close_option_position(long_leg_symbol)

            logger.info(
                "Put spread position closed",
                long_leg=long_leg_symbol,
                short_leg=short_leg_symbol,
            )

            return {
                "long_leg": long_close,
                "short_leg": short_close,
            }

        except TradingClientError as e:
            # Log partial state for reconciliation
            logger.error(
                "Failed to close spread position",
                long_leg=long_leg_symbol,
                short_leg=short_leg_symbol,
                short_leg_closed=short_close is not None,
                long_leg_closed=long_close is not None,
                error=str(e),
            )
            raise

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
                volume=int(data.get("volume") or 0),
                open_interest=int(data.get("open_interest") or 0),
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
