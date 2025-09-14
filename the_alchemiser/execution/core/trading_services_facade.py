"""Business Unit: execution | Status: legacy

Trading services facade for backward compatibility.
"""

from typing import Any


class TradingServicesFacade:
    """Minimal trading services facade for backward compatibility."""
    
    def execute_trade(self, trade_request: Any) -> Any:
        """Execute a trade."""
        return None
    
    def get_trading_status(self) -> dict[str, Any]:
        """Get trading status."""
        return {"status": "unknown"}