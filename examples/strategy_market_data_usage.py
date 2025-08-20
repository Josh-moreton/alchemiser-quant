"""Example usage of MarketDataPort in strategy implementation.

This demonstrates how strategies can be updated to use the MarketDataPort protocol
instead of direct dependencies on UnifiedDataProvider or other infrastructure.
"""

from typing import Any

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort


class ExampleStrategy:
    """Example strategy showing how to use MarketDataPort protocol.

    This demonstrates the pattern that strategies should follow when using
    the new MarketDataPort protocol for data access.
    """

    def __init__(self, market_data: MarketDataPort) -> None:
        """Initialize strategy with market data port dependency.

        Args:
            market_data: Implementation of MarketDataPort protocol
        """
        self.market_data = market_data
        self.symbols = ["AAPL", "MSFT", "GOOGL"]

    def get_market_data(self) -> dict[str, Any]:
        """Fetch data for all symbols using the MarketDataPort.

        Returns:
            Dictionary mapping symbols to their market data
        """
        market_data = {}
        for symbol in self.symbols:
            # Use the protocol method to get historical data
            data = self.market_data.get_data(symbol, timeframe="1day", period="1y")
            if not data.empty:
                market_data[symbol] = data
            else:
                print(f"Warning: Could not fetch data for {symbol}")

        return market_data

    def get_current_prices(self) -> dict[str, float]:
        """Get current prices for all symbols.

        Returns:
            Dictionary mapping symbols to their current prices
        """
        prices = {}
        for symbol in self.symbols:
            price = self.market_data.get_current_price(symbol)
            if price is not None:
                prices[symbol] = price

        return prices

    def get_bid_ask_spreads(self) -> dict[str, float]:
        """Calculate bid-ask spreads for all symbols.

        Returns:
            Dictionary mapping symbols to their bid-ask spreads
        """
        spreads = {}
        for symbol in self.symbols:
            bid, ask = self.market_data.get_latest_quote(symbol)
            if bid is not None and ask is not None:
                spreads[symbol] = ask - bid

        return spreads


# Example usage in actual strategy files:
"""
# Before (using data_provider directly):
class TECLStrategyEngine:
    def __init__(self, data_provider: Any = None) -> None:
        if data_provider is None:
            raise ValueError("data_provider is required")
        self.data_provider = data_provider

    def get_market_data(self):
        data = self.data_provider.get_data(symbol)
        # ... rest of method

# After (using MarketDataPort protocol):
class TECLStrategyEngine:
    def __init__(self, market_data: MarketDataPort) -> None:
        self.market_data = market_data

    def get_market_data(self):
        data = self.market_data.get_data(symbol)
        # ... rest of method
"""
