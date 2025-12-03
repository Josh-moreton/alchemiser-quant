"""Business Unit: shared | Status: current.

AWS SigV4 signing transport for httpx.

Provides an httpx transport that signs requests using AWS Signature Version 4,
enabling authentication with AWS Lambda Function URLs using AWS_IAM auth type.
"""

from __future__ import annotations

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import get_session


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
        self._credentials = self._session.get_credentials()
        self._region = region or self._session.get_config_variable("region") or "us-east-1"
        self._transport = httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """Handle an HTTP request by signing it with SigV4 before sending.

        Args:
            request: The httpx Request to sign and send

        Returns:
            The httpx Response from the signed request

        """
        # Extract request details
        url = str(request.url)
        method = request.method
        headers = dict(request.headers)
        body = request.content.decode() if request.content else None

        # Create AWS request for signing
        aws_request = AWSRequest(
            method=method,
            url=url,
            headers=headers,
            data=body,
        )

        # Sign the request
        SigV4Auth(self._credentials, "lambda", self._region).add_auth(aws_request)

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
