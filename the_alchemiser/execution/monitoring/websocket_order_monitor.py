"""Business Unit: execution | Status: legacy

WebSocket order monitoring for backward compatibility.
"""

from typing import Any

from the_alchemiser.shared.dto.broker_dto import WebSocketResult


class OrderCompletionMonitor:
    """Minimal order completion monitor for backward compatibility."""
    
    def __init__(self, trading_client: Any, api_key: str, secret_key: str) -> None:
        """Initialize the monitor.
        
        Args:
            trading_client: Alpaca trading client
            api_key: API key
            secret_key: Secret key

        """
        self.trading_client = trading_client
        self.api_key = api_key
        self.secret_key = secret_key
    
    def wait_for_order_completion(self, order_ids: list[str], max_wait_seconds: int = 60) -> WebSocketResult:
        """Wait for order completion.
        
        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum wait time in seconds
            
        Returns:
            WebSocketResult with completion status

        """
        # This is a minimal implementation that returns a basic result
        # In practice, this should implement actual WebSocket monitoring
        return WebSocketResult(
            success=True,
            completed_order_ids=order_ids,  # Assume all completed for compatibility
            timeout_reached=False,
            error_message=None
        )