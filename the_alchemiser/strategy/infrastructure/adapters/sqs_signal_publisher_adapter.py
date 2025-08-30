"""Business Unit: strategy & signal generation | Status: current

SQS signal publisher adapter implementing SignalPublisherPort.
"""

import logging
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.anti_corruption.serialization.signal_serializer import SignalSerializer
from the_alchemiser.shared_kernel.exceptions.base_exceptions import ValidationError
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1
from the_alchemiser.strategy.application.ports import SignalPublisherPort
from the_alchemiser.strategy.domain.exceptions import PublishError

logger = logging.getLogger(__name__)

class SqsSignalPublisherAdapter(SignalPublisherPort):
    """SQS adapter for publishing strategy signals with deduplication."""
    
    def __init__(self, queue_url: str, region_name: str = "us-east-1") -> None:
        """Initialize SQS client and serializer.
        
        Args:
            queue_url: Full SQS queue URL
            region_name: AWS region
        """
        self._queue_url = queue_url
        self._sqs = boto3.client("sqs", region_name=region_name)
        self._serializer = SignalSerializer()
        self._logger = logger.bind(
            component="SqsSignalPublisherAdapter",
            queue_url=queue_url
        )
    
    def publish(self, signal: SignalContractV1) -> None:
        """Publish signal to SQS with FIFO deduplication.
        
        Args:
            signal: Complete signal contract with metadata
            
        Raises:
            PublishError: SQS delivery failure
            ValidationError: Invalid signal contract
        """
        try:
            # Validate signal contract first
            self._validate_signal(signal)
            
            # Serialize to JSON via anti-corruption layer
            message_body = self._serializer.signal_contract_to_json(signal)
            
            # Prepare SQS message attributes
            message_attributes = self._build_message_attributes(signal)
            
            # Use correlation_id for message grouping (FIFO)
            # Use message_id for deduplication
            send_params: Dict[str, Any] = {
                "QueueUrl": self._queue_url,
                "MessageBody": message_body,
                "MessageAttributes": message_attributes,
                "MessageDeduplicationId": str(signal.message_id),
                "MessageGroupId": str(signal.correlation_id)
            }
            
            self._logger.info(
                "Publishing signal to SQS",
                correlation_id=str(signal.correlation_id),
                message_id=str(signal.message_id),
                symbol=signal.symbol.value,
                action=signal.action.value
            )
            
            response = self._sqs.send_message(**send_params)
            
            self._logger.debug(
                "Successfully published signal",
                message_id=response["MessageId"],
                correlation_id=str(signal.correlation_id),
                symbol=signal.symbol.value
            )
            
        except ValidationError:
            raise  # Re-raise validation errors as-is
        except (ClientError, BotoCoreError) as e:
            self._logger.error(
                "SQS publish failed",
                correlation_id=str(signal.correlation_id),
                error=str(e),
                error_code=getattr(e, "response", {}).get("Error", {}).get("Code")
            )
            raise PublishError(
                f"Failed to publish signal to SQS: {e}"
            ) from e
        except Exception as e:
            self._logger.error(
                "Unexpected error publishing signal",
                correlation_id=str(signal.correlation_id),
                error=str(e)
            )
            raise PublishError(
                f"Unexpected error publishing signal: {e}"
            ) from e
    
    def _validate_signal(self, signal: SignalContractV1) -> None:
        """Validate signal contract before publishing.
        
        Args:
            signal: Signal to validate
            
        Raises:
            ValidationError: Invalid signal
        """
        if not signal.correlation_id:
            raise ValidationError("Signal missing correlation_id")
        
        if not signal.message_id:
            raise ValidationError("Signal missing message_id")
        
        if not signal.symbol or not signal.symbol.value:
            raise ValidationError("Signal missing valid symbol")
        
        if signal.confidence < 0 or signal.confidence > 1:
            raise ValidationError(
                f"Signal confidence must be 0-1, got: {signal.confidence}"
            )
    
    def _build_message_attributes(self, signal: SignalContractV1) -> Dict[str, Dict[str, str]]:
        """Build SQS message attributes for filtering/routing.
        
        Args:
            signal: Signal contract
            
        Returns:
            SQS message attributes dict
        """
        return {
            "MessageType": {
                "StringValue": "SignalV1",
                "DataType": "String"
            },
            "Symbol": {
                "StringValue": signal.symbol.value,
                "DataType": "String"
            },
            "Action": {
                "StringValue": signal.action.value,
                "DataType": "String"
            },
            "CorrelationId": {
                "StringValue": str(signal.correlation_id),
                "DataType": "String"
            },
            "SourceContext": {
                "StringValue": "Strategy",
                "DataType": "String"
            }
        }