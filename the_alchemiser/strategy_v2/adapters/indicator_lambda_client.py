"""Business Unit: strategy_v2 | Status: current.

Lambda client for invoking the Indicators Lambda.

This adapter invokes the Indicators Lambda synchronously to compute
technical indicators. It implements the IndicatorPort interface to
maintain the same contract as the old in-process IndicatorService.
"""

from __future__ import annotations

import json
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.errors.exceptions import IndicatorError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.types.indicator_port import IndicatorPort

logger = get_logger(__name__)

# Module constant for logging context
MODULE_NAME = "strategy_v2"


class IndicatorLambdaClient(IndicatorPort):
    """Client for invoking the Indicators Lambda synchronously.

    This adapter wraps Lambda.invoke() calls to the Indicators Lambda,
    handling request serialization, response deserialization, and error
    translation.

    Attributes:
        function_name: ARN or name of the Indicators Lambda function
        client: Boto3 Lambda client

    """

    def __init__(
        self,
        function_name: str | None = None,
        region_name: str | None = None,
    ) -> None:
        """Initialize Lambda client.

        Args:
            function_name: ARN or name of the Indicators Lambda.
                Defaults to INDICATORS_FUNCTION_NAME env var.
            region_name: AWS region. Defaults to AWS_REGION or us-east-1.

        """
        self.function_name = function_name or os.environ.get(
            "INDICATORS_FUNCTION_NAME",
            "alchemiser-indicators-dev",
        )
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self._client: Any = None

        logger.info(
            "IndicatorLambdaClient initialized",
            module=MODULE_NAME,
            function_name=self.function_name,
            region_name=self.region_name,
        )

    @property
    def client(self) -> Any:  # noqa: ANN401
        """Lazy-load boto3 Lambda client."""
        if self._client is None:
            self._client = boto3.client("lambda", region_name=self.region_name)
        return self._client

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Get technical indicator by invoking Indicators Lambda.

        Args:
            request: IndicatorRequest with symbol, type, and parameters

        Returns:
            TechnicalIndicator with computed values

        Raises:
            IndicatorError: If Lambda invocation fails or returns an error

        """
        correlation_id = request.correlation_id or "unknown"

        logger.info(
            "Invoking Indicators Lambda",
            module=MODULE_NAME,
            function_name=self.function_name,
            symbol=request.symbol,
            indicator_type=request.indicator_type,
            correlation_id=correlation_id,
        )

        try:
            # Serialize request to JSON payload
            payload = request.model_dump(mode="json")

            # Invoke Lambda synchronously (RequestResponse)
            response = self.client.invoke(
                FunctionName=self.function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(payload),
            )

            # Check for function error
            if "FunctionError" in response:
                error_payload = json.loads(response["Payload"].read().decode("utf-8"))
                logger.error(
                    "Indicators Lambda returned error",
                    module=MODULE_NAME,
                    function_error=response["FunctionError"],
                    error_payload=error_payload,
                    correlation_id=correlation_id,
                )
                raise IndicatorError(
                    f"Indicators Lambda error: {error_payload}",
                    symbol=request.symbol,
                )

            # Parse response payload
            response_payload = json.loads(response["Payload"].read().decode("utf-8"))

            # Check HTTP status code in response
            status_code = response_payload.get("statusCode", 200)
            if status_code != 200:
                error_body = response_payload.get("body", {})
                error_message = error_body.get("message", "Unknown error")
                logger.error(
                    "Indicators Lambda returned non-200 status",
                    module=MODULE_NAME,
                    status_code=status_code,
                    error_body=error_body,
                    correlation_id=correlation_id,
                )
                raise IndicatorError(
                    f"Indicators Lambda error (HTTP {status_code}): {error_message}",
                    symbol=request.symbol,
                )

            # Parse TechnicalIndicator from response body
            body = response_payload.get("body", {})
            indicator = TechnicalIndicator.model_validate(body)

            logger.info(
                "Indicators Lambda returned successfully",
                module=MODULE_NAME,
                symbol=request.symbol,
                indicator_type=request.indicator_type,
                correlation_id=correlation_id,
            )

            return indicator

        except IndicatorError:
            raise
        except ClientError as e:
            logger.error(
                "AWS Lambda invocation failed",
                module=MODULE_NAME,
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code", "Unknown"),
                correlation_id=correlation_id,
            )
            raise IndicatorError(
                f"Failed to invoke Indicators Lambda: {e}",
                symbol=request.symbol,
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error invoking Indicators Lambda",
                module=MODULE_NAME,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            raise IndicatorError(
                f"Error invoking Indicators Lambda: {e}",
                symbol=request.symbol,
            ) from e
