#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""
        ...


class DynamicTickSizeService:
    """Service for resolving symbol-specific tick sizes.

    Phase 7 Enhancement: Replaces hardcoded $0.01 with intelligent
    tick size resolution based on symbol characteristics and price levels.
    """

    def __init__(self) -> None:
        """Initialize the tick size service with default rules."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Default tick size rules by price range for US equities
        self._equity_tick_rules = [
            (Decimal("1.00"), Decimal("0.01")),  # $1+ = 1 cent
            (Decimal("0.01"), Decimal("0.0001")),  # $0.01-$1 = 0.1 cent
            (Decimal("0"), Decimal("0.000001")),  # <$0.01 = micro cent
        ]

        # Special symbol overrides
        self._symbol_overrides: dict[str, Decimal] = {
            # Crypto symbols typically have smaller tick sizes
            "BTCUSD": Decimal("0.01"),
            "ETHUSD": Decimal("0.01"),
            # High-priced stocks may use different ticks
            "BRK.A": Decimal("1.00"),  # Berkshire Hathaway Class A
        }

        # Default fallback tick size
        self._default_tick_size = Decimal("0.01")

    def get_tick_size(self, symbol: str, current_price: Decimal | None = None) -> Decimal:
        """Get the appropriate tick size for a symbol.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTCUSD")
            current_price: Current price to determine price-based tick rules

        Returns:
            Appropriate tick size as Decimal

        """
        # Normalize symbol
        symbol = symbol.upper().strip()

        # Check for explicit symbol overrides first
        if symbol in self._symbol_overrides:
            tick_size = self._symbol_overrides[symbol]
            self.logger.debug(f"Using override tick size {tick_size} for {symbol}")
            return tick_size

        # If we have current price, use price-based rules
        if current_price is not None and current_price > Decimal("0"):
            tick_size = self._get_price_based_tick_size(current_price)
            self.logger.debug(
                f"Using price-based tick size {tick_size} for {symbol} at ${current_price}"
            )
            return tick_size

        # Fall back to default
        self.logger.debug(f"Using default tick size {self._default_tick_size} for {symbol}")
        return self._default_tick_size

    def _get_price_based_tick_size(self, price: Decimal) -> Decimal:
        """Get tick size based on current price level.

        Args:
            price: Current price

        Returns:
            Appropriate tick size for the price level

        """
        for min_price, tick_size in self._equity_tick_rules:
            if price >= min_price:
                return tick_size

        # Should not reach here, but return default as safety
        return self._default_tick_size

    def add_symbol_override(self, symbol: str, tick_size: Decimal) -> None:
        """Add or update a symbol-specific tick size override.

        Args:
            symbol: Trading symbol
            tick_size: Tick size for this symbol

        """
        symbol = symbol.upper().strip()
        self._symbol_overrides[symbol] = tick_size
        self.logger.info(f"Added tick size override: {symbol} -> {tick_size}")

    def remove_symbol_override(self, symbol: str) -> None:
        """Remove a symbol-specific tick size override.

        Args:
            symbol: Trading symbol to remove override for

        """
        symbol = symbol.upper().strip()
        if symbol in self._symbol_overrides:
            del self._symbol_overrides[symbol]
            self.logger.info(f"Removed tick size override for {symbol}")

    def get_symbol_overrides(self) -> dict[str, Decimal]:
        """Get current symbol-specific overrides.

        Returns:
            Dictionary of symbol -> tick size overrides

        """
        return dict(self._symbol_overrides)


# NOTE: Global singleton access was removed to align with DDD and DI rules.
# Provide a lightweight factory helper for transitional call sites; new code
# should inject a DynamicTickSizeService instance explicitly.


def create_tick_size_service() -> DynamicTickSizeService:
    """Create a new tick size service instance.

    Prefer dependency injection: construct once in the application layer and
    pass the instance down (e.g., into strategies or execution planners).
    """
    return DynamicTickSizeService()


def resolve_tick_size(
    service: DynamicTickSizeService, symbol: str, current_price: Decimal | None = None
) -> Decimal:
    """Resolve tick size using an injected service instance.

    This replaces the previous implicit global accessor.
    """
    return service.get_tick_size(symbol, current_price)
