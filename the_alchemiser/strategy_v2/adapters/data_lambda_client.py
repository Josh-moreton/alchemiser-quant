"""Business Unit: strategy | Status: current.

Data Lambda client for fetching market data.

This client invokes the Data Lambda synchronously to fetch historical bars,
keeping pyarrow/Parquet dependencies in the Data Lambda only. Strategy Lambda
uses this to get market data for indicator computation.

When cache is empty (no bars returned), this client automatically triggers
a refresh_single operation to fetch data from Alpaca, then retries get_bars.

Architecture:
    Strategy Lambda -> Data Lambda (get_bars) -> S3 Parquet
                            |
                            v (on cache miss)
    Strategy Lambda -> Data Lambda (refresh_single) -> Alpaca -> S3
                            |
                            v
    Strategy Lambda -> Data Lambda (get_bars) -> S3 Parquet
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = get_logger(__name__)


class DataLambdaError(Exception):
    """Error invoking Data Lambda."""


class DataLambdaClient(MarketDataPort):
    """Client for invoking Data Lambda to fetch market data.

    This client enables the Strategy Lambda to fetch bars from S3 without
    including pyarrow in its layer. The Data Lambda handles all Parquet I/O.

    When bars are not found in S3 cache, this client triggers a refresh_single
    operation to fetch data from Alpaca on-demand, then retries the get_bars.

    Attributes:
        function_name: Name of the Data Lambda function
        enable_refresh_on_miss: Whether to trigger data refresh on cache miss

    """

    def __init__(
        self,
        function_name: str | None = None,
        *,
        enable_refresh_on_miss: bool = True,
    ) -> None:
        """Initialize Data Lambda client.

        Args:
            function_name: Data Lambda function name. Defaults to DATA_FUNCTION_NAME env var.
            enable_refresh_on_miss: If True, triggers refresh_single when cache miss occurs.

        """
        self.function_name = function_name or os.environ.get(
            "DATA_FUNCTION_NAME", "alchemiser-DataFunction"
        )
        self._client: Any = None
        self._enable_refresh_on_miss = enable_refresh_on_miss

        logger.info(
            "DataLambdaClient initialized",
            function_name=self.function_name,
            refresh_on_miss=enable_refresh_on_miss,
        )

    @property
    def client(self) -> Any:  # noqa: ANN401
        """Lazy-load boto3 Lambda client."""
        if self._client is None:
            import boto3

            self._client = boto3.client("lambda")
        return self._client

    def _refresh_symbol(self, symbol_str: str, correlation_id: str = "unknown") -> bool:
        """Trigger Data Lambda to refresh a single symbol from Alpaca.

        Args:
            symbol_str: Ticker symbol
            correlation_id: Correlation ID for tracing

        Returns:
            True if refresh succeeded, False otherwise

        """
        request_payload = {
            "action": "refresh_single",
            "symbol": symbol_str,
            "correlation_id": correlation_id,
        }

        logger.info(
            "Triggering refresh_single for cache miss",
            function_name=self.function_name,
            symbol=symbol_str,
            correlation_id=correlation_id,
        )

        try:
            response = self.client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(request_payload),
            )

            response_payload = json.loads(response["Payload"].read().decode("utf-8"))

            if response.get("FunctionError"):
                error_msg = response_payload.get("errorMessage", "Unknown error")
                logger.error(
                    "refresh_single returned error",
                    function_name=self.function_name,
                    symbol=symbol_str,
                    error=error_msg,
                )
                return False

            status_code = response_payload.get("statusCode", 500)
            if status_code == 200:
                logger.info(
                    "refresh_single completed successfully",
                    symbol=symbol_str,
                    correlation_id=correlation_id,
                )
                return True

            body = response_payload.get("body", {})
            logger.warning(
                "refresh_single returned non-200 status",
                symbol=symbol_str,
                status_code=status_code,
                message=body.get("message", "Unknown"),
            )
            return False

        except Exception as e:
            logger.error(
                "Failed to invoke refresh_single",
                symbol=symbol_str,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def _fetch_bars_from_lambda(
        self, symbol_str: str, period: str, timeframe: str
    ) -> list[BarModel]:
        """Invoke get_bars on Data Lambda and parse response.

        Args:
            symbol_str: Ticker symbol string
            period: Lookback period
            timeframe: Bar interval

        Returns:
            List of BarModel objects

        Raises:
            DataLambdaError: If invocation fails

        """
        request_payload = {
            "action": "get_bars",
            "symbol": symbol_str,
            "period": period,
            "timeframe": timeframe,
        }

        response = self.client.invoke(
            FunctionName=self.function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(request_payload),
        )

        response_payload = json.loads(response["Payload"].read().decode("utf-8"))

        if response.get("FunctionError"):
            error_msg = response_payload.get("errorMessage", "Unknown error")
            logger.error(
                "Data Lambda returned error",
                function_name=self.function_name,
                error=error_msg,
            )
            raise DataLambdaError(f"Data Lambda error: {error_msg}")

        status_code = response_payload.get("statusCode", 500)
        body = response_payload.get("body", {})

        if status_code != 200:
            error_msg = body.get("message", "Unknown error")
            logger.error(
                "Data Lambda returned non-200 status",
                function_name=self.function_name,
                status_code=status_code,
                error=error_msg,
            )
            raise DataLambdaError(f"Data Lambda returned {status_code}: {error_msg}")

        # Parse bars from response
        bars_data = body.get("bars", [])
        bars: list[BarModel] = []

        for bar_dict in bars_data:
            ts_str = bar_dict["timestamp"]
            # Parse ISO timestamp
            if ts_str.endswith("Z"):
                ts_str = ts_str[:-1] + "+00:00"
            ts = datetime.fromisoformat(ts_str)

            bar = BarModel(
                symbol=bar_dict["symbol"],
                timestamp=ts,
                open=Decimal(bar_dict["open"]),
                high=Decimal(bar_dict["high"]),
                low=Decimal(bar_dict["low"]),
                close=Decimal(bar_dict["close"]),
                volume=int(bar_dict["volume"]),
            )
            bars.append(bar)

        return bars

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars by invoking Data Lambda.

        If no bars are returned from the S3 cache and refresh_on_miss is enabled,
        this method will trigger a refresh_single operation to fetch data from
        Alpaca, then retry the get_bars request.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (e.g., "1Day")

        Returns:
            List of BarModel objects, oldest first

        Raises:
            DataLambdaError: If Data Lambda invocation fails

        """
        symbol_str = str(symbol)

        logger.debug(
            "Invoking Data Lambda for bars",
            function_name=self.function_name,
            symbol=symbol_str,
            period=period,
            timeframe=timeframe,
        )

        try:
            # First attempt: get from cache
            bars = self._fetch_bars_from_lambda(symbol_str, period, timeframe)

            if bars:
                logger.debug(
                    "Data Lambda returned bars from cache",
                    symbol=symbol_str,
                    bars_count=len(bars),
                )
                return bars

            # Cache miss - no bars returned
            if not self._enable_refresh_on_miss:
                logger.warning(
                    "Cache miss but refresh_on_miss disabled",
                    symbol=symbol_str,
                )
                return []

            # Trigger refresh and retry
            logger.info(
                "Cache miss - triggering on-demand refresh",
                symbol=symbol_str,
                period=period,
            )

            refresh_success = self._refresh_symbol(symbol_str)
            if not refresh_success:
                logger.warning(
                    "On-demand refresh failed, returning empty bars",
                    symbol=symbol_str,
                )
                return []

            # Retry get_bars after refresh
            bars = self._fetch_bars_from_lambda(symbol_str, period, timeframe)
            logger.info(
                "Data Lambda returned bars after refresh",
                symbol=symbol_str,
                bars_count=len(bars),
            )
            return bars

        except DataLambdaError:
            raise
        except Exception as e:
            logger.error(
                "Failed to invoke Data Lambda",
                function_name=self.function_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise DataLambdaError(f"Failed to invoke Data Lambda: {e}") from e

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote (not implemented for Lambda client).

        Strategy only needs get_bars for indicator computation.

        Args:
            symbol: Trading symbol

        Returns:
            None (not implemented)

        """
        logger.debug(
            "get_latest_quote not implemented for DataLambdaClient",
            symbol=str(symbol),
        )
        return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price from latest bar.

        Args:
            symbol: Trading symbol

        Returns:
            Latest close price, or None if no bars available

        """
        bars = self.get_bars(symbol, period="5D", timeframe="1Day")
        if bars:
            return float(bars[-1].close)
        return None
