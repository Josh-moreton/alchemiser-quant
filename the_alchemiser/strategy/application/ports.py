"""Business Unit: strategy & signal generation | Status: current

Port protocols for Strategy context external dependencies.
"""

from typing import Protocol, Sequence
from decimal import Decimal
from datetime import datetime
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.application.contracts.signal_contract_v1 import SignalContractV1
from the_alchemiser.strategy.domain.value_objects.market_bar_vo import MarketBarVO
from the_alchemiser.strategy.domain.exceptions import SymbolNotFoundError, PublishError
from the_alchemiser.shared_kernel.exceptions.base_exceptions import DataAccessError, ValidationError


class MarketDataPort(Protocol):
    """Port for retrieving market data required by strategy algorithms.
    
    Responsibilities:
    - Provide price history for technical analysis
    - Deliver real-time/latest market data
    - Handle symbol resolution and validation
    
    NOT responsible for:
    - Data caching (implementation detail)
    - Data transformation (belongs in anti_corruption)
    - Strategy signal generation (belongs in domain)
    
    Error expectations:
    - Raises DataAccessError for connectivity issues
    - Raises SymbolNotFoundError for invalid symbols
    
    Idempotency: get_* methods are idempotent for same parameters
    """
    
    def get_latest_bar(self, symbol: Symbol, timeframe: str) -> MarketBarVO:
        """Get most recent price bar for symbol.
        
        Args:
            symbol: Symbol to fetch data for
            timeframe: Period (e.g., "1Day", "1Hour", "15Min")
            
        Returns:
            MarketBarVO with OHLCV data
            
        Raises:
            DataAccessError: Network/API failure
            SymbolNotFoundError: Invalid symbol
        """
        ...
    
    def get_history(
        self, 
        symbol: Symbol, 
        timeframe: str, 
        limit: int,
        end_time: datetime | None = None
    ) -> Sequence[MarketBarVO]:
        """Get historical price bars for technical analysis.
        
        Args:
            symbol: Symbol to fetch data for
            timeframe: Period (e.g., "1Day", "1Hour")
            limit: Maximum number of bars (1-1000)
            end_time: End of range (None = latest available)
            
        Returns:
            Sequence of MarketBarVO ordered by timestamp (oldest first)
            
        Raises:
            DataAccessError: Network/API failure
            SymbolNotFoundError: Invalid symbol
            ValueError: Invalid limit or timeframe
        """
        ...


class SignalPublisherPort(Protocol):
    """Port for publishing strategy signals to Portfolio context.
    
    Responsibilities:
    - Deliver SignalContractV1 messages to Portfolio
    - Handle message deduplication (via message_id)
    - Ensure reliable delivery semantics
    
    NOT responsible for:
    - Signal generation (belongs in domain)
    - Portfolio state updates (Portfolio responsibility)
    - Message transformation (belongs in anti_corruption)
    
    Error expectations:
    - Raises PublishError for delivery failures
    
    Idempotency: Publishing same message_id twice has no additional effect
    """
    
    def publish(self, signal: SignalContractV1) -> None:
        """Publish a strategy signal for Portfolio consumption.
        
        Args:
            signal: Complete signal contract with envelope metadata
            
        Raises:
            PublishError: Message delivery failure
            ValidationError: Invalid signal contract
        """
        ...


# Export list for explicit re-exports
__all__ = [
    "MarketDataPort",
    "SignalPublisherPort",
]