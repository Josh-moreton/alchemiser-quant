"""Business Unit: indicators | Status: current.

Lambda handler for the Indicators Lambda function.

This Lambda is invoked synchronously by the Strategy Lambda to compute
technical indicators. It receives IndicatorRequest payloads and returns
TechnicalIndicator responses.
"""

from __future__ import annotations

import json
from typing import Any

from the_alchemiser.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.indicators.indicator_service import IndicatorComputationError, IndicatorService
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest

logger = get_logger(__name__)

# Module constant for logging
MODULE_NAME = "indicators"


# Singleton service instance for Lambda warm starts
_indicator_service: IndicatorService | None = None


def _get_indicator_service() -> IndicatorService:
    """Get or create singleton IndicatorService instance.

    Uses singleton pattern to reuse connections across warm Lambda invocations.

    Returns:
        Configured IndicatorService instance

    """
    global _indicator_service

    if _indicator_service is not None:
        logger.debug("Reusing existing IndicatorService instance", module=MODULE_NAME)
        return _indicator_service

    logger.info("Creating new IndicatorService instance", module=MODULE_NAME)

    # Create market data adapter (uses env vars MARKET_DATA_BUCKET via MarketDataStore)
    market_data_adapter = CachedMarketDataAdapter()

    # Create and cache service
    _indicator_service = IndicatorService(market_data_service=market_data_adapter)

    logger.info(
        "IndicatorService initialized",
        module=MODULE_NAME,
    )

    return _indicator_service


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ANN401
    """Lambda handler for indicator computation requests.

    This handler is invoked synchronously by the Strategy Lambda using
    Lambda.invoke(). It receives an IndicatorRequest as the event payload
    and returns a TechnicalIndicator as the response.

    Args:
        event: IndicatorRequest payload (either as dict or JSON string in 'body')
        context: Lambda context with invocation metadata

    Returns:
        Dict with statusCode and body containing TechnicalIndicator JSON

    Example Event::

        {
            "symbol": "AAPL",
            "indicator_type": "rsi",
            "parameters": {"window": 14},
            "correlation_id": "abc-123"
        }

    Example Response::

        {
            "statusCode": 200,
            "body": {
                "symbol": "AAPL",
                "timestamp": "2024-01-15T10:30:00Z",
                "rsi_14": 65.5,
                "current_price": "185.50",
                "data_source": "real_market_data",
                "metadata": {"value": 65.5, "window": 14}
            }
        }

    """
    # Extract correlation_id from event for logging context
    correlation_id = event.get("correlation_id", "unknown")

    logger.info(
        "Indicators Lambda invoked",
        module=MODULE_NAME,
        correlation_id=correlation_id,
        request_id=context.aws_request_id,
        function_name=context.function_name,
        memory_limit_mb=context.memory_limit_in_mb,
        remaining_time_ms=context.get_remaining_time_in_millis(),
    )

    try:
        # Handle both direct invocation (dict) and API Gateway style (body as string)
        if "body" in event and isinstance(event["body"], str):
            payload = json.loads(event["body"])
        else:
            payload = event

        # Validate and parse request
        request = IndicatorRequest.model_validate(payload)

        logger.info(
            "Processing indicator request",
            module=MODULE_NAME,
            symbol=request.symbol,
            indicator_type=request.indicator_type,
            parameters=request.parameters,
            correlation_id=correlation_id,
        )

        # Get service and compute indicator
        service = _get_indicator_service()
        indicator = service.get_indicator(request)

        # Serialize response
        response_body = indicator.model_dump(mode="json")

        logger.info(
            "Indicator computed successfully",
            module=MODULE_NAME,
            symbol=request.symbol,
            indicator_type=request.indicator_type,
            correlation_id=correlation_id,
            remaining_time_ms=context.get_remaining_time_in_millis(),
        )

        return {
            "statusCode": 200,
            "body": response_body,
        }

    except IndicatorComputationError as e:
        logger.error(
            "Indicator computation error",
            module=MODULE_NAME,
            error=str(e),
            error_type="IndicatorComputationError",
            correlation_id=correlation_id,
        )
        return {
            "statusCode": 400,
            "body": {
                "error": "IndicatorComputationError",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        }

    except ValueError as e:
        logger.error(
            "Invalid request payload",
            module=MODULE_NAME,
            error=str(e),
            error_type="ValidationError",
            correlation_id=correlation_id,
        )
        return {
            "statusCode": 400,
            "body": {
                "error": "ValidationError",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        }

    except Exception as e:
        logger.exception(
            "Unexpected error in Indicators Lambda",
            module=MODULE_NAME,
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id,
        )
        return {
            "statusCode": 500,
            "body": {
                "error": "InternalError",
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id,
            },
        }
