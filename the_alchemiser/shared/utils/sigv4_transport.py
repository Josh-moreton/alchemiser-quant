"""Business Unit: shared | Status: current.

AWS SigV4 signing transport for httpx.

Provides an httpx transport that signs requests using AWS Signature Version 4,
enabling authentication with AWS Lambda Function URLs using AWS_IAM auth type.
"""

from __future__ import annotations

import os

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def create_sigv4_signed_client(
    *,
    timeout: float = 180.0,
    region: str | None = None,
) -> httpx.Client:
    """Create an httpx Client that signs requests with AWS SigV4.

    This client automatically signs all requests using the Lambda execution role's
    credentials, which are available via environment variables in Lambda.

    Args:
        timeout: Request timeout in seconds (default: 180s for Lambda cold starts)
        region: AWS region for signing. If None, uses AWS_REGION env var.

    Returns:
        httpx.Client configured with SigV4 signing transport

    Example:
        client = create_sigv4_signed_client()
        response = client.post(
            "https://xxx.lambda-url.us-east-1.on.aws/generate",
            json={"trigger_event": {...}}
        )

    """
    transport = SigV4Transport(region=region)
    return httpx.Client(transport=transport, timeout=timeout)


class SigV4Transport(httpx.BaseTransport):
    """HTTP transport that signs requests with AWS Signature Version 4.

    Uses botocore to sign requests for AWS Lambda Function URLs with IAM auth.
    Credentials are automatically retrieved from the Lambda execution environment.
    """

    def __init__(self, region: str | None = None) -> None:
        """Initialize the SigV4 transport.

        Args:
            region: AWS region for signing. If None, auto-detected from environment.

        """
        self._session = get_session()
        # Get region from environment or default
        self._region = region or os.environ.get("AWS_REGION", "us-east-1")
        self._transport = httpx.HTTPTransport()
        logger.info(
            "SigV4Transport initialized",
            extra={"region": self._region},
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Handle an HTTP request by signing it with SigV4 before sending.

        Args:
            request: The httpx Request to sign and send

        Returns:
            The httpx Response from the signed request

        """
        # Get fresh credentials each time (important for Lambda role credentials)
        credentials = self._session.get_credentials()
        if credentials is None:
            logger.error("No AWS credentials available for SigV4 signing")
            raise RuntimeError("No AWS credentials available for SigV4 signing")

        # Get frozen credentials to ensure we have access_key, secret_key, and token
        frozen_credentials = credentials.get_frozen_credentials()

        # Extract request details
        url = str(request.url)
        method = request.method
        headers = dict(request.headers)
        body = request.content.decode() if request.content else None

        logger.debug(
            "Signing request with SigV4",
            extra={
                "url": url,
                "method": method,
                "region": self._region,
                "has_session_token": bool(frozen_credentials.token),
            },
        )

        # Create AWS request for signing
        aws_request = AWSRequest(
            method=method,
            url=url,
            headers=headers,
            data=body,
        )

        # Sign the request using frozen credentials
        SigV4Auth(frozen_credentials, "lambda", self._region).add_auth(aws_request)

        # Create new httpx request with signed headers
        signed_headers = dict(aws_request.headers)
        signed_request = httpx.Request(
            method=method,
            url=url,
            headers=signed_headers,
            content=request.content,
        )

        # Send the signed request
        return self._transport.handle_request(signed_request)

    def close(self) -> None:
        """Close the underlying transport."""
        self._transport.close()
