"""Business Unit: execution | Status: legacy

Account service for backward compatibility.
"""

from typing import Any


class AccountService:
    """Minimal account service for backward compatibility."""
    
    def get_account(self) -> dict[str, Any]:
        """Get account information."""
        return {}
    
    def get_positions(self) -> dict[str, Any]:
        """Get account positions."""
        return {}