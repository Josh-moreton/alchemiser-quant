from datetime import datetime

from the_alchemiser.backtest.events import MarketEvent
from the_alchemiser.data.replayer import MarketDataReplayer


def test_data_replayer_ordering() -> None:
    events = [
        MarketEvent(datetime(2024, 1, 1, 10, 0), "B", 101),
        MarketEvent(datetime(2024, 1, 1, 9, 59), "A", 100),
        MarketEvent(datetime(2024, 1, 1, 10, 0), "A", 102),
    ]
    replayer = MarketDataReplayer(events)
    ordered = [(e.timestamp, e.symbol) for e in replayer]
    assert ordered == sorted(ordered)
