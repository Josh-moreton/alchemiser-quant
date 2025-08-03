import logging
from typing import Dict, List


class AccountService:
    """Service class for account and position management."""

    def __init__(self, data_provider):
        self.data_provider = data_provider

    def get_account_info(self) -> Dict:
        """Return comprehensive account info using helper utilities."""
        from the_alchemiser.utils.account_utils import extract_comprehensive_account_data
        return extract_comprehensive_account_data(self.data_provider)

    def get_positions(self) -> Dict:
        """Return current positions keyed by symbol."""
        positions = self.data_provider.get_positions()
        position_dict = {}
        if not positions:
            return position_dict
        for position in positions:
            symbol = position.get('symbol') if isinstance(position, dict) else getattr(position, 'symbol', None)
            if symbol:
                position_dict[symbol] = position
        return position_dict

    def get_current_price(self, symbol: str) -> float:
        """Return current price for a symbol."""
        price = self.data_provider.get_current_price(symbol)
        return float(price) if price is not None else 0.0

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Return current prices for multiple symbols."""
        prices = {}
        for symbol in symbols:
            try:
                price = self.get_current_price(symbol)
                if price and price > 0:
                    prices[symbol] = float(price)
            except Exception as e:
                logging.warning(f"Failed to get current price for {symbol}: {e}")
        return prices
