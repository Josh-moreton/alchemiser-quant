"""Business Unit: execution | Status: legacy

Executor for backward compatibility.
"""

from typing import Any, Optional


class CanonicalOrderExecutor:
    """Minimal executor implementation for backward compatibility.
    
    This class provides the interface expected by existing code
    but delegates actual execution to execution_v2 components.
    """
    
    def execute_order(self, order_request: Any) -> Optional[str]:
        """Execute an order request.
        
        Returns:
            Order ID if successful, None if failed
        """
        # This is a placeholder implementation
        # In practice, this should delegate to execution_v2
        return None
    
    def execute_market_order(self, symbol: str, side: str, quantity: float) -> Optional[str]:
        """Execute a market order.
        
        Returns:
            Order ID if successful, None if failed
        """
        # This is a placeholder implementation
        # In practice, this should delegate to execution_v2
        return None