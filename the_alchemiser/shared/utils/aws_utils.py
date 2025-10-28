"""Business Unit: shared | Status: current.

AWS utility functions for interacting with AWS services.
"""

from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ..logging import get_logger

logger = get_logger(__name__)

__all__ = ["get_aws_account_id"]


def get_aws_account_id() -> str:
    """Get AWS account ID from STS.

    Returns:
        AWS account ID

    Raises:
        ClientError: If unable to retrieve account ID from STS
        BotoCoreError: If boto3 operation fails
        KeyError: If Account field missing from STS response

    """
    try:
        sts_client = boto3.client("sts")
        identity = sts_client.get_caller_identity()
        return str(identity["Account"])
    except (ClientError, BotoCoreError, KeyError) as e:
        logger.error("Failed to retrieve AWS account ID", error=str(e))
        raise
