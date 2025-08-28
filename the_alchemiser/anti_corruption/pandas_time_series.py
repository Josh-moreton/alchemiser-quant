"""Business Unit: utilities; Status: current.

Utilities to convert domain time-series models to pandas structures for indicators.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from the_alchemiser.strategy.infrastructure.models.bar import BarModel


def bars_to_dataframe(bars: Iterable[BarModel]) -> pd.DataFrame:
    """Convert list of BarModel to a pandas DataFrame with OHLCV and Date index."""
    rows = []
    idx = []
    for b in bars:
        rows.append(
            {
                "Open": float(b.open),
                "High": float(b.high),
                "Low": float(b.low),
                "Close": float(b.close),
                "Volume": float(b.volume),
            }
        )
        idx.append(b.ts)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(idx)
    df.index.name = "Date"
    return df
