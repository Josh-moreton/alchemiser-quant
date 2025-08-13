"""Trading calendar helpers."""

from collections.abc import Iterator
from datetime import datetime, timedelta


def iter_trading_days(
    start: datetime, end: datetime
) -> Iterator[datetime]:  # pragma: no cover - stub
    """Yield trading days between *start* and *end* inclusive."""
    day = start
    while day <= end:
        if day.weekday() < 5:  # Monday-Friday
            yield day
        day += timedelta(days=1)
