"""Business Unit: strategy | Status: current.."""
        symbol_obj = Symbol(symbol)
        return self._canonical_port.get_mid_price(symbol_obj)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest quote returning (bid, ask) or None.

        Matches DataProvider protocol: either both floats (bid, ask) or None if
        quote unavailable or incomplete.
        """
        symbol_obj = Symbol(symbol)
        quote = self._canonical_port.get_latest_quote(symbol_obj)
        if quote is None:
            return None
        # QuoteModel fields appear non-optional by type; retain defensive try/except
        try:
            return (float(quote.bid), float(quote.ask))
        except (AttributeError, TypeError, ValueError):  # Defensive fallback
            return None
