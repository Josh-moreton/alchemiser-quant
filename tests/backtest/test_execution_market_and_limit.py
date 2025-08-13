from datetime import datetime

from the_alchemiser.accounting.ledger import Ledger
from the_alchemiser.backtest.events import MarketEvent
from the_alchemiser.brokers.simulated_broker import SimulatedBroker
from the_alchemiser.execution.engine import ExecutionEngine
from the_alchemiser.execution.models import Order


def test_execution_market_and_limit() -> None:
    engine = ExecutionEngine()
    ledger = Ledger()
    broker = SimulatedBroker(engine, ledger)

    mkt = Order(id="1", symbol="AAPL", qty=10, side="buy", type="market")
    broker.submit_order(mkt)
    broker.on_market_event(MarketEvent(datetime(2024, 1, 1, 10, 0), "AAPL", 100))
    assert ledger.positions["AAPL"].lots[0].qty == 10

    limit = Order(id="2", symbol="AAPL", qty=10, side="sell", type="limit", limit_price=105)
    broker.submit_order(limit)
    broker.on_market_event(MarketEvent(datetime(2024, 1, 1, 10, 1), "AAPL", 104, size=5))
    assert limit.filled_qty == 0
    broker.on_market_event(MarketEvent(datetime(2024, 1, 1, 10, 2), "AAPL", 106, size=5))
    assert limit.filled_qty == 5
    broker.on_market_event(MarketEvent(datetime(2024, 1, 1, 10, 3), "AAPL", 106, size=5))
    assert "2" not in broker.orders
    assert ledger.realised_pnl == 60
