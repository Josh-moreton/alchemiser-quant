"""Business Unit: strategy_v2 | Status: current.

Data validation service for strategy execution.

Validates that market data is fresh before strategy evaluation. If stale data
is detected, triggers synchronous refresh via Data Lambda and waits for completion.
Halts strategy execution if refresh fails or times out.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

import boto3

from the_alchemiser.data_v2.data_freshness_validator import DataFreshnessValidator
from the_alchemiser.data_v2.market_data_store import MarketDataStore
from the_alchemiser.data_v2.symbol_extractor import extract_symbols_from_file
from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Timeout and retry configuration
MAX_REFRESH_WAIT_SECONDS = 60
POLL_INTERVAL_SECONDS = 2


class DataValidationService:
    """Service for validating data freshness before strategy execution.

    This service ensures that strategies only execute with up-to-date market data.
    It validates data freshness, triggers synchronous refresh if needed, and waits
    for completion before allowing strategy execution to proceed.

    Attributes:
        validator: DataFreshnessValidator instance for checking data freshness
        market_data_store: MarketDataStore for accessing market data
        lambda_client: Boto3 Lambda client for invoking Data Lambda
        data_lambda_name: Name of the Data Lambda function

    """

    def __init__(
        self,
        validator: DataFreshnessValidator | None = None,
        market_data_store: MarketDataStore | None = None,
        data_lambda_name: str | None = None,
    ) -> None:
        """Initialize data validation service.

        Args:
            validator: DataFreshnessValidator instance. If None, creates default.
            market_data_store: MarketDataStore instance. If None, creates default.
            data_lambda_name: Name of Data Lambda function. If None, uses env var.

        """
        self.market_data_store = market_data_store or MarketDataStore()
        self.validator = validator or DataFreshnessValidator(
            market_data_store=self.market_data_store, max_staleness_days=2
        )
        self.lambda_client = boto3.client("lambda")
        self.data_lambda_name = data_lambda_name or "alchemiser-data-lambda"

        logger.info(
            "DataValidationService initialized",
            extra={"data_lambda": self.data_lambda_name},
        )

    def validate_and_refresh_if_needed(
        self, dsl_file: str, correlation_id: str
    ) -> None:
        """Validate data freshness for symbols in DSL file, refresh if stale.

        Extracts symbols from the DSL file, validates their data freshness,
        and triggers synchronous refresh via Data Lambda if any data is stale.
        Waits for refresh completion before returning.

        Args:
            dsl_file: DSL strategy file name (e.g., '1-KMLM.clj')
            correlation_id: Correlation ID for tracing

        Raises:
            DataProviderError: If data is stale and refresh fails or times out
            FileNotFoundError: If DSL file doesn't exist

        """
        # Extract symbols from DSL file
        symbols = self._extract_symbols_from_dsl(dsl_file)

        if not symbols:
            logger.warning(
                "No symbols found in DSL file",
                extra={
                    "dsl_file": dsl_file,
                    "correlation_id": correlation_id,
                },
            )
            return

        logger.info(
            "Validating data freshness for strategy symbols",
            extra={
                "dsl_file": dsl_file,
                "symbol_count": len(symbols),
                "symbols": list(symbols),
                "correlation_id": correlation_id,
            },
        )

        # Validate data freshness
        is_fresh, stale_symbols = self.validator.validate_data_freshness(
            symbols=list(symbols), raise_on_stale=False
        )

        if is_fresh:
            logger.info(
                "✅ Data validation passed: all symbols current",
                extra={
                    "dsl_file": dsl_file,
                    "symbol_count": len(symbols),
                    "correlation_id": correlation_id,
                },
            )
            return

        # Data is stale - trigger refresh
        logger.warning(
            "⚠️ Stale data detected, triggering synchronous refresh",
            extra={
                "dsl_file": dsl_file,
                "stale_symbols": list(stale_symbols.keys()),
                "correlation_id": correlation_id,
            },
        )

        # Refresh stale symbols
        self._refresh_symbols_sync(list(stale_symbols.keys()), correlation_id)

        # Re-validate after refresh
        is_fresh_after_refresh, still_stale = self.validator.validate_data_freshness(
            symbols=list(symbols), raise_on_stale=False
        )

        if not is_fresh_after_refresh:
            error_msg = (
                f"Data validation failed after refresh. "
                f"Stale symbols: {list(still_stale.keys())}. "
                f"Cannot proceed with strategy execution for {dsl_file}."
            )
            logger.error(
                error_msg,
                extra={
                    "dsl_file": dsl_file,
                    "still_stale_symbols": list(still_stale.keys()),
                    "correlation_id": correlation_id,
                },
            )
            raise DataProviderError(error_msg)

        logger.info(
            "✅ Data validation passed after refresh",
            extra={
                "dsl_file": dsl_file,
                "refreshed_symbols": list(stale_symbols.keys()),
                "correlation_id": correlation_id,
            },
        )

    def _extract_symbols_from_dsl(self, dsl_file: str) -> set[str]:
        """Extract symbols from a DSL strategy file.

        Args:
            dsl_file: DSL file name (e.g., '1-KMLM.clj')

        Returns:
            Set of ticker symbols found in the file

        Raises:
            FileNotFoundError: If DSL file doesn't exist

        """
        # Resolve strategies directory relative to this module
        strategies_path = Path(__file__).parent.parent / "strategies"
        file_path = strategies_path / dsl_file

        if not file_path.exists():
            raise FileNotFoundError(f"DSL file not found: {file_path}")

        return extract_symbols_from_file(file_path)

    def _refresh_symbols_sync(
        self, symbols: list[str], correlation_id: str
    ) -> None:
        """Refresh symbols synchronously via Data Lambda.

        Invokes Data Lambda for each symbol and waits for completion.
        Uses synchronous Lambda invocation (RequestResponse) to wait for result.

        Args:
            symbols: List of symbols to refresh
            correlation_id: Correlation ID for tracing

        Raises:
            DataProviderError: If refresh fails or times out

        """
        for symbol in symbols:
            logger.info(
                "Invoking Data Lambda to refresh symbol",
                extra={
                    "symbol": symbol,
                    "correlation_id": correlation_id,
                },
            )

            start_time = time.time()

            try:
                # Invoke Data Lambda synchronously (RequestResponse)
                payload = {
                    "symbols": [symbol],
                    "full_seed": False,
                    "correlation_id": correlation_id,
                }

                response = self.lambda_client.invoke(
                    FunctionName=self.data_lambda_name,
                    InvocationType="RequestResponse",  # Synchronous
                    Payload=json.dumps(payload),
                )

                # Parse response
                response_payload = json.loads(response["Payload"].read())
                status_code = response_payload.get("statusCode", 500)

                elapsed_time = time.time() - start_time

                if status_code == 200:
                    logger.info(
                        "✅ Symbol refresh completed successfully",
                        extra={
                            "symbol": symbol,
                            "elapsed_seconds": round(elapsed_time, 2),
                            "correlation_id": correlation_id,
                        },
                    )
                else:
                    error_msg = (
                        f"Data Lambda returned error for {symbol}: "
                        f"status={status_code}, "
                        f"response={response_payload}"
                    )
                    logger.error(
                        error_msg,
                        extra={
                            "symbol": symbol,
                            "status_code": status_code,
                            "correlation_id": correlation_id,
                        },
                    )
                    raise DataProviderError(error_msg)

            except Exception as e:
                elapsed_time = time.time() - start_time
                error_msg = (
                    f"Failed to refresh symbol {symbol} after "
                    f"{round(elapsed_time, 2)}s: {str(e)}"
                )
                logger.error(
                    error_msg,
                    extra={
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": correlation_id,
                    },
                    exc_info=True,
                )
                raise DataProviderError(error_msg) from e

            # Check if we've exceeded max wait time
            if elapsed_time > MAX_REFRESH_WAIT_SECONDS:
                error_msg = (
                    f"Data refresh for {symbol} exceeded max wait time "
                    f"({MAX_REFRESH_WAIT_SECONDS}s)"
                )
                logger.error(
                    error_msg,
                    extra={
                        "symbol": symbol,
                        "elapsed_seconds": round(elapsed_time, 2),
                        "max_wait_seconds": MAX_REFRESH_WAIT_SECONDS,
                        "correlation_id": correlation_id,
                    },
                )
                raise DataProviderError(error_msg)
