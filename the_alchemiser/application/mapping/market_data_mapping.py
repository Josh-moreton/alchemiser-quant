"""Market data mapping utilities for strategy adaptation.

Provides conversion functions between typed domain models and DataFrame formats
for strategies that still need pandas ergonomics while maintaining domain purity.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd

from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel
from the_alchemiser.domain.shared_kernel.value_objects.symbol import Symbol


def bars_to_dataframe(bars: list[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel domain objects to pandas DataFrame.

    Args:
        bars: List of BarModel domain objects

    Returns:
        DataFrame with OHLCV data indexed by timestamp
    """
    if not bars:
        return pd.DataFrame()

    data = []
    for bar in bars:
        data.append(
            {
                "Open": float(bar.open),
                "High": float(bar.high),
                "Low": float(bar.low),
                "Close": float(bar.close),
                "Volume": float(bar.volume),
            }
        )

    df = pd.DataFrame(data, index=[bar.ts for bar in bars])
    df.index.name = "timestamp"
    return df


def quote_to_tuple(quote: QuoteModel | None) -> tuple[float | None, float | None]:
    """Convert QuoteModel to tuple format for backward compatibility.

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
