"""Business Unit: strategy_v2 | Status: current.

Data validation service for strategy execution.

Validates that market data is fresh before strategy evaluation. If stale data
is detected, triggers synchronous refresh via Data Lambda and waits for completion.
Halts strategy execution if refresh fails or times out.
"""

from __future__ import annotations

import json
import os
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

# Timeout and retry configuration (12-factor configuration via environment variables)
MAX_REFRESH_WAIT_SECONDS = int(os.environ.get("DATA_VALIDATION_MAX_WAIT_SECONDS", "60"))
POLL_INTERVAL_SECONDS = int(os.environ.get("DATA_VALIDATION_POLL_INTERVAL_SECONDS", "2"))


class DataValidationService:
    """Service for validating data freshness before strategy execution.

    This service ensures that strategies only execute with up-to-date market data.
    It validates data freshness, triggers synchronous refresh if needed, and waits
    for completion before allowing strategy execution to proceed.

    ARCHITECTURAL NOTE - Synchronous Lambda Invocation:
    This service currently uses synchronous (RequestResponse) Lambda invocation to wait
    for data refresh completion before proceeding. This creates tight coupling with the
    Data Lambda and introduces operational risks:

    - Strategy Lambda timeout is coupled to Data Lambda performance
    - Data Lambda cold starts directly impact strategy execution latency
    - Cascading failures if Data Lambda is throttled
    - No built-in retry mechanism for transient failures

    A future enhancement should migrate to an event-driven pattern:
    1. Publish DataRefreshRequested event to EventBridge
    2. Use Step Functions or polling with exponential backoff
    3. Maintain event-driven architecture consistency
    4. Improve resilience through decoupling

    PERFORMANCE NOTE - Sequential Symbol Refresh:
    Currently refreshes stale symbols sequentially (one at a time). With multiple stale
    symbols, this can consume significant timeout budget. For example, 3 stale symbols at
    60s each = 180s (20% of 900s Lambda timeout). Consider future optimization:
    1. Batch all stale symbols in a single Data Lambda call
    2. Use concurrent invocations with asyncio
    3. Document maximum expected stale symbols and verify timeout budget

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
        self.data_lambda_name = data_lambda_name or os.environ.get(
            "DATA_LAMBDA_FUNCTION_NAME", "alchemiser-shared-data"
        )

        logger.info(
            "DataValidationService initialized",
            extra={"data_lambda": self.data_lambda_name},
        )

    def validate_and_refresh_if_needed(self, dsl_file: str, correlation_id: str) -> None:
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
            # NOTE: Currently logs success locally only. For operational visibility into
            # data freshness patterns, consider emitting DataValidationCompleted event or
            # structured metrics (symbols_validated, refresh_rate) to EventBridge.
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

        # Re-validate after refresh only for symbols that were previously stale
        is_fresh_after_refresh, still_stale = self.validator.validate_data_freshness(
            symbols=list(stale_symbols.keys()), raise_on_stale=False
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

    def _refresh_symbols_sync(self, symbols: list[str], correlation_id: str) -> None:
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

                # Check if we've exceeded max wait time before processing result
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
                    f"Failed to refresh symbol {symbol} after {round(elapsed_time, 2)}s: {e!s}"
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
