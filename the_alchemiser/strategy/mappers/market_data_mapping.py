"""Business Unit: strategy | Status: current..

    Args:
        quote: QuoteModel domain object or None

    Returns:
        Tuple of (bid_price, ask_price), either can be None if quote unavailable

    """
    if quote is None:
        return (None, None)

    return (float(quote.bid), float(quote.ask))


def symbol_str_to_symbol(symbol: str) -> Symbol:
    """Convert string symbol to Symbol value object.

    Args:
        symbol: String symbol (e.g., "AAPL")

    Returns:
        Symbol value object

    """
    return Symbol(symbol)


def quote_to_current_price(quote: QuoteModel | None) -> float | None:
    """Extract current price from quote as mid-price.

    Args:
        quote: QuoteModel domain object or None

    Returns:
        Mid-price as float, or None if quote unavailable

    """
    if quote is None:
        return None

    return float(quote.mid)


def dataframe_to_bars(df: pd.DataFrame, symbol: Symbol) -> list[BarModel]:
    """Convert pandas DataFrame to list of BarModel objects.

    Args:
        df: DataFrame with OHLCV data indexed by timestamp
        symbol: Symbol value object (unused but kept for interface compatibility)

    Returns:
        List of BarModel domain objects

    """
    if df.empty:
        return []

    bars = []
    for timestamp, row in df.iterrows():
        bar = BarModel(
            ts=pd.to_datetime(timestamp),
            open=Decimal(str(row["Open"])),
            high=Decimal(str(row["High"])),
            low=Decimal(str(row["Low"])),
            close=Decimal(str(row["Close"])),
            volume=Decimal(str(row["Volume"])),
        )
        bars.append(bar)

    return bars
