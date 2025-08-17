"""
Typed data provider adapter for typed services migration.

This adapter provides a type-safe interface for market data operations,
supporting the gradual migration to typed domain models.
"""

from typing import Any, Protocol

from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade import (
    UnifiedDataProviderFacade,
)


class TypedDataProviderProtocol(Protocol):
    """Protocol for typed data provider interface."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        ...

    def get_data(self, symbol: str, **kwargs: Any) -> Any:
        """Get historical data for a symbol."""
        ...


class TypedDataProviderAdapter:
    """
    Adapter for typed data provider operations.

    This adapter wraps the UnifiedDataProviderFacade to provide a typed interface
    for market data operations while maintaining backward compatibility.
    """

    def __init__(
        self,
        paper_trading: bool = True,
        cache_duration: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the typed data provider adapter."""
        self._facade = UnifiedDataProviderFacade(
            paper_trading=paper_trading,
            cache_duration=cache_duration,
            **kwargs,
        )

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol."""
        return self._facade.get_current_price(symbol)

    def get_data(self, symbol: str, **kwargs: Any) -> Any:
        """Get historical data for a symbol."""
        return self._facade.get_data(symbol, **kwargs)

    @property
    def trading_client(self) -> Any:
        """Provide access to trading client for backward compatibility."""
        return self._facade.trading_client
